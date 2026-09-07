"""
Re-ranking Module for RAG Chunk Relevance Refinement.

Implements a two-stage retrieval pipeline:
1. Stage 1: Retrieve a larger candidate set (e.g., k_candidate=10)
2. Stage 2: Re-rank candidates using advanced scoring and return top-k (e.g., k_final=3)

Re-ranking strategies:
- LLM-based scoring: Use an LLM to score chunk relevance to the query
- Custom semantic scoring: Use multi-aspect relevance computation
- Cross-encoder style: Score query-chunk pairs for better fine-grained matching
"""

from __future__ import annotations

import json
import os
import re
import math
import hashlib
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod

from dotenv import load_dotenv

# Configure stdout/stderr to use UTF-8
import sys
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

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# ---------------------------------------------------------------------------
# Data Models for Re-ranking Results
# ---------------------------------------------------------------------------
@dataclass
class RerankedChunk:
    """Represents a re-ranked chunk with both vector and re-rank scores."""
    
    rank: int
    chunk_id: str
    source_text: str
    metadata: Dict[str, Any]
    
    # Original vector similarity score
    vector_score: float
    
    # Re-ranker score (higher is better)
    rerank_score: float
    
    # Scoring breakdown for transparency
    scoring_breakdown: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "chunk_id": self.chunk_id,
            "source_text": self.source_text,
            "metadata": self.metadata,
            "vector_score": round(self.vector_score, 6),
            "rerank_score": round(self.rerank_score, 6),
            "scoring_breakdown": {k: round(v, 6) for k, v in self.scoring_breakdown.items()},
        }


@dataclass
class RerangingResult:
    """Results from the two-stage retrieval and re-ranking process."""
    
    query: str
    k_candidate: int
    k_final: int
    
    # Stage 1: Initial candidates
    candidates_initial: List[RerankedChunk]
    
    # Stage 2: Final re-ranked results
    results_reranked: List[RerankedChunk]
    
    # Reranker used
    reranker_name: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "k_candidate": self.k_candidate,
            "k_final": self.k_final,
            "reranker_used": self.reranker_name,
            "candidates_initial": [c.to_dict() for c in self.candidates_initial],
            "results_reranked": [c.to_dict() for c in self.results_reranked],
        }


# ---------------------------------------------------------------------------
# Abstract Re-ranker Base Class
# ---------------------------------------------------------------------------
class ChunkReranker(ABC):
    """
    Abstract base class for chunk re-ranking strategies.
    Implementations should score a list of chunks relative to a query.
    """
    
    @abstractmethod
    def score_chunks(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
    ) -> Dict[str, Tuple[float, Dict[str, float]]]:
        """
        Score chunks for relevance to the query.
        
        Args:
            query: The user query/question
            chunks: List of chunk dicts with 'chunk_id', 'source_text', 'metadata'
        
        Returns:
            Dict mapping chunk_id -> (rerank_score, scoring_breakdown)
            where scoring_breakdown explains the score components
        """
        pass
    
    @abstractmethod
    def name(self) -> str:
        """Return the name of this reranker."""
        pass


