"""
Streaming Answer Generation with Citations for RAG Pipeline.

Implements Server-Sent Events (SSE) streaming for progressive answer display
with embedded citation markers and metadata attribution.

Features:
- Progressive token-by-token streaming
- Full source chunk content included in sources metadata for inspection
- Clear citation markers ([1], [2]) linked to retrieved document chunks
- Dual engine: live OpenAI-compatible LLM streaming with deterministic local fallback
- Robust error handling for network interruptions, missing context, and timeouts
"""

from __future__ import annotations

import os
import re
import sys
import json
import time
from typing import Optional, List, Dict, Any, Iterator, Tuple, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from dotenv import load_dotenv

# Reconfigure stdout/stderr to UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass

from src.similarity_search import VectorStoreRetriever, RetrievedChunk
from prompt.templates import STAFF_ASSISTANT_SYSTEM_PROMPT, render_rag_request

# Standard refusal for missing context
STANDARD_FALLBACK_ANSWER = (
    "I don't have access to this information in the verified company guidelines. "
    "Please contact HR at hr@company.com or submit a ticket via the IT Helpdesk portal."
)

CITATION_SYSTEM_PROMPT = STAFF_ASSISTANT_SYSTEM_PROMPT + """

CITATION INSTRUCTIONS:
- You MUST back up every claim or factual statement with inline bracket citations referencing the source chunk index, e.g. [1] or [2].
- Place citation brackets immediately following the claim or sentence they support.
- ONLY cite source numbers provided in the context (e.g. [1], [2]). NEVER fabricate citation numbers.
- If the context lacks sufficient information, do NOT invent claims or citations. Follow the fallback instruction.
"""


# ============================================================================
# Streaming Data Models
# ============================================================================

@dataclass
class StreamEvent:
    """A single streaming event to be sent to the client."""

    event_type: str  # "start", "sources", "token", "citation", "complete", "error"
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_sse(self) -> str:
        """Convert to Server-Sent Event (SSE) format."""
        event_json = json.dumps({
            "type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp
        }, ensure_ascii=False)
        return f"data: {event_json}\n\n"


@dataclass
class CitationMarker:
    """Tracks where a citation marker appears in the answer and its linked source."""

    marker_number: int  # e.g., 1 for [1]
    marker: str  # e.g., "[1]"
    position: int  # Character offset in answer
    source_rank: int
    chunk_id: str
    document_name: str
    section: str
    similarity_score: float
    text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# Streaming Generator
# ============================================================================

