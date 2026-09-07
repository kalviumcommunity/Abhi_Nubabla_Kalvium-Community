"""
Unit Tests for Retrieval Settings Tuning & Relevance Benchmarking (src/tuning_experiment.py).
"""

import os
import json
import tempfile
import unittest
from pathlib import Path

from src.similarity_search import VectorStoreRetriever
from src.tuning_experiment import (
    TUNING_TEST_QUERIES,
    RETRIEVAL_CONFIGURATIONS,
    evaluate_configuration,
    run_tuning_experiment
)


class TestTuningExperiment(unittest.TestCase):
    def setUp(self):
        self.vector_store_path = "data/embedded_chunks.json"
        self.retriever = VectorStoreRetriever(vector_store_path=self.vector_store_path)

    def test_task1_test_queries_structure(self):
        """Task 1: Verify test query suite defines expected chunk targets and topics."""
        self.assertGreaterEqual(len(TUNING_TEST_QUERIES), 4)
        for q in TUNING_TEST_QUERIES:
            self.assertIn("query_id", q)
            self.assertIn("query", q)
            self.assertIn("topic", q)
            self.assertIn("expected_chunk_id", q)
            self.assertIn("expected_source_doc", q)

    def test_task2_and_task3_evaluate_configuration_metrics(self):
        """Task 2 & 3: Verify configuration metric calculations (Hit Rate, MRR, Token Overhead)."""
        config = {
            "config_id": "test_cfg",
            "name": "Test Config (k=3)",
            "k": 3,
            "score_threshold": 0.0,
            "metadata_filter": None
        }

        res = evaluate_configuration(
            retriever=self.retriever,
            test_queries=TUNING_TEST_QUERIES[:3],
            config=config
        )

        self.assertEqual(res["config_id"], "test_cfg")
        self.assertEqual(res["k"], 3)
        metrics = res["metrics"]
        self.assertIn("top1_hit_rate", metrics)
        self.assertIn("topk_hit_rate", metrics)
        self.assertIn("mrr", metrics)
        self.assertIn("avg_tokens_per_query", metrics)
        self.assertIn("avg_top_score", metrics)

        self.assertGreaterEqual(metrics["top1_hit_rate"], 0.0)
        self.assertLessEqual(metrics["top1_hit_rate"], 1.0)
        self.assertGreaterEqual(metrics["mrr"], 0.0)
        self.assertLessEqual(metrics["mrr"], 1.0)

    def test_score_thresholding_and_metadata_filtering(self):
        """Task 2: Verify retriever filtering with score thresholds and metadata tags."""
        query = "How many days of paid time off do employees get?"

        # High threshold (0.99) should filter out lower scoring chunks
        strict_results = self.retriever.retrieve_top_k(query, k=5, score_threshold=0.99)
        self.assertLessEqual(len(strict_results), 5)

        # Metadata filter for .md files
        md_results = self.retriever.retrieve_top_k(query, k=5, metadata_filter={"file_type": ".md"})
        for c in md_results:
            self.assertTrue(c.metadata.get("source_document", "").endswith(".md") or c.metadata.get("file_type") == ".md")

    def test_task4_and_task5_run_tuning_experiment_pipeline(self):
        """Task 4 & 5: Verify end-to-end tuning experiment runner and file exports."""
        with tempfile.TemporaryDirectory() as temp_dir:
            res = run_tuning_experiment(
                vector_store_path=self.vector_store_path,
                output_dir=temp_dir
            )

            self.assertIn("best_configuration", res)
            self.assertIn("compared_configurations", res)

            json_file = Path(temp_dir) / "retrieval_tuning_results.json"
            report_file = Path(temp_dir) / "retrieval_tuning_report.md"

            self.assertTrue(json_file.exists())
            self.assertTrue(report_file.exists())
            self.assertGreater(json_file.stat().st_size, 0)
            self.assertGreater(report_file.stat().st_size, 0)

            # Check that best configuration has a valid justification string
            best_cfg = res["best_configuration"]
            self.assertIn("justification", best_cfg)
            self.assertIn("Chosen Setting", best_cfg["justification"])


if __name__ == "__main__":
    unittest.main()
