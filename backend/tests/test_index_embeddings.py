"""
Unit Tests for Vector Database Collection Indexing & Integrity Storage (src/index_embeddings.py).
"""

import os
import json
import tempfile
import unittest
from pathlib import Path

from src.index_embeddings import (
    VectorDatabaseCollection,
    process_vector_indexing
)


class TestVectorIndexer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        # Sample embedded chunks for testing
        self.sample_embedded_chunks = [
            {
                "chunk_id": "test_chunk_001",
                "source_text": "Full-time regular employees accrue 18 days of Paid Time Off annually.",
                "metadata": {
                    "source_document": "employee_benefits.md",
                    "source_path": "data/corpus/employee_benefits.md",
                    "chunk_index": 1,
                    "section": "1. Paid Time Off (PTO) Accrual",
                    "page": None,
                    "file_type": ".md",
                    "token_count": 14,
                    "char_count": 70
                },
                "vector_length": 1536,
                "trimmed_vector": {
                    "first_5": [0.1, 0.2, 0.3, 0.4, 0.5],
                    "last_5": [0.5, 0.4, 0.3, 0.2, 0.1],
                    "preview_str": "[+0.1000, +0.2000, +0.3000, ... , +0.3000, +0.2000, +0.1000]"
                },
                "vector": [0.01] * 1536
            },
            {
                "chunk_id": "test_chunk_002",
                "source_text": "All remote connections must use corporate-issued VPN with AES-256 encryption.",
                "metadata": {
                    "source_document": "it_security_policy.md",
                    "source_path": "data/corpus/it_security_policy.md",
                    "chunk_index": 2,
                    "section": "2. VPN & Encryption Protocols",
                    "page": 1,
                    "file_type": ".md",
                    "token_count": 12,
                    "char_count": 78
                },
                "vector_length": 1536,
                "trimmed_vector": {
                    "first_5": [0.0, 0.0, 0.0, 0.0, 0.0],
                    "last_5": [0.0, 0.0, 0.0, 0.0, 0.0],
                    "preview_str": "[+0.0000, +0.0000, +0.0000, ... , +0.0000, +0.0000, +0.0000]"
                },
                "vector": [0.02] * 1536
            }
        ]

        self.input_file = self.temp_path / "embedded_chunks.json"
        with open(self.input_file, "w", encoding="utf-8") as f:
            json.dump({
                "summary": {"total_chunks_embedded": 2},
                "embedded_chunks": self.sample_embedded_chunks
            }, f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_task1_and_task2_bulk_insert_record_storage(self):
        """Tasks 1 & 2: Verify bulk inserting embedded records stores vector, source text, and metadata."""
        collection = VectorDatabaseCollection(collection_name="test_coll", dimension=1536)
        inserted, total = collection.bulk_insert(self.sample_embedded_chunks)

        self.assertEqual(inserted, 2)
        self.assertEqual(total, 2)
        self.assertEqual(collection.count(), 2)

        rec1 = collection.get("test_chunk_001")
        self.assertIsNotNone(rec1)
        self.assertEqual(rec1["chunk_id"], "test_chunk_001")
        self.assertIn("Full-time regular employees accrue", rec1["source_text"])
        self.assertEqual(rec1["metadata"]["source_document"], "employee_benefits.md")
        self.assertEqual(rec1["metadata"]["chunk_index"], 1)
        self.assertEqual(rec1["metadata"]["section"], "1. Paid Time Off (PTO) Accrual")
        self.assertIsNone(rec1["metadata"]["page"])
        self.assertEqual(rec1["vector_length"], 1536)
        self.assertEqual(len(rec1["vector"]), 1536)

    def test_task3_confirm_indexed_count(self):
        """Task 3: Verify count matching logic."""
        collection = VectorDatabaseCollection(collection_name="test_coll", dimension=1536)
        collection.bulk_insert(self.sample_embedded_chunks)
        self.assertEqual(collection.count(), len(self.sample_embedded_chunks))

    def test_task4_spot_check_stored_integrity(self):
        """Task 4: Verify spot check reads back record and confirms 100% field integrity."""
        collection = VectorDatabaseCollection(collection_name="test_coll", dimension=1536)
        collection.bulk_insert(self.sample_embedded_chunks)

        spot_checks = collection.spot_check_integrity(self.sample_embedded_chunks)
        self.assertEqual(len(spot_checks), 2)
        for sc in spot_checks:
            self.assertEqual(sc["status"], "PASSED")
            self.assertTrue(sc["id_matched"])
            self.assertTrue(sc["text_matched"])
            self.assertTrue(sc["metadata_matched"])
            self.assertTrue(sc["vector_len_matched"])

    def test_persistence_save_and_load_disk(self):
        """Verify saving collection index to disk and reloading it."""
        collection = VectorDatabaseCollection(collection_name="test_coll", dimension=1536)
        collection.bulk_insert(self.sample_embedded_chunks)

        out_coll_file = self.temp_path / "indexed_coll.json"
        collection.save_to_disk(str(out_coll_file))

        loaded_coll = VectorDatabaseCollection()
        loaded_coll.load_from_disk(str(out_coll_file))

        self.assertEqual(loaded_coll.count(), 2)
        self.assertEqual(loaded_coll.collection_name, "test_coll")
        self.assertIsNotNone(loaded_coll.get("test_chunk_001"))

    def test_task5_process_vector_indexing_pipeline(self):
        """Task 5: Verify end-to-end vector indexing process and report generation."""
        out_coll = self.temp_path / "indexed_collection.json"
        out_summary = self.temp_path / "vector_indexing_results.json"
        out_report = self.temp_path / "vector_indexing_report.md"

        summary = process_vector_indexing(
            input_embedded_path=str(self.input_file),
            collection_output_path=str(out_coll),
            summary_json_path=str(out_summary),
            report_md_path=str(out_report),
            collection_name="corpus_chunks_v1",
            dimension=1536
        )

        self.assertTrue(summary["count_validation"]["count_matched"])
        self.assertTrue(summary["spot_check_summary"]["all_passed"])
        self.assertTrue(out_coll.exists())
        self.assertTrue(out_summary.exists())
        self.assertTrue(out_report.exists())


if __name__ == "__main__":
    unittest.main()