# ---------------------------------------------------------------------------
# Reranker 1: Custom Semantic Relevance Scoring
# ---------------------------------------------------------------------------
class SemanticRelevanceReranker(ChunkReranker):
    """
    Custom multi-aspect relevance scoring combining:
    1. Query term overlap (TF-IDF inspired scoring)
    2. Semantic concept matching
    3. Text structure and information density
    """
    
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension
        self.query_terms_weight = 0.4
        self.semantic_concept_weight = 0.35
        self.info_density_weight = 0.25
    
    def name(self) -> str:
        return "SemanticRelevanceReranker"
    
    def _tokenize_and_normalize(self, text: str) -> List[str]:
        """Extract and normalize tokens from text."""
        text_lower = text.lower().strip()
        tokens = re.findall(r"\b\w+\b", text_lower)
        return tokens
    
    def _query_term_score(self, query: str, chunk_text: str) -> float:
        """
        Score based on query term overlap in chunk.
        Weighted by query term importance (rarer terms score higher).
        """
        query_tokens = self._tokenize_and_normalize(query)
        chunk_text_lower = chunk_text.lower()
        
        # Remove common stopwords
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "is", "are"}
        query_tokens = [t for t in query_tokens if t not in stopwords and len(t) > 2]
        
        if not query_tokens:
            return 0.5  # Neutral score if all terms are stopwords
        
        # Score based on number of query terms found in chunk
        matches = sum(1 for term in query_tokens if term in chunk_text_lower)
        match_ratio = matches / len(query_tokens)
        
        # Weight by term specificity (longer terms are more specific)
        avg_term_length = sum(len(t) for t in query_tokens) / len(query_tokens)
        specificity_weight = min(1.0, avg_term_length / 10.0)
        
        return match_ratio * specificity_weight
    
    def _semantic_concept_score(self, query: str, chunk_text: str) -> float:
        """
        Score based on semantic concept alignment.
        Identifies domain concepts in both query and chunk.
        """
        query_lower = query.lower()
        chunk_lower = chunk_text.lower()
        
        # Define domain-specific semantic concepts
        semantic_patterns = {
            "leave_vacation": (["pto", "vacation", "leave", "holiday", "sick day", "accrual", "rollover"], 1.0),
            "security": (["security", "encryption", "malware", "vpn", "password", "mfa", "incident", "breach"], 1.0),
            "remote_work": (["remote", "work", "home", "hybrid", "telecommute", "wfh"], 0.9),
            "policy": (["policy", "procedure", "requirement", "guideline", "compliance"], 0.8),
            "benefits": (["benefit", "insurance", "health", "medical", "wellness", "stipend"], 0.9),
        }
        
        query_concepts = 0
        chunk_concepts = 0
        
        for concept_name, (keywords, weight) in semantic_patterns.items():
            query_match = sum(1 for kw in keywords if kw in query_lower)
            chunk_match = sum(1 for kw in keywords if kw in chunk_lower)
            
            if query_match > 0:
                query_concepts += weight
            if chunk_match > 0:
                chunk_concepts += weight
        
        # Alignment score: how well chunk's concepts match query's concepts
        if query_concepts == 0:
            return 0.5
        
        alignment = min(1.0, chunk_concepts / query_concepts)
        return alignment
    
    def _info_density_score(self, chunk_text: str) -> float:
        """
        Score based on information density and structure.
        Favors chunks with:
        - Moderate length (not too short, not too long)
        - Presence of structured markers (colons, bullets, numbers)
        """
        words = chunk_text.split()
        word_count = len(words)
        
        # Ideal chunk size: 50-300 words
        if 50 <= word_count <= 300:
            length_score = 1.0
        elif 20 <= word_count < 50 or 300 < word_count <= 500:
            length_score = 0.8
        elif word_count < 20 or word_count > 500:
            length_score = 0.6
        else:
            length_score = 1.0
        
        # Check for structural markers (colons, numbers, bullets)
        has_colons = ":" in chunk_text
        has_numbers = bool(re.search(r"\d+", chunk_text))
        has_bullets = bool(re.search(r"^[\s]*[-•*]", chunk_text, re.MULTILINE))
        
        structure_score = (int(has_colons) + int(has_numbers) + int(has_bullets)) / 3.0
        
        return 0.7 * length_score + 0.3 * structure_score
    
    def score_chunks(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
    ) -> Dict[str, Tuple[float, Dict[str, float]]]:
        """Score chunks using multi-aspect semantic relevance."""
        results = {}
        
        for chunk in chunks:
            chunk_id = chunk.get("chunk_id", "unknown")
            chunk_text = chunk.get("source_text", "")
            
            # Compute component scores
            query_term_score = self._query_term_score(query, chunk_text)
            semantic_score = self._semantic_concept_score(query, chunk_text)
            density_score = self._info_density_score(chunk_text)
            
            # Weighted combination
            final_score = (
                self.query_terms_weight * query_term_score +
                self.semantic_concept_weight * semantic_score +
                self.info_density_weight * density_score
            )
            
            scoring_breakdown = {
                "query_term_score": query_term_score,
                "semantic_concept_score": semantic_score,
                "info_density_score": density_score,
            }
            
            results[chunk_id] = (final_score, scoring_breakdown)
        
        return results


# ---------------------------------------------------------------------------
# Reranker 2: LLM-based Relevance Scorer
# ---------------------------------------------------------------------------
class LLMReranker(ChunkReranker):
    """
    LLM-based re-ranker that uses an LLM to score chunk relevance.
    Falls back to semantic scoring if LLM is not available.
    """
    
    def __init__(self, use_fallback: bool = True):
        self.use_fallback = use_fallback
        self.fallback_reranker = SemanticRelevanceReranker()
    
    def name(self) -> str:
        return "LLMReranker"
    
    def _llm_score_batch(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
    ) -> Dict[str, Tuple[float, Dict[str, float]]]:
        """Score chunks using LLM via API call."""
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        model = os.getenv("LLM_MODEL") or "gpt-3.5-turbo"
        
        if not api_key or api_key in ["your_api_key_here"]:
            if self.use_fallback:
                return self.fallback_reranker.score_chunks(query, chunks)
            raise ValueError("OpenAI API key not configured")
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            results = {}
            
            # Score chunks in batches of 5 to stay within token limits
            for chunk in chunks:
                chunk_id = chunk.get("chunk_id", "unknown")
                chunk_text = chunk.get("source_text", "")
                
                prompt = f"""Rate the relevance of the following document chunk to the query on a scale of 0-100.
Consider how directly the chunk answers or relates to the query.

Query: {query}

Document Chunk:
{chunk_text}

Provide only the numeric score (0-100) as your response."""
                
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.0,
                        max_tokens=10,
                    )
                    score_text = response.choices[0].message.content.strip()
                    score = float(score_text) / 100.0  # Normalize to [0, 1]
                    score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
                except (ValueError, IndexError, AttributeError) as e:
                    score = 0.5  # Default score if parsing fails
                
                results[chunk_id] = (score, {"llm_score": score})
            
            return results
        
        except Exception as e:
            if self.use_fallback:
                return self.fallback_reranker.score_chunks(query, chunks)
            raise
    
    def score_chunks(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
    ) -> Dict[str, Tuple[float, Dict[str, float]]]:
        """Score chunks using LLM with fallback to semantic scoring."""
        return self._llm_score_batch(query, chunks)


