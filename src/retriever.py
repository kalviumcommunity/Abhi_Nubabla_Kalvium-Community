"""
Public Retrieval Interface for Staff RAG Assistant.
Provides high-level retrieve_top_k function for grounding downstream LLM generation.
Supports single-stage (direct top-k) and two-stage (retrieve + re-rank) retrieval.
Includes end-to-end augmented prompt generation with context injection.
"""

from typing import List, Optional, Dict, Any
from src.similarity_search import VectorStoreRetriever, RetrievedChunk
from src.reranker import (
    TwoStageRetrievalPipeline,
    SemanticRelevanceReranker,
    ChunkReranker,
    RerangingResult,
)
from src.context_injector import AugmentedPromptBuilder, AugmentedPrompt


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


def build_augmented_prompt(
    user_question: str,
    k: int = 3,
    vector_store_path: str = "data/embedded_chunks.json",
    model_name: str = "gpt-3.5-turbo",
    context_budget_percent: float = 0.50,
    grounding_style: str = "professional",
) -> AugmentedPrompt:
    """
    End-to-end RAG pipeline: retrieve chunks and build augmented prompt with context injection.
    
    This is the primary function for integrating retrieval into LLM systems.
    It handles:
    1. Retrieving k most relevant chunks
    2. Injecting chunks with source markers [1], [2], etc.
    3. Enforcing token budget
    4. Adding grounding instructions
    5. Assembling final augmented prompt ready for LLM

    Args:
        user_question: The user's question or prompt.
        k: Number of chunks to retrieve (default: 3).
        vector_store_path: Path to pre-computed embedded chunks JSON.
        model_name: Target LLM model name (e.g., "gpt-3.5-turbo", "gpt-4").
        context_budget_percent: Percentage of model's tokens for context (default: 50%).
        grounding_style: Style of grounding instructions ("basic", "strict", "professional").

    Returns:
        AugmentedPrompt containing:
        - assembled_prompt: Ready-to-use prompt with injected context
        - injected_chunks: Chunks with source markers
        - token_count_*: Detailed token budget breakdown
        - token_budget_remaining: Tokens available for answer
    
    Example:
        >>> result = build_augmented_prompt(
        ...     user_question="How much PTO do employees get?",
        ...     k=3,
        ...     model_name="gpt-3.5-turbo",
        ... )
        >>> print(result.assembled_prompt)  # Ready for LLM API
        >>> print(result.token_budget_remaining)  # Space for answer
    """
    # Stage 1: Retrieve relevant chunks
    chunks = retrieve_top_k(query=user_question, k=k, vector_store_path=vector_store_path)
    
    # Stage 2: Build augmented prompt with context injection
    builder = AugmentedPromptBuilder(
        model_name=model_name,
        context_budget_percent=context_budget_percent,
        grounding_style=grounding_style,
    )
    
    augmented_prompt = builder.build_augmented_prompt(
        user_question=user_question,
        chunks=chunks,
        template_style="standard",
    )
    
    return augmented_prompt

