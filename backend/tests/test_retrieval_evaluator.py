"""
Unit Tests for Retrieval Quality Evaluation Engine.
Tests metrics calculation (Recall@k, Precision@k, MRR, NDCG@k), dataset validation,
failure inspection, and end-to-end evaluation reporting.
"""

from __future__ import annotations

import json
import math
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.retrieval_evaluator import (
    LABELLED_EVALUATION_DATASET,
    LabelledQuery,
    FailureDiagnostic,
    RetrievalMetricsCalculator,
    RetrievalFailureInspector,
    RetrievalEvaluator,
    generate_evaluation_report,
)
from src.similarity_search import RetrievedChunk


class TestLabelledQueryDataset(unittest.TestCase):
    """Validates the structure, integrity, and coverage of the evaluation dataset."""

    def test_dataset_size_and_types(self):
        """Dataset must contain benchmark queries covering various HR and security topics."""
        self.assertGreaterEqual(len(LABELLED_EVALUATION_DATASET), 10)
        for lq in LABELLED_EVALUATION_DATASET:
            self.assertIsInstance(lq, LabelledQuery)
            self.assertTrue(lq.query_id.startswith("eval_q"))
            self.assertGreater(len(lq.query.strip()), 10)
            self.assertGreater(len(lq.relevant_chunk_ids), 0)
            self.assertGreater(len(lq.relevant_source_documents), 0)
            self.assertIn(lq.difficulty, ["Easy", "Medium", "Hard/Borderline", "Edge/Adversarial"])

    def test_graded_relevance_consistency(self):
        """Every primary relevant chunk ID must have an assigned positive graded relevance score."""
        for lq in LABELLED_EVALUATION_DATASET:
            for cid in lq.relevant_chunk_ids:
                self.assertIn(cid, lq.graded_relevance)
                self.assertGreaterEqual(lq.graded_relevance[cid], 1)

    def test_serialization(self):
        """Ensure LabelledQuery converts cleanly to a dictionary."""
        first_q = LABELLED_EVALUATION_DATASET[0]
        q_dict = first_q.to_dict()
        self.assertEqual(q_dict["query_id"], first_q.query_id)
        self.assertEqual(q_dict["domain"], first_q.domain)
        self.assertIsInstance(q_dict["graded_relevance"], dict)