# ---------------------------------------------------------------------------
# Cross-Encoder Style Reranker (Hybrid approach)
# ---------------------------------------------------------------------------
class HybridReranker(ChunkReranker):
    """
    Hybrid re-ranker combining vector similarity with semantic relevance.
    Useful when you have both vector scores and want semantic refinement.
    """
    
    def __init__(self):
        self.semantic_reranker = SemanticRelevanceReranker()
        self.vector_weight = 0.4  # Weight of original vector score
        self.semantic_weight = 0.6  # Weight of semantic re-ranking
    
    def name(self) -> str:
        return "HybridReranker"
    
    def score_chunks(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
    ) -> Dict[str, Tuple[float, Dict[str, float]]]:
        """Score chunks using hybrid vector + semantic approach."""
        # Get semantic scores
        semantic_scores = self.semantic_reranker.score_chunks(query, chunks)
        
        results = {}
        for chunk in chunks:
            chunk_id = chunk.get("chunk_id", "unknown")
            
            # Get vector score if available
            vector_score = chunk.get("vector_score", 0.5)  # Default if not provided
            
            # Get semantic score
            semantic_score, breakdown = semantic_scores.get(chunk_id, (0.5, {}))
            
            # Combine scores
            final_score = (
                self.vector_weight * vector_score +
                self.semantic_weight * semantic_score
            )
            
            combined_breakdown = {
                "vector_score": vector_score,
                "semantic_score": semantic_score,
                **breakdown
            }
            
            results[chunk_id] = (final_score, combined_breakdown)
        
        return results


# ---------------------------------------------------------------------------
# Two-Stage Retrieval Pipeline with Re-ranking
# ---------------------------------------------------------------------------
class TwoStageRetrievalPipeline:
    """
    Two-stage retrieval pipeline:
    1. Stage 1: Initial retrieval with larger k_candidate
    2. Stage 2: Re-rank candidates with final top-k selection
    """
    
    def __init__(
        self,
        reranker: Optional[ChunkReranker] = None,
        k_candidate: int = 10,
        k_final: int = 3,
    ):
        self.reranker = reranker or SemanticRelevanceReranker()
        self.k_candidate = k_candidate
        self.k_final = k_final
    
    def rerank_candidates(
        self,
        query: str,
        initial_candidates: List[Dict[str, Any]],
    ) -> RerangingResult:
        """
        Re-rank initial candidates and return refined top-k results.
        
        Args:
            query: The user query
            initial_candidates: List of chunks from initial retrieval (already sorted by vector similarity)
        
        Returns:
            RerangingResult with before/after rankings and scores
        """
        # Prepare candidates as RerankedChunk objects
        candidates_reranked_chunk = []
        for i, chunk in enumerate(initial_candidates):
            chunk_id = chunk.get("chunk_id", f"chunk_{i}")
            reranked = RerankedChunk(
                rank=i + 1,
                chunk_id=chunk_id,
                source_text=chunk.get("source_text", ""),
                metadata=chunk.get("metadata", {}),
                vector_score=chunk.get("vector_score", chunk.get("score", 0.0)),
                rerank_score=0.0,  # Will be filled in
                scoring_breakdown={},
            )
            candidates_reranked_chunk.append(reranked)
        
        # Get re-ranking scores
        rerank_scores = self.reranker.score_chunks(query, initial_candidates)
        
        # Update re-rank scores
        for candidate in candidates_reranked_chunk:
            if candidate.chunk_id in rerank_scores:
                score, breakdown = rerank_scores[candidate.chunk_id]
                candidate.rerank_score = score
                candidate.scoring_breakdown = breakdown
        
        # Sort by re-rank score (descending)
        candidates_reranked_chunk.sort(key=lambda x: x.rerank_score, reverse=True)
        
        # Assign new ranks after re-ranking
        for i, candidate in enumerate(candidates_reranked_chunk):
            candidate.rank = i + 1
        
        # Take top-k final results
        final_results = candidates_reranked_chunk[:self.k_final]
        
        result = RerangingResult(
            query=query,
            k_candidate=self.k_candidate,
            k_final=self.k_final,
            candidates_initial=candidates_reranked_chunk,
            results_reranked=final_results,
            reranker_name=self.reranker.name(),
        )
        
        return result
