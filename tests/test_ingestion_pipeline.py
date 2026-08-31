"""
Unit & Integration Tests for Full Corpus Ingestion Pipeline & Completeness Validation.
"""

import json
import tempfile
import unittest
from pathlib import Path

from src.ingestion_pipeline import (
    run_ingestion_pipeline,
    save_ingestion_artifacts,
    process_md_file,
    process_html_file,
    process_txt_file,
    process_pdf_file,
    clean_text_whitespace,
    count_tokens,
    IngestedChunk,
)


class TestIngestionPipeline(unittest.TestCase):
    def setUp(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.corpus_dir = self.base_dir / "data" / "corpus"

    def test_clean_text_whitespace(self):
        dirty = "  Hello   world!  \r\n\r\n\n\nThis   is  a\ttest.   "
        cleaned = clean_text_whitespace(dirty)
        self.assertEqual(cleaned, "Hello world!\n\nThis is a test.")

    def test_token_counter(self):
        text = "Retrieval-Augmented Generation (RAG) system test."
        toks = count_tokens(text)
        self.assertGreater(toks, 0)

    def test_process_md_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# Title\n\n## Section 1\nContent of section 1.\n\n## Section 2\nContent of section 2.")
            temp_path = Path(f.name)

        try:
            chunks, total_chars, total_tokens = process_md_file(temp_path, "temp.md")
            self.assertEqual(len(chunks), 2)
            self.assertTrue(all(isinstance(c, IngestedChunk) for c in chunks))
            self.assertEqual(chunks[0].section, "Title > Section 1")
            self.assertEqual(chunks[1].section, "Title > Section 2")
            self.assertGreater(total_tokens, 0)
        finally:
            temp_path.unlink()

    def test_process_html_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
            f.write("<html><body><h1>Portal</h1><p>Main paragraph content.</p><script>alert(1)</script></body></html>")
            temp_path = Path(f.name)

        try:
            chunks, total_chars, total_tokens = process_html_file(temp_path, "portal.html")
            self.assertGreaterEqual(len(chunks), 1)
            # Ensure script was stripped
            self.assertNotIn("alert", chunks[0].text)
            self.assertIn("Main paragraph content.", chunks[0].text)
        finally:
            temp_path.unlink()

    def test_process_txt_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("First paragraph.\n\nSecond paragraph.")
            temp_path = Path(f.name)

        try:
            chunks, total_chars, total_tokens = process_txt_file(temp_path, "test.txt")
            self.assertEqual(len(chunks), 2)
            self.assertEqual(chunks[0].text, "First paragraph.")
            self.assertEqual(chunks[1].text, "Second paragraph.")
        finally:
            temp_path.unlink()

    def test_full_ingestion_pipeline_and_reconciliation(self):
        summary, chunks = run_ingestion_pipeline(self.corpus_dir)

        # Task 1: Complete pipeline run
        self.assertGreater(summary.total_source_documents, 0)
        self.assertGreater(summary.successfully_ingested, 0)
        self.assertGreater(len(chunks), 0)

        # Task 2: Ingestion summary verification
        self.assertIsInstance(summary.file_type_breakdown, dict)
        self.assertGreaterEqual(summary.failed_documents, 1)  # corrupt.pdf caught
        self.assertEqual(len(summary.failures), summary.failed_documents)

        # Task 3: Mathematical Completeness Validation
        self.assertTrue(summary.reconciliation_valid)
        self.assertEqual(
            summary.total_source_documents,
            summary.successfully_ingested + summary.failed_documents + summary.skipped_documents,
        )

        # Task 4: Chunk tags & structure verification
        for c in chunks:
            self.assertTrue(c.chunk_id)
            self.assertTrue(c.source)
            self.assertTrue(c.file_type)
            self.assertTrue(c.cleaned)
            self.assertGreater(c.char_count, 0)
            self.assertGreater(c.token_count, 0)
            self.assertIsNotNone(c.position)

    def test_save_artifacts_and_files(self):
        with tempfile.TemporaryDirectory() as temp_out:
            out_dir = Path(temp_out)
            summary, chunks = run_ingestion_pipeline(self.corpus_dir)
            artifacts = save_ingestion_artifacts(summary, chunks, out_dir)

            self.assertTrue(Path(artifacts["summary_json"]).exists())
            self.assertTrue(Path(artifacts["chunks_json"]).exists())
            self.assertTrue(Path(artifacts["report_md"]).exists())

            # Validate summary JSON
            with open(artifacts["summary_json"], "r", encoding="utf-8") as f:
                data = json.load(f)
                self.assertEqual(data["reconciliation_valid"], True)
                self.assertEqual(data["total_source_documents"], summary.total_source_documents)


if __name__ == "__main__":
    unittest.main()
