"""
Unit Tests for Document Chunking Strategies Module (src/chunker.py).
"""

import unittest
from pathlib import Path

from src.chunker import (
    FixedSizeChunker,
    SentenceChunker,
    ParagraphStructureChunker,
    count_tokens,
    calculate_strategy_stats,
    run_chunking_benchmark,
    get_default_tokenizer,
)


class TestChunkingStrategies(unittest.TestCase):
    def setUp(self):
        self.tokenizer = get_default_tokenizer()
        self.sample_text = (
            "# Policy Title\n\n"
            "## 1. Eligibility\n"
            "Employees are eligible after 6 months. Performance must be satisfactory.\n"
            "Remote work is approved annually.\n\n"
            "## 2. IT Requirements\n"
            "Company laptops must use VPN. Security updates are mandatory.\n"
            "Do not connect to public unencrypted Wi-Fi networks."
        )

    def test_token_counter(self):
        tokens = count_tokens("Hello world! This is a test.")
        self.assertGreater(tokens, 0)
        self.assertEqual(count_tokens(""), 0)

    def test_fixed_size_chunker_chars(self):
        chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=20, unit="char", snap_to_words=True)
        chunks = chunker.chunk(self.sample_text, doc_id="test_doc")

        self.assertGreater(len(chunks), 1)
        for c in chunks:
            self.assertEqual(c.doc_id, "test_doc")
            self.assertEqual(c.strategy, "Fixed-Size (Chars)")
            self.assertLessEqual(c.char_count, 120)  # within margin of snapping
            self.assertGreater(c.token_count, 0)
            self.assertIn("chunk_index", c.metadata)

    def test_fixed_size_chunker_tokens(self):
        chunker = FixedSizeChunker(chunk_size=30, chunk_overlap=10, unit="token")
        chunks = chunker.chunk(self.sample_text, doc_id="test_doc")

        self.assertGreater(len(chunks), 1)
        for c in chunks:
            self.assertEqual(c.doc_id, "test_doc")
            self.assertEqual(c.strategy, "Fixed-Size (Tokens)")
            self.assertLessEqual(c.token_count, 35)

    def test_fixed_size_invalid_overlap(self):
        with self.assertRaises(ValueError):
            FixedSizeChunker(chunk_size=100, chunk_overlap=100)

    def test_sentence_chunker(self):
        chunker = SentenceChunker(max_tokens=25, sentence_overlap=1)
        chunks = chunker.chunk(self.sample_text, doc_id="test_doc")

        self.assertGreater(len(chunks), 1)
        for c in chunks:
            self.assertEqual(c.doc_id, "test_doc")
            self.assertEqual(c.strategy, "Sentence-Based")
            self.assertGreater(c.token_count, 0)
            self.assertIn("sentence_count", c.metadata)

    def test_paragraph_structure_chunker(self):
        chunker = ParagraphStructureChunker(max_chunk_tokens=150, include_header_context=True)
        chunks = chunker.chunk(self.sample_text, doc_id="test_doc")

        self.assertGreaterEqual(len(chunks), 2)
        # Verify header breadcrumb injection
        self.assertTrue(any("Eligibility" in c.content for c in chunks))
        self.assertTrue(any("IT Requirements" in c.content for c in chunks))
        for c in chunks:
            self.assertEqual(c.doc_id, "test_doc")
            self.assertEqual(c.strategy, "Paragraph / Structure-Aware")
            self.assertIn("section_header", c.metadata)

    def test_empty_string_handling(self):
        for chunker in [
            FixedSizeChunker(),
            SentenceChunker(),
            ParagraphStructureChunker(),
        ]:
            chunks = chunker.chunk("", doc_id="empty_doc")
            self.assertEqual(chunks, [])

    def test_calculate_strategy_stats(self):
        chunker = ParagraphStructureChunker()
        chunks = chunker.chunk(self.sample_text, doc_id="test_doc")
        stats = calculate_strategy_stats("test_doc", self.sample_text, chunks, "Paragraph / Structure-Aware")

        self.assertEqual(stats.document_id, "test_doc")
        self.assertEqual(stats.chunk_count, len(chunks))
        self.assertGreater(stats.avg_tokens_per_chunk, 0)
        self.assertGreater(stats.avg_chars_per_chunk, 0)
        self.assertGreaterEqual(stats.min_tokens, 0)
        self.assertGreaterEqual(stats.max_tokens, stats.min_tokens)
        self.assertIsInstance(stats.to_dict(), dict)

    def test_run_chunking_benchmark_pipeline(self):
        benchmark_results = run_chunking_benchmark()
        self.assertIn("stats", benchmark_results)
        self.assertIn("aggregates", benchmark_results)
        self.assertIn("paths", benchmark_results)
        self.assertEqual(benchmark_results["chosen_strategy"], "Paragraph / Structure-Aware")

        # Verify output files exist
        for key, file_path in benchmark_results["paths"].items():
            path_obj = Path(file_path)
            self.assertTrue(path_obj.exists(), f"File {file_path} should exist")
            self.assertGreater(path_obj.stat().st_size, 0, f"File {file_path} should not be empty")


if __name__ == "__main__":
    unittest.main()
