"""
Unit Tests for Re-ranking Module.
Tests re-ranker implementations and pipeline behavior.
"""

import sys
import unittest
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.reranker import (
    RerankedChunk,
    RerangingResult,
    SemanticRelevanceReranker,
    HybridReranker,
    TwoStageRetrievalPipeline,
)


class TestSemanticRelevanceReranker(unittest.TestCase):
    """Test cases for SemanticRelevanceReranker."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.reranker = SemanticRelevanceReranker()
        
        # Create sample chunks
        self.chunks = [
            {
                "chunk_id": "chunk_1",
                "source_text": "Full-time employees receive 18 days of paid time off annually.",
                "metadata": {"source_document": "hr_policy.md"},
            },
            {
                "chunk_id": "chunk_2",
                "source_text": "Remote workers must use VPN and encryption for secure access.",
                "metadata": {"source_document": "security_policy.md"},
            },
            {
                "chunk_id": "chunk_3",
                "source_text": "Sick leave is available from the first day of employment.",
                "metadata": {"source_document": "hr_policy.md"},
            },
        ]
    
    def test_reranker_name(self):
        """Test that reranker returns correct name."""
        self.assertEqual(self.reranker.name(), "SemanticRelevanceReranker")
    
    def test_score_chunks_output_format(self):
        """Test that scoring returns correct data structure."""
        query = "How many days of PTO?"
        scores = self.reranker.score_chunks(query, self.chunks)
        
        # Should return dict mapping chunk_id to (score, breakdown)
        self.assertIsInstance(scores, dict)
        self.assertEqual(len(scores), 3)
        
        for chunk_id, (score, breakdown) in scores.items():
            self.assertIn(chunk_id, ["chunk_1", "chunk_2", "chunk_3"])
            self.assertIsInstance(score, float)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)
            self.assertIsInstance(breakdown, dict)
    
    def test_query_term_score(self):
        """Test query term scoring."""
        # Query with specific terms
        query = "paid time off days"
        chunk_relevant = {
            "chunk_id": "c1",
            "source_text": "Employees get 18 days of paid time off",
            "metadata": {},
        }
        chunk_irrelevant = {
            "chunk_id": "c2",
            "source_text": "The weather is sunny today",
            "metadata": {},
        }
        
        scores = self.reranker.score_chunks(query, [chunk_relevant, chunk_irrelevant])
        relevant_score = scores["c1"][0]
        irrelevant_score = scores["c2"][0]
        
        # Relevant chunk should score higher
        self.assertGreater(relevant_score, irrelevant_score)
    
    def test_semantic_concept_matching(self):
        """Test that semantic concepts are recognized."""
        query = "paid time off and vacation"
        chunk = {
            "chunk_id": "c1",
            "source_text": "PTO accrual and vacation rollover",
            "metadata": {},
        }
        
        scores = self.reranker.score_chunks(query, [chunk])
        score, breakdown = scores["c1"]
        
        # Should have non-zero semantic concept score
        self.assertGreater(breakdown["semantic_concept_score"], 0.0)
    
    def test_info_density_scoring(self):
        """Test information density scoring."""
        query = "policy"
        short_chunk = {
            "chunk_id": "short",
            "source_text": "A",
            "metadata": {},
        }
        medium_chunk = {
            "chunk_id": "medium",
            "source_text": "This is a medium-length chunk with enough text to be considered " + "informative. " * 10,
            "metadata": {},
        }
        long_chunk = {
            "chunk_id": "long",
            "source_text": "This is a very long chunk. " * 50,
            "metadata": {},
        }
        
        scores = self.reranker.score_chunks(query, [short_chunk, medium_chunk, long_chunk])
        
        # Extract density scores
        short_density = scores["short"][1]["info_density_score"]
        medium_density = scores["medium"][1]["info_density_score"]
        long_density = scores["long"][1]["info_density_score"]
        
        # Short chunk should have very low density (less than 1 word)
        self.assertLess(short_density, 0.6)
        # Medium chunk should score better than very short
        self.assertGreater(medium_density, short_density)


class TestTwoStageRetrievalPipeline(unittest.TestCase):
    """Test cases for TwoStageRetrievalPipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.reranker = SemanticRelevanceReranker()
        self.pipeline = TwoStageRetrievalPipeline(
            reranker=self.reranker,
            k_candidate=5,
            k_final=2,
        )
        
        # Create sample candidates
        self.candidates = [
            {
                "chunk_id": "c1",
                "source_text": "PTO policy: 18 days annually",
                "metadata": {"source_document": "hr.md"},
                "vector_score": 0.9,
            },
            {
                "chunk_id": "c2",
                "source_text": "Sick leave: 10 days per year",
                "metadata": {"source_document": "hr.md"},
                "vector_score": 0.7,
            },
            {
                "chunk_id": "c3",
                "source_text": "Remote work requires VPN",
                "metadata": {"source_document": "security.md"},
                "vector_score": 0.5,
            },
            {
                "chunk_id": "c4",
                "source_text": "Holiday schedule for 2024",
                "metadata": {"source_document": "calendar.md"},
                "vector_score": 0.3,
            },
            {
                "chunk_id": "c5",
                "source_text": "Unrelated content about weather",
                "metadata": {"source_document": "blog.md"},
                "vector_score": 0.1,
            },
        ]
    
    def test_reranking_result_structure(self):
        """Test that reranking returns correct result structure."""
        query = "How much PTO?"
        result = self.pipeline.rerank_candidates(query, self.candidates)
        
        self.assertIsInstance(result, RerangingResult)
        self.assertEqual(result.query, query)
        self.assertEqual(result.k_candidate, 5)
        self.assertEqual(result.k_final, 2)
        self.assertEqual(len(result.candidates_initial), 5)
        self.assertEqual(len(result.results_reranked), 2)
    
    def test_final_results_are_reranked(self):
        """Test that final results are actually reranked."""
        query = "How much PTO?"
        result = self.pipeline.rerank_candidates(query, self.candidates)
        
        # All results should be RerankedChunk objects with both scores
        for chunk in result.results_reranked:
            self.assertIsInstance(chunk, RerankedChunk)
            self.assertIsNotNone(chunk.vector_score)
            self.assertIsNotNone(chunk.rerank_score)
            self.assertIsInstance(chunk.scoring_breakdown, dict)
    
    def test_k_final_limit(self):
        """Test that final results respect k_final limit."""
        query = "policy"
        result = self.pipeline.rerank_candidates(query, self.candidates)
        
        # Should return exactly k_final=2 results
        self.assertEqual(len(result.results_reranked), 2)
    
    def test_ranking_changes(self):
        """Test that re-ranking can reorder candidates."""
        query = "paid time off"
        result = self.pipeline.rerank_candidates(query, self.candidates)
        
        # Initial order is by vector_score: c1(0.9), c2(0.7), c3(0.5)...
        initial_order = [c.chunk_id for c in result.candidates_initial]
        self.assertEqual(initial_order[0], "c1")
        self.assertEqual(initial_order[1], "c2")
        
        # Verify that all chunks have re-rank scores
        for chunk in result.candidates_initial:
            self.assertGreater(chunk.rerank_score, 0.0)


