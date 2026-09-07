"""
Unit tests for the RAG Top-K Vector Store Retriever Module.
Uses standard library unittest.
"""

import math
import unittest
from src.retriever import VectorStoreRetriever, DenseSemanticEmbedder, cosine_similarity


class TestDenseSemanticEmbedder(unittest.TestCase):
    def setUp(self):
        self.embedder = DenseSemanticEmbedder(dimension=1536)

    def test_embedding_dimension(self):
        vec = self.embedder.embed("How many days of paid time off do employees get?")
        self.assertEqual(len(vec), 1536)

    def test_embedding_unit_norm(self):
        vec = self.embedder.embed("Incident reporting hotline procedure")
        norm = math.sqrt(sum(x * x for x in vec))
        self.assertAlmostEqual(norm, 1.0, places=4)

    def test_empty_string_embedding(self):
        vec = self.embedder.embed("")
        self.assertTrue(all(x == 0.0 for x in vec))


class TestVectorStoreRetriever(unittest.TestCase):
    def setUp(self):
        self.mock_chunks = [
            {
                "chunk_id": "hr_chunk_001",
                "source": "data/corpus/employee_benefits.md",
                "document_name": "employee_benefits.md",
                "file_type": ".md",
                "section": "Paid Time Off (PTO)",
                "page": None,
                "position": 0,
                "text": "Full-time regular employees accrue 18 days of Paid Time Off annually. Employees may roll over a maximum of 5 unused PTO days into the following calendar year.",
                "char_count": 156,
                "token_count": 28,
                "metadata": {"header_breadcrumb": "Employee Benefits > PTO"}
            },
            {
                "chunk_id": "sec_chunk_001",
                "source": "data/corpus/it_security_policy.md",
                "document_name": "it_security_policy.md",
                "file_type": ".md",
                "section": "Incident Response",
                "page": None,
                "position": 500,
                "text": "Suspected security breaches, malware infections, and lost company devices must be reported immediately to the 24/7 IT Security Incident Hotline.",
                "char_count": 146,
                "token_count": 22,
                "metadata": {"header_breadcrumb": "IT Security > Incident Hotline"}
            },
            {
                "chunk_id": "remote_chunk_001",
                "source": "data/corpus/remote_work_policy.md",
                "document_name": "remote_work_policy.md",
                "file_type": ".md",
                "section": "VPN & Encryption",
                "page": None,
                "position": 1000,
                "text": "All remote connections to corporate networks must traverse the company-managed VPN tunnel with mandatory AES-256 encryption.",
                "char_count": 126,
                "token_count": 19,
                "metadata": {"header_breadcrumb": "Remote Work > VPN"}
            },
            {
                "chunk_id": "guide_chunk_001",
                "source": "data/corpus/document.pdf",
                "document_name": "document.pdf",
                "file_type": ".pdf",
                "section": "RAG Overview",
                "page": 1,
                "position": 0,
                "text": "Retrieval-Augmented Generation combines document loaders, semantic chunking, embedding vectors, and top-k retrieval.",
                "char_count": 117,
                "token_count": 17,
                "metadata": {}
            }
        ]
        self.retriever = VectorStoreRetriever(chunks_data=self.mock_chunks)

    def test_index_initialization(self):
        self.assertEqual(self.retriever.total_chunks, len(self.mock_chunks))

    def test_retrieve_returns_top_k(self):
        query = "How much PTO rollover is allowed?"
        results_k2 = self.retriever.retrieve(query, k=2)
        self.assertEqual(len(results_k2), 2)

        results_k3 = self.retriever.retrieve(query, k=3)
        self.assertEqual(len(results_k3), 3)

    def test_retrieve_scores_are_sorted_descending(self):
        query = "Report security breach and malware"
        results = self.retriever.retrieve(query, k=4)
        scores = [c["similarity_score"] for c in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_retrieve_includes_all_metadata_fields(self):
        query = "What are the VPN and encryption requirements?"
        results = self.retriever.retrieve(query, k=1)
        self.assertEqual(len(results), 1)
        chunk = results[0]

        expected_keys = {
            "chunk_id", "chunk_index", "document_name", "source", "file_type",
            "section", "page", "position", "token_count", "char_count",
            "similarity_score", "text", "metadata", "rank"
        }
        self.assertTrue(expected_keys.issubset(chunk.keys()))
        self.assertEqual(chunk["rank"], 1)
        self.assertIsInstance(chunk["similarity_score"], float)
        self.assertIn(chunk["chunk_id"], ["remote_chunk_001", "sec_chunk_001"])

    def test_compare_k_values_and_subset_invariance(self):
        query = "How many PTO days can be rolled over?"
        comparison = self.retriever.compare_k(query, k_values=[2, 4])
        
        self.assertIn("k=2", comparison["comparisons"])
        self.assertIn("k=4", comparison["comparisons"])
        
        k2_chunks = comparison["comparisons"]["k=2"]["chunks"]
        k4_chunks = comparison["comparisons"]["k=4"]["chunks"]
        
        self.assertEqual(len(k2_chunks), 2)
        self.assertEqual(len(k4_chunks), 4)
        
        # Invariant: the top 2 chunks of k=2 must match the first 2 chunks of k=4
        self.assertEqual(
            [c["chunk_id"] for c in k2_chunks],
            [c["chunk_id"] for c in k4_chunks[:2]]
        )
        
        # Marginal analysis check
        self.assertEqual(len(comparison["marginal_analysis"]), 1)
        self.assertEqual(comparison["marginal_analysis"][0]["chunks_added"], 2)

    def test_empty_query_returns_empty(self):
        self.assertEqual(self.retriever.retrieve("", k=3), [])
        self.assertEqual(self.retriever.retrieve("   ", k=3), [])

    def test_k_greater_than_total_chunks(self):
        results = self.retriever.retrieve("Any query", k=100)
        self.assertEqual(len(results), self.retriever.total_chunks)

    def test_min_score_threshold(self):
        query = "Paid time off and annual vacation"
        all_results = self.retriever.retrieve(query, k=4)
        top_score = all_results[0]["similarity_score"]
        
        filtered = self.retriever.retrieve(query, k=4, min_score=top_score - 0.05)
        self.assertGreaterEqual(len(filtered), 1)
        self.assertTrue(all(c["similarity_score"] >= (top_score - 0.05) for c in filtered))


class TestCosineSimilarity(unittest.TestCase):
    def test_identical_vectors(self):
        v = [0.6, 0.8]
        self.assertAlmostEqual(cosine_similarity(v, v), 1.0, places=5)

    def test_orthogonal_vectors(self):
        v1 = [1.0, 0.0]
        v2 = [0.0, 1.0]
        self.assertAlmostEqual(cosine_similarity(v1, v2), 0.0, places=5)

    def test_mismatch_dimension_raises(self):
        with self.assertRaises(ValueError):
            cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0])


if __name__ == "__main__":
    unittest.main()
