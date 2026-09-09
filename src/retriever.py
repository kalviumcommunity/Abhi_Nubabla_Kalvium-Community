"""
Public Retrieval Interface for Staff RAG Assistant.
Provides high-level retrieve_top_k and retrieve_filtered functions for grounding downstream LLM generation.
"""

from typing import List, Optional
from src.similarity_search import (
    VectorStoreRetriever,
    DenseSemanticEmbedder,
    RetrievedChunk,
    cosine_similarity,
)
from src.filtered_retrieval import (
    FilteredRetriever,
    FilteredSearchResultChunk,
    MetadataFilter,
)


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


def retrieve_filtered(
    query: str,
    filter_spec: Optional[MetadataFilter] = None,
    k: int = 3,
    vector_store_path: str = "data/embedded_chunks.json",
    alpha: float = 0.0,
    exact_terms: Optional[List[str]] = None,
) -> List[FilteredSearchResultChunk]:
    """
    Retrieves filtered chunks matching query and metadata constraints.

    Args:
        query: The user prompt or question.
        filter_spec: Optional MetadataFilter specification.
        k: Number of top chunks to return.
        vector_store_path: Path to vector store JSON file.
        alpha: Hybrid scoring keyword balance weight.
        exact_terms: Optional exact keywords for bonus scoring.

    Returns:
        List of FilteredSearchResultChunk objects.
    """
    retriever = FilteredRetriever(vector_store_path=vector_store_path)
    return retriever.retrieve(
        query=query,
        filter_spec=filter_spec,
        k=k,
        alpha=alpha,
        exact_terms=exact_terms,
    )