class StreamingAnswerGenerator:
    """Generates grounded answers with streaming and citations."""

    def __init__(
        self,
        retriever: Optional[VectorStoreRetriever] = None,
        min_similarity_threshold: float = 0.0,
        min_relevant_chunks: int = 1,
        stream_delay: float = 0.015,
    ):
        """
        Initialize the streaming generator.

        Args:
            retriever: VectorStoreRetriever instance for document retrieval
            min_similarity_threshold: Minimum similarity score for retrieved chunks
            min_relevant_chunks: Minimum number of relevant chunks required
            stream_delay: Delay between tokens in local synthesis mode (seconds)
        """
        self.retriever = retriever or VectorStoreRetriever()
        self.min_similarity_threshold = min_similarity_threshold
        self.min_relevant_chunks = min_relevant_chunks
        self.stream_delay = stream_delay

    def stream_grounded_answer(
        self,
        query: str,
        k: int = 3,
        score_threshold: float = 0.0,
    ) -> Iterator[StreamEvent]:
        """
        Stream a grounded answer with progressive tokens and citations.

        Yields StreamEvent objects to be sent via Server-Sent Events (SSE).

        Args:
            query: User question
            k: Number of chunks to retrieve
            score_threshold: Minimum similarity score threshold

        Yields:
            StreamEvent objects for each streaming update
        """
        load_dotenv()
        start_time = time.time()

        # Event 1: Start event
        yield StreamEvent(
            event_type="start",
            data={
                "message": "Processing query and retrieving relevant documents...",
                "query": query
            }
        )

        try:
            effective_threshold = max(score_threshold, self.min_similarity_threshold)

            # Retrieve relevant chunks
            raw_chunks = self.retriever.retrieve_top_k(
                query=query,
                k=k,
                score_threshold=effective_threshold
            )

            relevant_chunks = [c for c in raw_chunks if c.score >= effective_threshold]

            # Check if we have sufficient relevant context
            if len(relevant_chunks) < self.min_relevant_chunks:
                # Fallback: No relevant documents found
                yield StreamEvent(
                    event_type="sources",
                    data={
                        "sources": [],
                        "retrieved_count": 0,
                        "context_preview": "No relevant documents found."
                    }
                )

                # Stream the fallback refusal token-by-token
                fallback_tokens = self._tokenize_text(STANDARD_FALLBACK_ANSWER)
                answer_tokens: List[str] = []

                for tok in fallback_tokens:
                    answer_tokens.append(tok)
                    yield StreamEvent(
                        event_type="token",
                        data={"token": tok}
                    )
                    if self.stream_delay > 0:
                        time.sleep(self.stream_delay)

                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                yield StreamEvent(
                    event_type="complete",
                    data={
                        "answer": "".join(answer_tokens),
                        "citations": [],
                        "latency_ms": elapsed_ms,
                        "retrieval_count": 0,
                        "is_fallback": True
                    }
                )
                return

            # Assemble context and extract rich source metadata
            context_block, sources, citation_map = self._assemble_context(relevant_chunks)

            # Event 2: Sources event - sends metadata and chunk texts
            yield StreamEvent(
                event_type="sources",
                data={
                    "sources": sources,
                    "retrieved_count": len(relevant_chunks),
                    "context_preview": context_block[:250] + "..." if len(context_block) > 250 else context_block
                }
            )

            # Event 3 & 4: Stream answer tokens and citation markers
            answer_tokens: List[str] = []
            citations_emitted: Set[str] = set()
            citation_records: List[Dict[str, Any]] = []

            for token in self._stream_answer_tokens(
                query=query,
                context_block=context_block,
                relevant_chunks=relevant_chunks,
                citation_map=citation_map
            ):
                answer_tokens.append(token)
                yield StreamEvent(
                    event_type="token",
                    data={"token": token}
                )

                # Check if recently accumulated text has new citation markers
                current_text = "".join(answer_tokens)
                found_tags = re.findall(r'\[(\d+)\]', current_text)

                for tag_num in found_tags:
                    tag = f"[{tag_num}]"
                    if tag not in citations_emitted and tag in citation_map:
                        citations_emitted.add(tag)
                        source_info = citation_map[tag]
                        record = {
                            "marker": tag,
                            "marker_number": int(tag_num),
                            "position": len(current_text),
                            "source": source_info
                        }
                        citation_records.append(record)
                        yield StreamEvent(
                            event_type="citation",
                            data=record
                        )

            # Event 5: Completion event
            complete_answer = "".join(answer_tokens)
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            yield StreamEvent(
                event_type="complete",
                data={
                    "answer": complete_answer,
                    "citations": citation_records,
                    "latency_ms": elapsed_ms,
                    "retrieval_count": len(relevant_chunks),
                    "is_fallback": False
                }
            )

        except Exception as e:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            yield StreamEvent(
                event_type="error",
                data={
                    "error": type(e).__name__,
                    "message": str(e),
                    "latency_ms": elapsed_ms
                }
            )

    def _assemble_context(
        self,
        chunks: List[RetrievedChunk],
        max_context_tokens: int = 1500
    ) -> Tuple[str, List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        """
        Assemble prompt context and build source metadata mapping with chunk texts.

        Returns:
            Tuple of (context_block, sources_list, citation_map)
        """
        snippets = []
        sources = []
        citation_map = {}
        total_tokens = 0

        for idx, chunk in enumerate(chunks, start=1):
            tag = f"[{idx}]"
            metadata = chunk.metadata or {}
            doc_name = metadata.get("source_document") or metadata.get("source_path") or "unknown_document"
            doc_name = os.path.basename(doc_name)
            sec = metadata.get("section", "General")
            page = metadata.get("page")
            tok_count = metadata.get("token_count") or len(chunk.source_text.split())

            if total_tokens + tok_count > max_context_tokens and snippets:
                break

            header = f"{tag} Source Document: {doc_name} | Section: {sec} | Score: {round(chunk.score, 4)}"
            snippet_text = f"{header}\n{chunk.source_text.strip()}\n"
            snippets.append(snippet_text)
            total_tokens += tok_count

            full_text = chunk.source_text.strip()
            preview = full_text[:220] + "..." if len(full_text) > 220 else full_text

            source_item = {
                "rank": idx,
                "tag": tag,
                "chunk_id": chunk.chunk_id,
                "source_document": doc_name,
                "section": sec,
                "page": page,
                "similarity_score": round(chunk.score, 4),
                "token_count": tok_count,
                "text": full_text,
                "snippet": preview
            }

            sources.append(source_item)
            citation_map[tag] = source_item

        return "\n".join(snippets), sources, citation_map

    def _stream_answer_tokens(
        self,
        query: str,
        context_block: str,
        relevant_chunks: List[RetrievedChunk],
        citation_map: Dict[str, Dict[str, Any]]
    ) -> Iterator[str]:
        """
        Stream answer tokens progressively.
        Uses OpenAI API when configured, otherwise uses local grounded synthesis.
        """
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("EMBEDDING_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("EMBEDDING_BASE_URL")
        chat_model = os.getenv("OPENAI_MODEL") or "gpt-4-turbo"

        is_live_api = bool(api_key and api_key not in ["your_api_key_here", "your_grok_api_key_here"])

        if is_live_api:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key, base_url=base_url)
                user_prompt = render_rag_request(context=context_block, question=query)

                with client.chat.completions.create(
                    model=chat_model,
                    messages=[
                        {"role": "system", "content": CITATION_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=350,
                    temperature=0.1,
                    stream=True
                ) as stream:
                    for chunk in stream:
                        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
                return
            except Exception:
                # Fall through to local grounded synthesis if API call fails
                pass

        # Local Grounded Synthesis Engine: provides realistic progressive streaming
        for token in self._stream_local_synthesis(query, relevant_chunks, citation_map):
            yield token

    def _stream_local_synthesis(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        citation_map: Dict[str, Dict[str, Any]]
    ) -> Iterator[str]:
        """
        Generate grounded answer deterministically and stream token-by-token.
        """
        top_meta = citation_map.get("[1]")
        if not top_meta:
            yield STANDARD_FALLBACK_ANSWER
            return

        doc_name = top_meta["source_document"]
        sec = top_meta["section"]

        # Extract factual lines from source text
        raw_lines = [
            line.strip()
            for line in top_meta["text"].split("\n")
            if line.strip() and not line.strip().startswith("#") and not line.strip().startswith("[")
        ]
        key_fact = raw_lines[0] if raw_lines else "Employees must follow verified organizational guidelines."

        answer = (
            f"Based on verified company guidelines in {doc_name} ({sec}) [1]: "
            f"{key_fact} [1]"
        )

        # Include second citation if available
        if len(chunks) > 1 and "[2]" in citation_map:
            meta2 = citation_map["[2]"]
            lines2 = [
                l.strip()
                for l in meta2["text"].split("\n")
                if l.strip() and not l.strip().startswith("#") and not l.strip().startswith("[")
            ]
            if lines2:
                answer += f" Additionally, {meta2['source_document']} ({meta2['section']}) clarifies: {lines2[0]} [2]."

        # Tokenize and stream with small delay for progressive visualization
        tokens = self._tokenize_text(answer)
        for token in tokens:
            yield token
            if self.stream_delay > 0:
                time.sleep(self.stream_delay)

    def _tokenize_text(self, text: str) -> List[str]:
        """
        Break text into natural token chunks (words and spaces) for streaming.
        """
        parts = re.split(r'(\s+)', text)
        return [p for p in parts if p]
