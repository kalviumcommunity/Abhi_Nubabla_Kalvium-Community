"""
Contract Q&A Generation Engine.

Handles grounded answer generation using Groq LLM (openai/gpt-oss-20b) and vector embedding
retrieval via OpenRouter (nvidia/llama-nemotron-embed-vl-1b-v2:free).
"""

import json
from typing import List, Dict, Any, Generator, Tuple, Optional
from openai import OpenAI

from app.config import AppConfig, setup_logger
from app.ingestion.contract_processor import estimate_tokens
from app.rag.prompt_templates import render_contract_rag_prompt
from app.rag.retriever import contract_retriever

logger = setup_logger("contract_generator")


def get_groq_client() -> OpenAI:
    """Instantiates OpenAI-compatible client for Groq LLM inference."""
    return OpenAI(
        api_key=AppConfig.GROQ_API_KEY or "dummy-groq-key",
        base_url=AppConfig.GROQ_BASE_URL
    )


def get_openrouter_embedding_client() -> OpenAI:
    """Instantiates OpenAI-compatible client for OpenRouter text vector embeddings."""
    return OpenAI(
        api_key=AppConfig.OPENROUTER_API_KEY or "dummy-openrouter-key",
        base_url=AppConfig.OPENROUTER_BASE_URL
    )


OFF_TOPIC_PATTERNS = [
    "capital of", "recipe", "how to cook", "weather in", "tell me a joke",
    "who is the president", "who won", "movie", "song lyrics", "football",
    "cricket", "basketball", "write code for", "solve math", "translate this"
]

CONTRACT_KEYWORDS = [
    "contract", "agreement", "supplier", "vendor", "payment", "term",
    "expire", "renewal", "sow", "nda", "sla", "liability", "termination",
    "clause", "discount", "audit", "pricing", "effective", "date", "commitment",
    "value", "legal", "fee", "notice", "service", "party", "parties", "compliance",
    "warrant", "governing", "jurisdiction", "indemnification", "breach"
]

GUARDRAIL_MESSAGE = (
    "I am your Enterprise Contract Intelligence Assistant. I am designed specifically "
    "to answer questions about your corporate contracts, procurement terms, vendor agreements, "
    "and compliance portfolio. I cannot assist with general knowledge or off-topic questions. "
    "Please ask a question related to your contracts or suppliers!"
)


def check_guardrails(question: str, retrieved_chunks: list) -> Optional[str]:
    """Evaluates question against strict corporate contract guardrails."""
    q_lower = question.lower().strip()
    
    # 1. Explicit off-topic pattern match
    if any(pattern in q_lower for pattern in OFF_TOPIC_PATTERNS):
        return GUARDRAIL_MESSAGE

    # 2. If no chunks matched and query contains zero contract/procurement domain keywords
    has_contract_kw = any(kw in q_lower for kw in CONTRACT_KEYWORDS)
    if not retrieved_chunks and not has_contract_kw:
        return GUARDRAIL_MESSAGE

    return None


