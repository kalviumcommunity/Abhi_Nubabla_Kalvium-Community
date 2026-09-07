"""
Public Retrieval Interface for Staff RAG Assistant.
Provides high-level retrieve_top_k function for grounding downstream LLM generation.
Supports single-stage (direct top-k) and two-stage (retrieve + re-rank) retrieval.
"""

from typing import List, Optional, Dict, Any
from src.similarity_search import VectorStoreRetriever, RetrievedChunk
from src.reranker import (
    TwoStageRetrievalPipeline,
    SemanticRelevanceReranker,
    ChunkReranker,
    RerangingResult,
)


def retrieve_top_k(
    query: str,
    k: int = 3,
    score_threshold: float = 0.0,
    metadata_filter: Optional[Dict[str, Any]] = None,
    vector_store_path: str = "data/embedded_chunks.json"
) -> List[RetrievedChunk]:
    """
    Retrieves top-k most relevant document chunks for a given query text.
    Single-stage direct retrieval using vector similarity.

    Args:
        query: The user prompt or question.
        k: Number of most similar chunks to return (default: 3).
        score_threshold: Minimum similarity score threshold (default: 0.0).
        metadata_filter: Optional metadata filtering criteria (e.g. {"file_type": ".md"}).
        vector_store_path: Path to pre-computed embedded chunks JSON.

    Returns:
        List of RetrievedChunk objects with similarity scores, source text, and metadata.
    """
    retriever = VectorStoreRetriever(vector_store_path=vector_store_path)
    return retriever.retrieve_top_k(query=query, k=k)


def retrieve_with_reranking(
    query: str,
    k_final: int = 3,
    k_candidate: int = 10,
    vector_store_path: str = "data/embedded_chunks.json",
    reranker: Optional[ChunkReranker] = None,
) -> RerangingResult:
    """
    Two-stage retrieval pipeline with re-ranking:
    Stage 1: Retrieve larger candidate set (k_candidate chunks)
    Stage 2: Re-rank candidates and return top-k final results (k_final chunks)

    This improves relevance by allowing the re-ranker to see a broader candidate set
    and score them more carefully than the initial vector similarity pass.

    Args:
        query: The user prompt or question.
        k_final: Number of final results after re-ranking (default: 3).
        k_candidate: Number of initial candidates to retrieve and re-rank (default: 10).
        vector_store_path: Path to pre-computed embedded chunks JSON.
        reranker: Optional custom reranker. If None, uses SemanticRelevanceReranker.

    Returns:
        RerangingResult containing both initial and re-ranked results with scores.
    """
    # Stage 1: Retrieve initial candidates
    retriever = VectorStoreRetriever(vector_store_path=vector_store_path)
    initial_candidates_retrieved = retriever.retrieve_top_k(query=query, k=k_candidate)
    
    # Convert RetrievedChunk objects to dictionaries for reranker
    initial_candidates_dicts = []
    for chunk in initial_candidates_retrieved:
        chunk_dict = {
            "chunk_id": chunk.chunk_id,
            "source_text": chunk.source_text,
            "metadata": chunk.metadata,
            "vector_score": chunk.score,
        }
        initial_candidates_dicts.append(chunk_dict)
    
    # Stage 2: Re-rank candidates
    if reranker is None:
        reranker = SemanticRelevanceReranker()
    
    pipeline = TwoStageRetrievalPipeline(
        reranker=reranker,
        k_candidate=k_candidate,
        k_final=k_final,
    )
    
    result = pipeline.rerank_candidates(
        query=query,
        initial_candidates=initial_candidates_dicts,
    )
    
    return result