class TestRetrievalMetricsCalculator(unittest.TestCase):
    """Unit tests for individual retrieval metrics: Recall, Precision, MRR, NDCG."""

    def setUp(self):
        self.calc = RetrievalMetricsCalculator

    def test_recall_at_k(self):
        """Test Recall@k calculation for complete, partial, and zero retrieval."""
        ground_truth = {"c1", "c2"}
        
        # k=1: retrieves c1 (1 of 2 found => 0.5)
        self.assertAlmostEqual(self.calc.calculate_recall_at_k(["c1", "x", "y"], ground_truth, 1), 0.5)
        # k=2: retrieves c1, c2 (2 of 2 found => 1.0)
        self.assertAlmostEqual(self.calc.calculate_recall_at_k(["c1", "c2", "x"], ground_truth, 2), 1.0)
        # k=3: retrieves x, y, z (0 of 2 found => 0.0)
        self.assertAlmostEqual(self.calc.calculate_recall_at_k(["x", "y", "z"], ground_truth, 3), 0.0)
        # empty ground truth edge case
        self.assertEqual(self.calc.calculate_recall_at_k(["c1"], set(), 1), 0.0)

    def test_precision_at_k(self):
        """Test Precision@k calculation with binary relevance matching."""
        ground_truth = {"c1", "c2"}

        # k=1: retrieved c1 (1/1 => 1.0)
        self.assertAlmostEqual(self.calc.calculate_precision_at_k(["c1", "x", "y"], ground_truth, 1), 1.0)
        # k=2: retrieved c1, x (1/2 => 0.5)
        self.assertAlmostEqual(self.calc.calculate_precision_at_k(["c1", "x", "y"], ground_truth, 2), 0.5)
        # k=3: retrieved c1, c2, x (2/3 => 0.6667)
        self.assertAlmostEqual(self.calc.calculate_precision_at_k(["c1", "c2", "x"], ground_truth, 3), 0.6667)
        # k=0 edge case
        self.assertEqual(self.calc.calculate_precision_at_k(["c1"], ground_truth, 0), 0.0)

    def test_hit_rate_at_k(self):
        """Test Hit Rate (1 if at least one relevant chunk is in top-k, else 0)."""
        ground_truth = {"c1"}
        self.assertEqual(self.calc.calculate_hit_rate_at_k(["c1", "x", "y"], ground_truth, 1), 1)
        self.assertEqual(self.calc.calculate_hit_rate_at_k(["x", "c1", "y"], ground_truth, 1), 0)
        self.assertEqual(self.calc.calculate_hit_rate_at_k(["x", "c1", "y"], ground_truth, 2), 1)
        self.assertEqual(self.calc.calculate_hit_rate_at_k(["x", "y", "z"], ground_truth, 3), 0)

    def test_mrr(self):
        """Test Mean Reciprocal Rank calculation based on first relevant item position."""
        ground_truth = {"target"}
        
        # Rank 1 -> MRR = 1/1 = 1.0
        self.assertAlmostEqual(self.calc.calculate_reciprocal_rank(["target", "x", "y"], ground_truth), 1.0)
        # Rank 2 -> MRR = 1/2 = 0.5
        self.assertAlmostEqual(self.calc.calculate_reciprocal_rank(["x", "target", "y"], ground_truth), 0.5)
        # Rank 3 -> MRR = 1/3 = 0.3333
        self.assertAlmostEqual(self.calc.calculate_reciprocal_rank(["x", "y", "target"], ground_truth), 0.3333)
        # Not found -> MRR = 0.0
        self.assertEqual(self.calc.calculate_reciprocal_rank(["x", "y", "z"], ground_truth), 0.0)

    def test_ndcg_at_k(self):
        """Test Normalized Discounted Cumulative Gain with graded relevance."""
        graded = {"c1": 2, "c2": 1, "c3": 0}
        
        # Perfect ranking: [c1, c2] -> NDCG should be 1.0
        self.assertAlmostEqual(self.calc.calculate_ndcg_at_k(["c1", "c2"], graded, 2), 1.0)
        
        # Inverted ranking: [c2, c1] -> DCG < IDCG, NDCG < 1.0
        ndcg_inverted = self.calc.calculate_ndcg_at_k(["c2", "c1"], graded, 2)
        self.assertLess(ndcg_inverted, 1.0)
        self.assertGreater(ndcg_inverted, 0.0)

        # No relevant items retrieved -> NDCG = 0.0
        self.assertEqual(self.calc.calculate_ndcg_at_k(["x", "y"], graded, 2), 0.0)

    def test_f1_at_k(self):
        """Test F1 score calculation from precision and recall."""
        self.assertAlmostEqual(self.calc.calculate_f1_at_k(precision=1.0, recall=1.0), 1.0)
        self.assertAlmostEqual(self.calc.calculate_f1_at_k(precision=0.5, recall=1.0), 0.6667)
        self.assertEqual(self.calc.calculate_f1_at_k(precision=0.0, recall=0.0), 0.0)