class ContractQAGenerator:
    """
    Orchestrates Retrieval-Augmented Generation (RAG) over stored corporate contracts.
    Uses OpenRouter for embeddings & vector retrieval, and Groq for fast LLM answer generation.
    """

    def __init__(self):
        self.retriever = contract_retriever

    def trim_history(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Trims old messages from history to respect AppConfig.MAX_HISTORY_TOKENS while preserving system prompt."""
        if not messages:
            return messages

        system_msg = messages[0] if messages[0].get("role") == "system" else None
        conversation = messages[1:] if system_msg else list(messages)

        max_tokens = AppConfig.MAX_HISTORY_TOKENS
        current_tokens = sum(estimate_tokens(m.get("content", "")) for m in messages)

        if current_tokens <= max_tokens * AppConfig.HISTORY_TRIM_THRESHOLD:
            return messages

        while len(conversation) > 2:
            conversation.pop(0)
            t_count = sum(estimate_tokens(m.get("content", "")) for m in conversation)
            if system_msg:
                t_count += estimate_tokens(system_msg.get("content", ""))
            if t_count <= max_tokens * AppConfig.HISTORY_TRIM_THRESHOLD:
                break

        trimmed = [system_msg] + conversation if system_msg else conversation
        return trimmed

    def generate_answer(
        self,
        question: str,
        history: Optional[List[Dict[str, str]]] = None,
        k: int = 4,
        contract_id: Optional[str] = None,
        score_threshold: float = 0.0
    ) -> Dict[str, Any]:
        """
        Executes end-to-end contract RAG pipeline:
        1. Embeds query via OpenRouter embedding client & retrieves matching chunks from Pinecone.
        2. Evaluates guardrails for off-topic questions.
        3. Formats strict context system prompt.
        4. Calls Groq LLM to synthesize answer with citations.
        """
        groq_client = get_groq_client()
        embedding_client = get_openrouter_embedding_client()

        # 1. Retrieve relevant contract chunks using OpenRouter embedding client
        retrieved_chunks = self.retriever.retrieve(
            query=question,
            client=embedding_client,
            k=k,
            score_threshold=score_threshold,
            contract_id=contract_id
        )

        # 2. Check Guardrails
        guardrail_response = check_guardrails(question, retrieved_chunks)
        if guardrail_response:
            return {
                "answer": guardrail_response,
                "sources": [],
                "chunks_retrieved": 0
            }

        # 3. Render prompt with retrieved context
        system_prompt, formatted_context = render_contract_rag_prompt(question, retrieved_chunks)

        # 3. Assemble chat payload
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for turn in history:
                if turn.get("role") in ("user", "assistant"):
                    messages.append({"role": turn["role"], "content": turn["content"]})
        
        messages.append({"role": "user", "content": question})
        messages = self.trim_history(messages)

        # 4. Fallback response if Groq API Key is unconfigured
        if not AppConfig.GROQ_API_KEY or AppConfig.GROQ_API_KEY.startswith("your_"):
            logger.warning("No valid Groq API Key configured in .env. Returning grounded answer fallback.")
            if retrieved_chunks:
                top_chunk = retrieved_chunks[0]
                meta = top_chunk.get("metadata", {})
                answer = (
                    f"Based on the stored contract '{meta.get('contract_title', 'Contract')}' "
                    f"({meta.get('section_title', 'General Clause')}):\n\n"
                    f"{top_chunk['text'][:300]}...\n\n"
                    f"[Citation Ref: {top_chunk['chunk_id']}]"
                )
            else:
                answer = "The provided contract documents do not contain sufficient information to answer this question."

            citations = [
                {
                    "chunk_id": c["chunk_id"],
                    "contract_title": c.get("metadata", {}).get("contract_title", "Contract"),
                    "section_title": c.get("metadata", {}).get("section_title", "Section"),
                    "score": c.get("similarity_score", 0.0),
                    "snippet": c["text"][:200]
                }
                for c in retrieved_chunks
            ]
            return {
                "answer": answer,
                "sources": citations,
                "chunks_retrieved": len(retrieved_chunks)
            }

        try:
            # Send completion request exclusively to Groq LLM API
            response = groq_client.chat.completions.create(
                model=AppConfig.GROQ_MODEL,
                messages=messages,
                max_tokens=AppConfig.MAX_ANSWER_TOKENS,
                temperature=AppConfig.ANSWER_TEMPERATURE
            )
            answer = response.choices[0].message.content

            citations = [
                {
                    "chunk_id": c["chunk_id"],
                    "contract_title": c.get("metadata", {}).get("contract_title", "Contract"),
                    "section_title": c.get("metadata", {}).get("section_title", "Section"),
                    "score": c.get("similarity_score", 0.0),
                    "snippet": c["text"][:200]
                }
                for c in retrieved_chunks
            ]

            return {
                "answer": answer,
                "sources": citations,
                "chunks_retrieved": len(retrieved_chunks)
            }
        except Exception as e:
            logger.error(f"Groq LLM Answer Generation Error: {e}")
            return {
                "answer": f"An error occurred while generating answer from contract context: {str(e)}",
                "sources": [],
                "chunks_retrieved": len(retrieved_chunks)
            }

    def generate_stream(
        self,
        question: str,
        k: int = 4,
        contract_id: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        Streams contract Q&A response token-by-token from Groq LLM using Server-Sent Events (SSE).
        """
        groq_client = get_groq_client()
        embedding_client = get_openrouter_embedding_client()

        retrieved_chunks = self.retriever.retrieve(
            query=question,
            client=embedding_client,
            k=k,
            contract_id=contract_id
        )

        guardrail_response = check_guardrails(question, retrieved_chunks)
        if guardrail_response:
            evt = json.dumps({"event": "token", "content": guardrail_response})
            yield f"data: {evt}\n\n"
            yield f"data: {json.dumps({'event': 'done'})}\n\n"
            return

        system_prompt, _ = render_contract_rag_prompt(question, retrieved_chunks)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]

        sources = [
            {
                "chunk_id": c["chunk_id"],
                "contract_title": c.get("metadata", {}).get("contract_title", "Contract"),
                "section_title": c.get("metadata", {}).get("section_title", "Section"),
                "score": c.get("similarity_score", 0.0)
            }
            for c in retrieved_chunks
        ]
        meta_event = json.dumps({"event": "metadata", "sources": sources})
        yield f"data: {meta_event}\n\n"

        if not AppConfig.GROQ_API_KEY or AppConfig.GROQ_API_KEY.startswith("your_"):
            full_ans = self.generate_answer(question, k=k, contract_id=contract_id)["answer"]
            words = full_ans.split()
            for word in words:
                evt = json.dumps({"event": "token", "content": word + " "})
                yield f"data: {evt}\n\n"
            yield f"data: {json.dumps({'event': 'done'})}\n\n"
            return

        try:
            stream = groq_client.chat.completions.create(
                model=AppConfig.GROQ_MODEL,
                messages=messages,
                max_tokens=AppConfig.MAX_ANSWER_TOKENS,
                temperature=AppConfig.ANSWER_TEMPERATURE,
                stream=True
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    evt = json.dumps({"event": "token", "content": token})
                    yield f"data: {evt}\n\n"
            yield f"data: {json.dumps({'event': 'done'})}\n\n"
        except Exception as e:
            err_evt = json.dumps({"event": "error", "error": str(e)})
            yield f"data: {err_evt}\n\n"

contract_qa_generator = ContractQAGenerator()
