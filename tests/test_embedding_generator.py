"""
Unit Tests for Corpus Embedding Generation & Retrieval Metadata Storage (src/generate_embeddings.py).
"""

import os
import json
import tempfile
import unittest
from pathlib import Path

from src.generate_embeddings import (
    load_environment_config,
    generate_embeddings,
    process_corpus_embeddings,
    DenseSemanticEmbedder
)


class TestEmbeddingGenerator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        # Sample prepared text chunks for testing
        self.sample_chunks = [
            {
                "chunk_id": "test_chunk_001",
                "source": "data/corpus/employee_benefits.md",
                "document_name": "employee_benefits.md",
                "file_type": ".md",
                "section": "1. Paid Time Off (PTO) Accrual",
                "page": None,
                "position": 1,
                "text": "Full-time regular employees accrue 18 days of Paid Time Off annually at 1.5 days per month.",
                "char_count": 91,
                "token_count": 22
            },
            {
                "chunk_id": "test_chunk_002",
                "source": "data/corpus/it_security_policy.md",
                "document_name": "it_security_policy.md",
                "file_type": ".md",
                "section": "2. VPN & Encryption Protocols",
                "page": 1,
                "position": 2,
                "text": "All remote connections must use corporate-issued VPN with AES-256 encryption.",
                "char_count": 78,
                "token_count": 18
            }
        ]

        self.input_chunks_file = self.temp_path / "test_chunks.json"
        with open(self.input_chunks_file, "w", encoding="utf-8") as f:
            json.dump(self.sample_chunks, f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_task3_load_environment_config(self):
        """Task 3: Verify environment configuration loading without hardcoded secrets."""
        config = load_environment_config()
        self.assertIn("api_key", config)
        self.assertIn("base_url", config)
        self.assertIn("model", config)

    def test_task1_generate_embeddings_dimension(self):
        """Task 1: Verify passing prepared text chunks returns vectors of expected dimension."""
        texts = [c["text"] for c in self.sample_chunks]
        expected_dim = 1536
        vectors, model_info, metrics = generate_embeddings(texts, dimension=expected_dim, initial_retry_delay=0.01)

        self.assertEqual(len(vectors), len(texts))
        for vec in vectors:
            self.assertEqual(len(vec), expected_dim)
            self.assertIsInstance(vec, list)
            self.assertTrue(all(isinstance(x, float) for x in vec))
        self.assertIn("total_batches", metrics)

    def test_batch_processing_and_metrics(self):
        """Task 1: Verify batch processing divides input into correct batch sizes."""
        texts = [c["text"] for c in self.sample_chunks]
        # Batch size 1 -> 2 batches
        vectors_b1, _, metrics_b1 = generate_embeddings(texts, batch_size=1, initial_retry_delay=0.01)
        self.assertEqual(metrics_b1["total_batches"], 2)
        self.assertEqual(len(vectors_b1), 2)

        # Batch size 10 -> 1 batch
        vectors_b10, _, metrics_b10 = generate_embeddings(texts, batch_size=10, initial_retry_delay=0.01)
        self.assertEqual(metrics_b10["total_batches"], 1)
        self.assertEqual(len(vectors_b10), 2)

    def test_task2_store_vectors_with_metadata(self):
        """Task 2: Verify storing each vector paired with source text and metadata."""
        out_json = self.temp_path / "embedded_chunks.json"
        out_report = self.temp_path / "embedding_report.md"

        summary = process_corpus_embeddings(
            input_chunks_path=str(self.input_chunks_file),
            output_json_path=str(out_json),
            output_report_path=str(out_report),
            dimension=1536,
            batch_size=1,
            initial_retry_delay=0.01
        )

        self.assertEqual(summary["total_chunks_embedded"], 2)
        self.assertEqual(summary["vector_dimension"], 1536)
        self.assertTrue(summary["uniform_dimension_confirmed"])

        # Inspect saved JSON structure
        with open(out_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("summary", data)
        self.assertIn("embedded_chunks", data)
        items = data["embedded_chunks"]
        self.assertEqual(len(items), 2)

        # Check metadata fields for chunk 1
        item1 = items[0]
        self.assertEqual(item1["chunk_id"], "test_chunk_001")
        self.assertIn("Full-time regular employees accrue", item1["source_text"])
        meta1 = item1["metadata"]
        self.assertEqual(meta1["source_document"], "employee_benefits.md")
        self.assertEqual(meta1["chunk_index"], 1)
        self.assertEqual(meta1["section"], "1. Paid Time Off (PTO) Accrual")
        self.assertIsNone(meta1["page"])
        self.assertEqual(item1["vector_length"], 1536)
        self.assertEqual(len(item1["vector"]), 1536)

    def test_task4_skip_already_embedded_chunks(self):
        """Task 4: Verify on re-runs already-embedded chunks are detected and skipped."""
        out_json = self.temp_path / "embedded_chunks.json"
        out_report = self.temp_path / "embedding_report.md"

        # First run: embeds 2 chunks, 0 skipped
        summary_run1 = process_corpus_embeddings(
            input_chunks_path=str(self.input_chunks_file),
            output_json_path=str(out_json),
            output_report_path=str(out_report),
            dimension=1536,
            initial_retry_delay=0.01
        )
        rm1 = summary_run1["run_metrics"]
        self.assertEqual(rm1["chunks_embedded_this_run"], 2)
        self.assertEqual(rm1["skipped_chunks_already_embedded"], 0)

        # Second run: 0 chunks embedded, 2 skipped
        summary_run2 = process_corpus_embeddings(
            input_chunks_path=str(self.input_chunks_file),
            output_json_path=str(out_json),
            output_report_path=str(out_report),
            dimension=1536,
            initial_retry_delay=0.01
        )
        rm2 = summary_run2["run_metrics"]
        self.assertEqual(rm2["chunks_embedded_this_run"], 0)
        self.assertEqual(rm2["skipped_chunks_already_embedded"], 2)
        self.assertEqual(rm2["run_cost_usd"], 0.0)

        # Third run with force=True: 2 chunks embedded, 0 skipped
        summary_run3 = process_corpus_embeddings(
            input_chunks_path=str(self.input_chunks_file),
            output_json_path=str(out_json),
            output_report_path=str(out_report),
            dimension=1536,
            force=True,
            initial_retry_delay=0.01
        )
        rm3 = summary_run3["run_metrics"]
        self.assertEqual(rm3["chunks_embedded_this_run"], 2)
        self.assertEqual(rm3["skipped_chunks_already_embedded"], 0)

    def test_task3_cost_calculation_and_reporting(self):
        """Task 3: Verify token usage and approximate cost estimation."""
        out_json = self.temp_path / "embedded_chunks.json"
        out_report = self.temp_path / "embedding_report.md"

        summary = process_corpus_embeddings(
            input_chunks_path=str(self.input_chunks_file),
            output_json_path=str(out_json),
            output_report_path=str(out_report),
            cost_per_1k_tokens=0.0001,
            initial_retry_delay=0.01
        )
        rm = summary["run_metrics"]
        expected_tokens = 22 + 18  # 40 tokens total
        self.assertEqual(rm["tokens_embedded_this_run"], expected_tokens)
        expected_cost = (40 / 1000.0) * 0.0001  # 0.000004
        self.assertAlmostEqual(rm["run_cost_usd"], expected_cost, places=6)

    def test_fallback_dense_embedder(self):
        """Verify DenseSemanticEmbedder generates normalized vectors of target dimension."""
        embedder = DenseSemanticEmbedder(dimension=1536)
        vec = embedder.embed("Sample text for embedding test")
        self.assertEqual(len(vec), 1536)
        
        # Verify L2 norm is approximately 1.0
        norm = sum(x * x for x in vec) ** 0.5
        self.assertAlmostEqual(norm, 1.0, places=4)


if __name__ == "__main__":
    unittest.main()