class TestRetrievalFailureInspector(unittest.TestCase):
    """Tests the diagnostic analysis and root-cause classifier for failure inspection."""

    def test_inspect_optimal_case(self):
        """When the primary chunk is at Rank 1 and all relevant are found, return None."""
        q = LABELLED_EVALUATION_DATASET[0]  # requires employee_benefits_chunk_001
        
        mock_chunks = [
            RetrievedChunk(rank=1, chunk_id="employee_benefits_chunk_001", source_text="PTO details", metadata={"source_document": "employee_benefits.md"}, score=0.92),
            RetrievedChunk(rank=2, chunk_id="employee_benefits_chunk_002", source_text="Sick leave", metadata={"source_document": "employee_benefits.md"}, score=0.85),
        ]
        
        inspection = RetrievalFailureInspector.inspect_query_run(q, mock_chunks, k=3)
        self.assertIsNone(inspection)

    def test_inspect_rank_suboptimal_case(self):
        """When primary chunk is retrieved at rank 2 or 3, classify with diagnostic."""
        q = LABELLED_EVALUATION_DATASET[0]
        
        mock_chunks = [
            RetrievedChunk(rank=1, chunk_id="security_chunk_001", source_text="Security overview", metadata={"source_document": "security_policy.md"}, score=0.88),
            RetrievedChunk(rank=2, chunk_id="employee_benefits_chunk_001", source_text="PTO details", metadata={"source_document": "employee_benefits.md"}, score=0.84),
        ]
        
        inspection = RetrievalFailureInspector.inspect_query_run(q, mock_chunks, k=3)
        self.assertIsNotNone(inspection)
        self.assertEqual(inspection.first_relevant_rank, 2)
        self.assertIn("Borderline Rank Inversion", inspection.root_cause_category)
        self.assertGreater(len(inspection.recommended_mitigation), 10)

    def test_inspect_missed_case(self):
        """When primary chunk is missing from top-k, classify as failure with mitigation."""
        q = LABELLED_EVALUATION_DATASET[0]
        
        mock_chunks = [
            RetrievedChunk(rank=1, chunk_id="other_001", source_text="Other info", metadata={"source_document": "other.md"}, score=0.80),
            RetrievedChunk(rank=2, chunk_id="other_002", source_text="Other info 2", metadata={"source_document": "other.md"}, score=0.75),
        ]
        
        inspection = RetrievalFailureInspector.inspect_query_run(q, mock_chunks, k=3)
        self.assertIsNotNone(inspection)
        self.assertIsNone(inspection.first_relevant_rank)
        self.assertIn(q.relevant_chunk_ids[0], inspection.expected_relevant_ids)
        self.assertGreater(len(inspection.recommended_mitigation), 10)


class TestRetrievalEvaluatorIntegration(unittest.TestCase):
    """End-to-end evaluation execution and report generation tests."""

    @classmethod
    def setUpClass(cls):
        chunks_path = Path(__file__).resolve().parent.parent / "data" / "embedded_chunks.json"
        if not chunks_path.exists():
            raise unittest.SkipTest(f"Required corpus file missing: {chunks_path}")
        cls.evaluator = RetrievalEvaluator(vector_store_path=str(chunks_path))

    def test_evaluate_single_mode(self):
        """Test evaluating a single pipeline mode produces summary metrics and diagnostics."""
        result = self.evaluator.evaluate_pipeline_mode(mode="vector_top_k", k_values=[1, 2, 3, 5])
        
        self.assertEqual(result["mode"], "vector_top_k")
        self.assertIn("summary_metrics", result)
        self.assertIn("query_evaluations", result)
        self.assertEqual(len(result["query_evaluations"]), len(LABELLED_EVALUATION_DATASET))
        
        summary = result["summary_metrics"]
        self.assertGreaterEqual(summary["metrics_by_k"]["k=3"]["mean_recall"], 0.70)
        self.assertGreaterEqual(summary["mean_mrr"], 0.70)

    def test_run_full_comparative_benchmark(self):
        """Test running comparative benchmark across all 3 retrieval pipelines."""
        benchmark = self.evaluator.run_full_comparative_benchmark(
            k_values=[1, 2, 3, 5, 10],
            save_artifacts=False,
        )
        
        self.assertIn("metadata", benchmark)
        self.assertIn("pipeline_comparisons", benchmark)
        comparisons = benchmark["pipeline_comparisons"]
        self.assertIn("vector_top_k", comparisons)
        self.assertIn("metadata_filtered", comparisons)
        self.assertIn("two_stage_rerank", comparisons)

    def test_generate_evaluation_report(self):
        """Test that report generator outputs valid Markdown document with tables and failure analysis."""
        benchmark = self.evaluator.run_full_comparative_benchmark(
            k_values=[1, 2, 3, 5],
            save_artifacts=False,
        )
        report_md = generate_evaluation_report(benchmark)
        
        self.assertIn("# Systematic RAG Retrieval Quality Evaluation & Diagnostic Audit", report_md)
        self.assertIn("## 1. Executive Summary & Evaluation Framework", report_md)
        self.assertIn("## 2. Global Metric Summary by Retrieval Architecture", report_md)
        self.assertIn("## 3. Recall@k & Precision@k Progression Curve", report_md)
        self.assertIn("## 4. Per-Query Breakdown & Relevance Judgements", report_md)
        self.assertIn("## 5. Failure Case Inspection & Diagnostic Root-Cause Analysis", report_md)


if __name__ == "__main__":
    unittest.main(verbosity=2)
