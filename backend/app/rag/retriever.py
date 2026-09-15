"""
Contract RAG Retrieval & Reranking Engine.
"""

from typing import List, Dict, Any, Optional
from openai import OpenAI

from app.config import AppConfig, setup_logger
from app.vector_store.pinecone_store import vector_store

logger = setup_logger("contract_retriever")

class ContractRetriever:
    """
    Executes hybrid retrieval over corporate contracts.
    Combines vector search, metadata filtering, and relevance reranking.
    """

    def __init__(self):
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        client: OpenAI,
        k: int = 4,
        score_threshold: float = 0.0,
        metadata_filter: Optional[Dict[str, Any]] = None,
        contract_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top-k contract chunks relevant to the user query.
        """
        filter_dict = metadata_filter or {}
        if contract_id:
            filter_dict["contract_id"] = contract_id

        logger.info(f"Executing retrieval for query: '{query}' (top_k={k}, filter={filter_dict})")
        results = self.vector_store.search_similar_chunks(
            query=query,
            client=client,
            k=k,
            score_threshold=score_threshold,
            metadata_filter=filter_dict if filter_dict else None
        )

        # Optional Reranking Step (Keyword & Exact Title Boost)
        results = self._rerank_results(query, results)
        return results

    def _rerank_results(self, query: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Reranks vector search results based on query term frequency and section heading alignment."""
        if not chunks:
            return chunks

        query_terms = [t.lower() for t in query.split() if len(t) > 2]
        if not query_terms:
            return chunks

        reranked = []
        for chunk in chunks:
            text_lower = chunk["text"].lower()
            section_lower = (chunk.get("metadata", {}).get("section_title") or "").lower()
            
            # Boost score based on keyword hits in body and section title
            boost = 0.0
            for term in query_terms:
                if term in text_lower:
                    boost += 0.05
                if term in section_lower:
                    boost += 0.10

            final_score = min(1.0, chunk["similarity_score"] + boost)
            item = dict(chunk)
            item["similarity_score"] = round(final_score, 4)
            reranked.append(item)

        reranked.sort(key=lambda x: x["similarity_score"], reverse=True)
        return reranked

contract_retriever = ContractRetriever()
