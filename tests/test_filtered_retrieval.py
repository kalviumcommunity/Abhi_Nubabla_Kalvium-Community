"""
Unit tests for Metadata Filtering & Hybrid Vector Retrieval Engine.
"""

import math
import unittest
from pathlib import Path
from src.filtered_retrieval import (
    MetadataFilter,
    HybridScorer,
    FilteredRetriever,
    FilteredSearchResultChunk,
    DenseSemanticEmbedder,
    cosine_similarity,
)
from src.retriever import retrieve_filtered


class TestMetadataFilter(unittest.TestCase):
    def setUp(self):
        self.chunk_meta_1 = {
            "source_document": "employee_benefits.md",
            "file_type": ".md",
            "section": "Section 6.0: Employee Benefits > 1. PTO Accrual",
            "page": None,
        }
        self.chunk_meta_2 = {
            "source_document": "document.pdf",
            "file_type": ".pdf",
            "section": "RAG System Documentation",
            "page": 2,
        }
        self.chunk_meta_3 = {
            "source_document": "it_security_policy.md",
            "file_type": ".md",
            "section": "Corporate IT Security > 4. Incident Reporting",
            "page": None,
        }

    def test_document_exact_filter(self):
        f = MetadataFilter(source_document="employee_benefits.md")
        self.assertTrue(f.matches(self.chunk_meta_1))
        self.assertFalse(f.matches(self.chunk_meta_2))
        self.assertFalse(f.matches(self.chunk_meta_3))

    def test_file_type_filter(self):
        f = MetadataFilter(file_type=".pdf")
        self.assertFalse(f.matches(self.chunk_meta_1))
        self.assertTrue(f.matches(self.chunk_meta_2))
        self.assertFalse(f.matches(self.chunk_meta_3))

    def test_section_contains_filter(self):
        f = MetadataFilter(section_contains="Incident")
        self.assertFalse(f.matches(self.chunk_meta_1))
        self.assertFalse(f.matches(self.chunk_meta_2))
        self.assertTrue(f.matches(self.chunk_meta_3))

    def test_multiple_constraints_and(self):
        f = MetadataFilter(source_document="it_security_policy.md", section_contains="Incident")
        self.assertTrue(f.matches(self.chunk_meta_3))

        f_mismatch = MetadataFilter(source_document="employee_benefits.md", section_contains="Incident")
        self.assertFalse(f_mismatch.matches(self.chunk_meta_3))

    def test_custom_predicate_filter(self):
        f = MetadataFilter(custom_predicate=lambda m, text: m.get("page") == 2)
        self.assertFalse(f.matches(self.chunk_meta_1))
        self.assertTrue(f.matches(self.chunk_meta_2))


class TestHybridScorer(unittest.TestCase):
    def test_lexical_overlap(self):
        query = "ransomware malware incident reporting"
        doc = "In case of ransomware or malware, report immediately to the incident hotline."
        score = HybridScorer.compute_lexical_score(query, doc)
        self.assertGreaterEqual(score, 0.5)

    def test_exact_term_boosting(self):
        query = "hotline phone number"
        doc_without = "Call the security team on slack."
        doc_with = "Call the security hotline at extension 4357 immediately."

        score_without = HybridScorer.compute_lexical_score(query, doc_without, exact_terms=["4357"])
        score_with = HybridScorer.compute_lexical_score(query, doc_with, exact_terms=["4357"])
        self.assertGreater(score_with, score_without)

    def test_score_fusion_alpha_extremes(self):
        v_score = 0.8
        l_score = 0.4

        # alpha = 0.0 -> pure vector
        self.assertEqual(HybridScorer.fuse_scores(v_score, l_score, alpha=0.0), 0.8)

        # alpha = 1.0 -> pure lexical
        self.assertEqual(HybridScorer.fuse_scores(v_score, l_score, alpha=1.0), 0.4)

        # alpha = 0.5 -> average
        self.assertEqual(HybridScorer.fuse_scores(v_score, l_score, alpha=0.5), 0.6)


class TestFilteredRetriever(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retriever = FilteredRetriever()

    def test_unfiltered_retrieval_returns_top_k(self):
        query = "How many days of paid time off do employees get?"
        results = self.retriever.retrieve(query, filter_spec=None, k=3)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].rank, 1)

    def test_filtered_retrieval_scopes_to_target_document(self):
        query = "What are the rules for annual leave and PTO rollover?"
        f = MetadataFilter(source_document="employee_benefits.md")
        results = self.retriever.retrieve(query, filter_spec=f, k=3)

        self.assertGreaterEqual(len(results), 1)
        for chunk in results:
            self.assertEqual(chunk.source_document, "employee_benefits.md")

    def test_compare_filtered_vs_unfiltered_demonstrates_precision_gain(self):
        query = "What is the procedure for reporting a suspected security incident or lost hardware?"
        f = MetadataFilter(source_document="it_security_policy.md")
        comp = self.retriever.compare_filtered_vs_unfiltered(
            query=query,
            filter_spec=f,
            target_document="it_security_policy.md",
            k=5,
        )

        self.assertEqual(comp["filtered"]["precision"], 1.0)
        self.assertGreaterEqual(comp["precision_gain"], 0.0)
        self.assertTrue(comp["precision_improved"])

    def test_hybrid_search_with_exact_terms(self):
        query = "What is the 24/7 hotline phone extension for reporting active malware?"
        f = MetadataFilter(source_document="it_security_policy.md")
        results = self.retriever.retrieve(
            query=query,
            filter_spec=f,
            k=2,
            alpha=0.3,
            exact_terms=["4357", "#security-incident"],
        )
        self.assertGreaterEqual(len(results), 1)
        self.assertIn("4357", results[0].text)

    def test_public_retrieve_filtered_interface(self):
        query = "Hardware encryption requirements"
        f = MetadataFilter(source_document="remote_work_policy.md")
        results = retrieve_filtered(query=query, filter_spec=f, k=2)
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].source_document, "remote_work_policy.md")

    def test_empty_query_returns_empty_list(self):
        self.assertEqual(self.retriever.retrieve("", k=3), [])
        self.assertEqual(self.retriever.retrieve("   ", k=3), [])

    def test_no_match_filter_returns_empty_list(self):
        f = MetadataFilter(source_document="non_existent_doc.xyz")
        results = self.retriever.retrieve("Any query", filter_spec=f, k=3)
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
