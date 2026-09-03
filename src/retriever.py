"""
Public Retrieval Interface for Staff RAG Assistant.
Provides high-level retrieve_top_k function for grounding downstream LLM generation.
"""

from typing import List, Optional
from src.similarity_search import VectorStoreRetriever, RetrievedChunk


def retrieve_top_k(
    query: str,
    k: int = 3,
    vector_store_path: str = "data/embedded_chunks.json"
) -> List[RetrievedChunk]:
    """
    Retrieves top-k most relevant document chunks for a given query text.

    Args:
        query: The user prompt or question.
        k: Number of most similar chunks to return (default: 3).
        vector_store_path: Path to pre-computed embedded chunks JSON.

    Returns:
        List of RetrievedChunk objects with similarity scores, source text, and metadata.
    """
    retriever = VectorStoreRetriever(vector_store_path=vector_store_path)
    return retriever.retrieve_top_k(query=query, k=k)
