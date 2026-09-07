"""
Public Retrieval Interface for Staff RAG Assistant.
Provides high-level retrieve_top_k and retrieve_filtered functions for grounding downstream LLM generation.
"""

from typing import Any, Dict, List, Optional
from src.similarity_search import (
    VectorStoreRetriever,
    RetrievedChunk,
    DenseSemanticEmbedder,
    cosine_similarity,
)
from src.filtered_retrieval import (
    FilteredRetriever,
    MetadataFilter,
    FilteredSearchResultChunk,
    HybridScorer,
)


def retrieve_top_k(
    query: str,
    k: int = 3,
    vector_store_path: str = "data/embedded_chunks.json",
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
    alpha: float = 0.0,
    exact_terms: Optional[List[str]] = None,
    vector_store_path: str = "data/embedded_chunks.json",
) -> List[FilteredSearchResultChunk]:
    """
    Retrieves top-k chunks with metadata pre-filtering and optional hybrid scoring.

    Args:
        query: User prompt.
        filter_spec: MetadataFilter instance specifying document, section, or file type constraints.
        k: Number of chunks to retrieve (default: 3).
        alpha: Hybrid weight in [0.0, 1.0] (0.0 = pure vector, 0.3 = hybrid).
        exact_terms: Specific tokens or phrases to boost in lexical ranking.
        vector_store_path: Path to vector store file.

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
