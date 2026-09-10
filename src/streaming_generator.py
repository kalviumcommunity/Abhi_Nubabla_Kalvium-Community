"""
Streaming Answer Generation with Citations for RAG Pipeline.

Implements server-sent events (SSE) streaming for progressive answer display
with embedded citation markers and metadata.

Features:
- Streams answer tokens progressively
- Embeds citation markers [1], [2], etc. in the answer
- Tracks citation positions for interactive source viewing
- Handles stream interruptions and errors gracefully
"""

import os
import re
import json
import time
from typing import Optional, List, Dict, Any, Iterator, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from dotenv import load_dotenv

from src.similarity_search import VectorStoreRetriever, RetrievedChunk
from prompt.templates import STAFF_ASSISTANT_SYSTEM_PROMPT, render_rag_request


# ============================================================================
# Streaming Data Models
# ============================================================================

@dataclass
class StreamEvent:
    """A single streaming event to be sent to the client."""
    
    event_type: str  # "start", "token", "citation", "sources", "complete", "error"
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_sse(self) -> str:
        """Convert to Server-Sent Event format."""
        event_json = json.dumps({
            "type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp
        })
        return f"data: {event_json}\n\n"


@dataclass
class CitationMarker:
    """Tracks where a citation marker appears in the answer."""
    
    marker_number: int  # e.g., 1 for [1]
    position: int  # Character position in answer
    source_rank: int  # Rank of the source in retrieved chunks
    chunk_id: str
    document_name: str
    section: str


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
    ):
        """
        Initialize the streaming generator.
        
        Args:
            retriever: VectorStoreRetriever instance for document retrieval
            min_similarity_threshold: Minimum similarity score for retrieved chunks
            min_relevant_chunks: Minimum number of relevant chunks required
        """
        self.retriever = retriever or VectorStoreRetriever()
        self.min_similarity_threshold = min_similarity_threshold
        self.min_relevant_chunks = min_relevant_chunks
        
    def stream_grounded_answer(
        self,
        query: str,
        k: int = 3,
        score_threshold: float = 0.0,
    ) -> Iterator[StreamEvent]:
        """
        Stream a grounded answer with progressive tokens and citations.
        
        Yields StreamEvent objects that should be sent to the client via SSE.
        
        Args:
            query: User question
            k: Number of chunks to retrieve
            score_threshold: Minimum similarity score
            
        Yields:
            StreamEvent objects for each streaming update
        """
        load_dotenv()
        start_time = time.time()
        
        # Event 1: Start event
        yield StreamEvent(
            event_type="start",
            data={"message": "Processing query...", "query": query}
        )
        
        try:
            # Retrieve relevant chunks
            raw_chunks = self.retriever.retrieve_top_k(
                query=query,
                k=k,
                score_threshold=score_threshold
            )
            
            relevant_chunks = [c for c in raw_chunks if c.score >= self.min_similarity_threshold]
            
            # Check if we have enough relevant chunks
            if len(relevant_chunks) < self.min_relevant_chunks:
                yield StreamEvent(
                    event_type="error",
                    data={
                        "error": "Insufficient context",
                        "message": f"Only {len(relevant_chunks)} relevant chunks found. "
                                  f"Minimum {self.min_relevant_chunks} required."
                    }
                )
                return
            
            # Assemble context from chunks
            context_block, sources = self._assemble_context(relevant_chunks)
            
            # Event 2: Sources event - send metadata about retrieved sources
            yield StreamEvent(
                event_type="sources",
                data={
                    "sources": sources,
                    "retrieved_count": len(relevant_chunks),
                    "context_preview": context_block[:200]  # First 200 chars of context
                }
            )
            
            # Prepare prompt for LLM
            user_prompt = render_rag_request(context=context_block, question=query)
            system_prompt = STAFF_ASSISTANT_SYSTEM_PROMPT
            
            # Event 3: Stream answer tokens with citation handling
            answer_tokens = []
            citation_markers: List[CitationMarker] = []
            
            for token, citation_info in self._stream_llm_answer(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                sources=sources
            ):
                answer_tokens.append(token)
                
                # If this token includes a citation marker, track it
                if citation_info:
                    citation_markers.append(citation_info)
                    yield StreamEvent(
                        event_type="citation",
                        data={
                            "marker": citation_info["marker"],
                            "position": len("".join(answer_tokens)),
                            "source": citation_info["source"]
                        }
                    )
                else:
                    # Regular answer token
                    yield StreamEvent(
                        event_type="token",
                        data={"token": token}
                    )
            
            # Event 4: Completion event
            complete_answer = "".join(answer_tokens)
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            
            yield StreamEvent(
                event_type="complete",
                data={
                    "answer": complete_answer,
                    "citations": [
                        {
                            "marker": cm.marker_number,
                            "source": {
                                "document": cm.document_name,
                                "section": cm.section,
                                "chunk_id": cm.chunk_id
                            }
                        }
                        for cm in citation_markers
                    ],
                    "latency_ms": elapsed_ms,
                    "retrieval_count": len(relevant_chunks)
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
    
    def _stream_llm_answer(
        self,
        user_prompt: str,
        system_prompt: str,
        sources: List[Dict[str, Any]]
    ) -> Iterator[Tuple[str, Optional[Dict[str, Any]]]]:
        """
        Stream answer tokens from LLM with citation markers.
        
        Yields tuples of (token, citation_info) where citation_info is not None
        if the token represents a citation marker.
        
        Args:
            user_prompt: The user question with context
            system_prompt: System instruction for the LLM
            sources: List of retrieved sources
            
        Yields:
            (token, citation_info) tuples
        """
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("EMBEDDING_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("EMBEDDING_BASE_URL")
        chat_model = os.getenv("OPENAI_MODEL") or "gpt-4-turbo"
        
        if not api_key or api_key in ["your_api_key_here", "your_grok_api_key_here"]:
            yield "[Local Fallback: No API configured. Please add OPENAI_API_KEY.]", None
            return
        
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            with client.chat.completions.create(
                model=chat_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=300,
                temperature=0.1,
                stream=True,  # Enable streaming
            ) as stream:
                token_count = 0
                citation_number = 1
                
                for event in stream:
                    if event.choices[0].delta.content:
                        token = event.choices[0].delta.content
                        
                        # Check if token contains citation markers or should trigger one
                        # We'll inject citations when specific keywords appear
                        citation_info = self._check_for_citation(
                            token,
                            token_count,
                            citation_number,
                            sources
                        )
                        
                        if citation_info:
                            citation_number += 1
                            yield token, citation_info
                        else:
                            yield token, None
                        
                        token_count += 1
                        
        except Exception as e:
            yield f"[Error: {str(e)}]", None
    
    def _check_for_citation(
        self,
        token: str,
        token_count: int,
        citation_number: int,
        sources: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a token should trigger a citation insertion.
        
        A simple heuristic: insert citations after key sentences or facts.
        
        Args:
            token: The current token
            token_count: How many tokens have been generated
            citation_number: Current citation marker number
            sources: List of available sources
            
        Returns:
            Citation info dict if a citation should be inserted, None otherwise
        """
        # Insert citations periodically or after sentences
        # For now, use a simple heuristic: every ~30 tokens or after periods
        should_cite = False
        
        if token.strip().endswith(".") or token.strip().endswith(".\n"):
            should_cite = token_count > 0 and (token_count % 30 == 0)
        
        if should_cite and citation_number <= len(sources):
            source = sources[min(citation_number - 1, len(sources) - 1)]
            return {
                "marker": f"[{citation_number}]",
                "source": {
                    "document": source.get("source_document", "Unknown"),
                    "section": source.get("section", ""),
                    "chunk_id": source.get("chunk_id", ""),
                    "rank": source.get("rank", citation_number)
                }
            }
        
        return None
    
    def _assemble_context(
        self,
        chunks: List[RetrievedChunk],
        max_context_tokens: int = 1500
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Assemble context from retrieved chunks.
        
        Args:
            chunks: Retrieved chunks
            max_context_tokens: Maximum context tokens
            
        Returns:
            (context_block, sources_list) tuple
        """
        snippets = []
        sources = []
        total_tokens = 0
        
        for chunk in chunks:
            tok_count = len(chunk.source_text.split())
            
            if total_tokens + tok_count > max_context_tokens:
                break
            
            snippet = f"[{chunk.chunk_id}] {chunk.source_text}"
            snippets.append(snippet)
            
            metadata = chunk.metadata or {}
            doc_name = metadata.get("source_document", "Unknown")
            sec = metadata.get("section", "General")
            
            total_tokens += tok_count
            
            sources.append({
                "rank": chunk.rank,
                "chunk_id": chunk.chunk_id,
                "source_document": doc_name,
                "section": sec,
                "page": metadata.get("page"),
                "similarity_score": chunk.score,
                "token_count": tok_count,
            })
        
        return "\n".join(snippets), sources
