"""
Unit tests for Full RAG System Evaluation & Answer Quality Scoring Engine.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.rag_evaluator import (
    BENCHMARK_TEST_SET,
    TestQueryItem,
    AnswerQualityScore,
    CitationAccuracyCheck,
    score_correctness,
    score_grounding,
    check_citation_accuracy,
    diagnose_failure_case,
    evaluate_rag_system
)
from src.similarity_search import RetrievedChunk


class TestRAGEvaluator(unittest.TestCase):

    def setUp(self):
        self.sample_item = TestQueryItem(
            test_id="test_q01",
            query="How many PTO days do employees get?",
            category="Factual Policy",
            expected_answer="Employees get 18 PTO days.",
            expected_keywords=["18 days", "pto", "rollover"],
            expected_sources=["employee_benefits.md"],
            is_out_of_domain=False
        )

        self.out_of_domain_item = TestQueryItem(
            test_id="test_q02",
            query="What is the Mars colony policy?",
            category="Out-Of-Domain Fallback",
            expected_answer="No information available.",
            expected_keywords=["don't have access"],
            expected_sources=[],
            is_out_of_domain=True
        )

    def test_benchmark_test_set_structure(self):
        """Task 1: Verify test set structure and expected ground-truth metadata."""
        self.assertTrue(len(BENCHMARK_TEST_SET) >= 5)
        for item in BENCHMARK_TEST_SET:
            self.assertTrue(bool(item.test_id))
            self.assertTrue(bool(item.query))
            self.assertTrue(isinstance(item.expected_keywords, list))
            self.assertTrue(isinstance(item.expected_sources, list))

    def test_score_correctness_normal_query(self):
        """Task 2: Test correctness scoring on normal factual queries."""
        ans_perfect = "Employees receive 18 days of PTO with rollover up to 5 days."
        score, matched, missing, notes = score_correctness(ans_perfect, self.sample_item)
        self.assertEqual(score, 1.0)
        self.assertEqual(len(matched), 3)

        ans_partial = "Employees get 18 days of PTO."
        score2, matched2, missing2, notes2 = score_correctness(ans_partial, self.sample_item)
        self.assertTrue(score2 > 0.0)

    def test_score_correctness_fallback_query(self):
        """Task 2: Test correctness scoring on fallback queries."""
        ans_fallback = "I don't have access to this information in the verified company guidelines."
        score, matched, missing, notes = score_correctness(ans_fallback, self.out_of_domain_item)
        self.assertEqual(score, 1.0)

        ans_hallucinated = "Mars colony subsidies provide $10,000 per month."
        score2, matched2, missing2, notes2 = score_correctness(ans_hallucinated, self.out_of_domain_item)
        self.assertEqual(score2, 0.0)

    def test_score_grounding(self):
        """Task 2: Test grounding score calculation."""
        context = "[1] Source: employee_benefits.md\nEmployees receive 18 days of PTO annually."
        ans_grounded = "Employees receive 18 days of PTO annually [1]."

        score, supp, unsupp, notes = score_grounding(ans_grounded, context, self.sample_item)
        self.assertEqual(score, 1.0)
        self.assertEqual(supp, 1)

    def test_check_citation_accuracy(self):
        """Task 3: Test citation accuracy checking."""
        citation_map = {
            "[1]": {
                "source_document": "employee_benefits.md",
                "chunk_id": "chunk_001"
            }
        }
        ans = "Employees get 18 days of PTO [1]."
        res = check_citation_accuracy(ans, citation_map, self.sample_item)
        self.assertEqual(res.citation_precision, 1.0)
        self.assertEqual(res.citation_recall, 1.0)
        self.assertTrue(res.is_citation_accurate)

        # Invalid citation tag
        ans_invalid = "Employees get 18 days [99]."
        res2 = check_citation_accuracy(ans_invalid, citation_map, self.sample_item)
        self.assertIn("[99]", res2.invalid_citations)
        self.assertFalse(res2.is_citation_accurate)

    def test_diagnose_failure_case(self):
        """Task 4: Test failure categorization logic."""
        q_score = AnswerQualityScore(
            correctness_score=0.40,
            grounding_score=0.50,
            matched_keywords=[],
            missing_keywords=["18 days"],
            supported_claims_count=0,
            unsupported_claims_count=2,
            correctness_notes="",
            grounding_notes=""
        )
        cit_check = CitationAccuracyCheck(
            citation_precision=1.0,
            citation_recall=0.0,
            citations_found=[],
            invalid_citations=[],
            expected_sources_cited=[],
            missing_expected_sources=["employee_benefits.md"],
            is_citation_accurate=False,
            citation_notes=""
        )

        fail = diagnose_failure_case(self.sample_item, q_score, cit_check, is_fallback=False)
        self.assertIsNotNone(fail)
        self.assertEqual(fail.failure_type, "Retrieval Miss / Incorrect Coverage")

    def test_end_to_end_evaluate_rag_system(self):
        """Task 5: Test end-to-end evaluation suite."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve_top_k.return_value = [
            RetrievedChunk(
                chunk_id="chunk_001",
                score=0.85,
                rank=1,
                source_text="Employees receive 18 days of PTO annually.",
                metadata={"source_document": "employee_benefits.md", "section": "PTO"}
            )
        ]

        summary = evaluate_rag_system(
            test_set=[self.sample_item, self.out_of_domain_item],
            retriever=mock_retriever
        )

        self.assertEqual(summary["total_queries"], 2)
        self.assertIn("overall_quality_score", summary)
        self.assertIn("metrics_summary", summary)


if __name__ == "__main__":
    unittest.main()
