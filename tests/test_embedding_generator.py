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
        vectors, model_info = generate_embeddings(texts, dimension=expected_dim)

        self.assertEqual(len(vectors), len(texts))
        for vec in vectors:
            self.assertEqual(len(vec), expected_dim)
            self.assertIsInstance(vec, list)
            self.assertTrue(all(isinstance(x, float) for x in vec))

    def test_task2_store_vectors_with_metadata(self):
        """Task 2: Verify storing each vector paired with source text and metadata."""
        out_json = self.temp_path / "embedded_chunks.json"
        out_report = self.temp_path / "embedding_report.md"

        summary = process_corpus_embeddings(
            input_chunks_path=str(self.input_chunks_file),
            output_json_path=str(out_json),
            output_report_path=str(out_report),
            dimension=1536
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

        # Check metadata fields for chunk 2
        item2 = items[1]
        self.assertEqual(item2["chunk_id"], "test_chunk_002")
        meta2 = item2["metadata"]
        self.assertEqual(meta2["source_document"], "it_security_policy.md")
        self.assertEqual(meta2["chunk_index"], 2)
        self.assertEqual(meta2["section"], "2. VPN & Encryption Protocols")
        self.assertEqual(meta2["page"], 1)

    def test_task4_verification_trimmed_vector_values(self):
        """Task 4: Verify vector length and trimmed vector values are recorded."""
        out_json = self.temp_path / "embedded_chunks.json"
        out_report = self.temp_path / "embedding_report.md"

        process_corpus_embeddings(
            input_chunks_path=str(self.input_chunks_file),
            output_json_path=str(out_json),
            output_report_path=str(out_report),
            dimension=1536
        )

        with open(out_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        item = data["embedded_chunks"][0]
        trimmed = item["trimmed_vector"]
        self.assertIn("first_5", trimmed)
        self.assertIn("last_5", trimmed)
        self.assertEqual(len(trimmed["first_5"]), 5)
        self.assertEqual(len(trimmed["last_5"]), 5)
        self.assertIn("preview_str", trimmed)

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
