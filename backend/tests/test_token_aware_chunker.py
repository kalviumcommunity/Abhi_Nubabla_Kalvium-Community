"""
Unit Tests for Token-Aware Chunker with Controlled Overlap (src/token_aware_chunker.py).
"""

import unittest
from pathlib import Path
from src.token_aware_chunker import (
    TokenAwareChunker,
    demonstrate_boundary_preservation,
    get_parameter_justification,
    run_corpus_token_chunking,
    get_tokenizer,
)


class TestTokenAwareChunker(unittest.TestCase):
    def setUp(self):
        self.tokenizer = get_tokenizer("gpt-4o")
        self.sample_text = (
            "# Remote Work & IT Security Protocol\n\n"
            "## 1. Overview\n"
            "This policy outlines requirements for working outside corporate headquarters. "
            "All personnel operating remotely must comply with security guidelines without exception.\n\n"
            "## 2. Technical Equipment & VPN Requirements\n"
            "Employees must connect using corporate-issued laptops equipped with endpoint detection software. "
            "Connecting to unencrypted public Wi-Fi networks is strictly prohibited under company regulations. "
            "All connections must tunnel through the corporate AES-256 encrypted VPN.\n\n"
            "## 3. Data Confidentiality & Document Handling\n"
            "Confidential physical documents must not be printed at home workstations. "
            "Digital records must be stored exclusively in designated encrypted cloud storage repositories. "
            "Workstations must be locked immediately when stepping away from the desk."
        )

    def test_task1_token_sizing(self):
        """Verify chunks are sized strictly by token count, not character count."""
        chunk_size = 40
        overlap = 10
        chunker = TokenAwareChunker(chunk_size_tokens=chunk_size, chunk_overlap_tokens=overlap)
        chunks = chunker.chunk(self.sample_text, doc_id="test_token_size")

        self.assertGreater(len(chunks), 1)
        for c in chunks:
            self.assertLessEqual(c.token_count, chunk_size)
            self.assertGreater(c.token_count, 0)
            self.assertEqual(c.doc_id, "test_token_size")

    def test_task2_controlled_overlap(self):
        """Verify adjacent chunks repeat the last N tokens of the preceding chunk."""
        chunk_size = 50
        overlap = 15
        chunker = TokenAwareChunker(chunk_size_tokens=chunk_size, chunk_overlap_tokens=overlap)
        chunks = chunker.chunk(self.sample_text, doc_id="test_overlap")

        self.assertGreater(len(chunks), 1)
        c1_tokens = self.tokenizer.encode(chunks[0].content)
        c2_tokens = self.tokenizer.encode(chunks[1].content)

        # The last `overlap` tokens of chunk 1 must match the first `overlap` tokens of chunk 2
        tail_c1 = c1_tokens[-overlap:]
        head_c2 = c2_tokens[:overlap]
        self.assertEqual(tail_c1, head_c2)

        # Check metadata overlap reporting
        self.assertEqual(chunks[0].metadata["overlap_tokens_from_prev"], 0)
        self.assertEqual(chunks[1].metadata["overlap_tokens_from_prev"], overlap)

    def test_invalid_parameters_raise_error(self):
        """Verify invalid size/overlap values raise ValueError."""
        with self.assertRaises(ValueError):
            TokenAwareChunker(chunk_size_tokens=0, chunk_overlap_tokens=10)
        with self.assertRaises(ValueError):
            TokenAwareChunker(chunk_size_tokens=50, chunk_overlap_tokens=50)
        with self.assertRaises(ValueError):
            TokenAwareChunker(chunk_size_tokens=50, chunk_overlap_tokens=60)
        with self.assertRaises(ValueError):
            TokenAwareChunker(chunk_size_tokens=50, chunk_overlap_tokens=-5)

    def test_empty_string_returns_empty_list(self):
        """Verify empty input string returns empty chunk list."""
        chunker = TokenAwareChunker()
        self.assertEqual(chunker.chunk(""), [])
        self.assertEqual(chunker.chunk("   "), [])

    def test_task3_boundary_preservation_demonstration(self):
        """Verify boundary context preservation comparison logic."""
        demo_results = demonstrate_boundary_preservation(self.sample_text, doc_id="test_demo", chunk_size=40, overlap=10)
        self.assertIn("boundary_idea_comparison", demo_results)
        comp = demo_results["boundary_idea_comparison"]
        self.assertIn("without_overlap", comp)
        self.assertIn("with_overlap", comp)
        self.assertIn("repeated_overlap_context", comp["with_overlap"])

    def test_task4_parameter_justification(self):
        """Verify parameter justification output structure."""
        justification = get_parameter_justification(chunk_size=200, chunk_overlap=40)
        self.assertEqual(justification["chosen_chunk_size_tokens"], 200)
        self.assertEqual(justification["chosen_overlap_tokens"], 40)
        self.assertIn("justifications", justification)

    def test_task5_corpus_chunking_pipeline(self):
        """Verify corpus execution and export of JSON & Markdown artifacts."""
        results = run_corpus_token_chunking()
        self.assertTrue(Path(results["json_path"]).exists())
        self.assertTrue(Path(results["report_path"]).exists())
        self.assertGreater(Path(results["json_path"]).stat().st_size, 0)
        self.assertGreater(Path(results["report_path"]).stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