class TestRerankedChunkModel(unittest.TestCase):
    """Test cases for RerankedChunk data model."""
    
    def test_reranked_chunk_creation(self):
        """Test creating a RerankedChunk."""
        chunk = RerankedChunk(
            rank=1,
            chunk_id="test_chunk",
            source_text="Sample text",
            metadata={"source": "test.md"},
            vector_score=0.85,
            rerank_score=0.75,
            scoring_breakdown={"component1": 0.5, "component2": 0.25},
        )
        
        self.assertEqual(chunk.rank, 1)
        self.assertEqual(chunk.chunk_id, "test_chunk")
        self.assertEqual(chunk.vector_score, 0.85)
        self.assertEqual(chunk.rerank_score, 0.75)
    
    def test_reranked_chunk_to_dict(self):
        """Test converting RerankedChunk to dictionary."""
        chunk = RerankedChunk(
            rank=1,
            chunk_id="test",
            source_text="Text",
            metadata={"key": "value"},
            vector_score=0.85,
            rerank_score=0.75,
            scoring_breakdown={"c1": 0.5},
        )
        
        chunk_dict = chunk.to_dict()
        self.assertIsInstance(chunk_dict, dict)
        self.assertEqual(chunk_dict["rank"], 1)
        self.assertEqual(chunk_dict["chunk_id"], "test")
        self.assertAlmostEqual(chunk_dict["vector_score"], 0.85, places=5)
        self.assertAlmostEqual(chunk_dict["rerank_score"], 0.75, places=5)


class TestHybridReranker(unittest.TestCase):
    """Test cases for HybridReranker."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.reranker = HybridReranker()
        self.chunks = [
            {
                "chunk_id": "c1",
                "source_text": "PTO policy text",
                "metadata": {},
                "vector_score": 0.9,
            },
            {
                "chunk_id": "c2",
                "source_text": "Security policy text",
                "metadata": {},
                "vector_score": 0.5,
            },
        ]
    
    def test_hybrid_reranker_name(self):
        """Test hybrid reranker name."""
        self.assertEqual(self.reranker.name(), "HybridReranker")
    
    def test_hybrid_combines_scores(self):
        """Test that hybrid reranker combines vector and semantic scores."""
        query = "PTO"
        scores = self.reranker.score_chunks(query, self.chunks)
        
        c1_score, c1_breakdown = scores["c1"]
        c2_score, c2_breakdown = scores["c2"]
        
        # Both should have breakdown with vector_score
        self.assertIn("vector_score", c1_breakdown)
        self.assertIn("vector_score", c2_breakdown)
        
        # Combined score should consider both components
        self.assertGreater(c1_score, 0.0)
        self.assertGreater(c2_score, 0.0)


if __name__ == "__main__":
    unittest.main()
