"""
Unit and Integration Tests for Top-K Vector Database Similarity Search.
"""

import unittest
from pathlib import Path
from src.similarity_search import (
    VectorStoreRetriever,
    DenseSemanticEmbedder,
    RetrievedChunk,
    cosine_similarity,
    run_retrieval_benchmark,
)
from src.retriever import retrieve_top_k


class TestSimilaritySearch(unittest.TestCase):
    def setUp(self):
        self.vector_store_path = "data/embedded_chunks.json"
        self.retriever = VectorStoreRetriever(vector_store_path=self.vector_store_path)

    def test_query_embedder_dimension(self):
        """Task 1: Verify query embedding produces 1536-dimensional unit vector."""
        query = "What is the policy for remote work and VPN access?"
        vec = self.retriever.embed_query(query)
        self.assertEqual(len(vec), 1536)

        # Verify unit normalization: ||vec||_2 == 1.0
        norm = sum(x * x for x in vec) ** 0.5
        self.assertAlmostEqual(norm, 1.0, places=4)

    def test_top_k_retrieval_count_and_ordering(self):
        """Task 2 & 3: Verify top-k returns correct count and monotonic score ordering."""
        query = "How many days of paid time off do employees get?"
        for k in [1, 2, 4]:
            results = self.retriever.retrieve_top_k(query, k=k)
            self.assertEqual(len(results), k)
            self.assertTrue(all(isinstance(c, RetrievedChunk) for c in results))

            # Verify rank numbering
            self.assertEqual([c.rank for c in results], list(range(1, k + 1)))

            # Verify monotonic descending score order
            scores = [c.score for c in results]
            self.assertEqual(scores, sorted(scores, reverse=True))

    def test_retrieved_chunk_metadata_integrity(self):
        """Task 3: Ensure retrieved chunks have scores, source text, and metadata."""
        query = "What are the password requirements and IT security rules?"
        results = self.retriever.retrieve_top_k(query, k=3)

        for c in results:
            self.assertTrue(c.chunk_id)
            self.assertIsInstance(c.score, float)
            self.assertGreaterEqual(c.score, -1.0)
            self.assertLessEqual(c.score, 1.0)
            self.assertTrue(c.source_text)
            self.assertIsInstance(c.metadata, dict)
            self.assertIn("source_document", c.metadata)
            self.assertIn("chunk_index", c.metadata)
            self.assertIn("section", c.metadata)

    def test_demonstrate_changing_k(self):
        """Task 4: Demonstrate changing k shows progression and consistent top match."""
        query = "How do I report a security incident or malware?"
        k_values = [1, 3, 5]
        runs_by_k = self.retriever.demonstrate_changing_k(query, k_values=k_values)

        self.assertEqual(set(runs_by_k.keys()), {1, 3, 5})
        self.assertEqual(runs_by_k[1].retrieved_count, 1)
        self.assertEqual(runs_by_k[3].retrieved_count, 3)
        self.assertEqual(runs_by_k[5].retrieved_count, 5)

        # Top result must be identical across all k runs
        top_chunk_k1 = runs_by_k[1].chunks[0].chunk_id
        top_chunk_k3 = runs_by_k[3].chunks[0].chunk_id
        top_chunk_k5 = runs_by_k[5].chunks[0].chunk_id
        self.assertEqual(top_chunk_k1, top_chunk_k3)
        self.assertEqual(top_chunk_k3, top_chunk_k5)

        # Token count should scale with k
        self.assertLess(runs_by_k[1].total_tokens, runs_by_k[3].total_tokens)
        self.assertLess(runs_by_k[3].total_tokens, runs_by_k[5].total_tokens)

    def test_invalid_k(self):
        """Verify proper validation for negative or zero k."""
        with self.assertRaises(ValueError):
            self.retriever.retrieve_top_k("test query", k=0)
        with self.assertRaises(ValueError):
            self.retriever.retrieve_top_k("test query", k=-2)

    def test_public_retriever_interface(self):
        """Verify public retrieve_top_k wrapper in src/retriever.py."""
        results = retrieve_top_k("VPN security policy", k=2)
        self.assertEqual(len(results), 2)
        top_docs = [c.metadata.get("source_document", "") for c in results]
        self.assertTrue(any("policy" in doc.lower() for doc in top_docs))

    def test_run_retrieval_benchmark_pipeline(self):
        """Task 5: Verify full benchmark runner exports files properly."""
        res = run_retrieval_benchmark(
            vector_store_path=self.vector_store_path,
            output_dir="data",
            k_values=[1, 3, 5],
        )
        self.assertIn("benchmark_data", res)
        self.assertTrue(Path(res["json_path"]).exists())
        self.assertTrue(Path(res["report_path"]).exists())
        self.assertGreater(Path(res["json_path"]).stat().st_size, 0)
        self.assertGreater(Path(res["report_path"]).stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
