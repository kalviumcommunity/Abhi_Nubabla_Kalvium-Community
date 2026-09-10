"""
Unit tests for Verifiable Source Citations and Metadata Attribution Engine.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.similarity_search import RetrievedChunk
from src.citation_engine import (
    build_citation_map,
    build_cited_context,
    extract_citations_from_text,
    verify_cited_answer,
    generate_cited_answer,
    run_citation_pipeline
)


class TestCitationEngine(unittest.TestCase):

    def setUp(self):
        self.sample_chunks = [
            RetrievedChunk(
                chunk_id="chunk_hr_001",
                score=0.8850,
                rank=1,
                source_text="Employees receive 15 days of paid time off (PTO) annually. Unused PTO can be rolled over up to 5 days into the next year.",
                metadata={
                    "source_document": "hr_remote_policy_raw.txt",
                    "chunk_index": 0,
                    "section": "Paid Time Off & Leave",
                    "page": 1,
                    "token_count": 25
                }
            ),
            RetrievedChunk(
                chunk_id="chunk_sec_002",
                score=0.7920,
                rank=2,
                source_text="Remote workers must use WPA3 enterprise WiFi and connect via the corporate WireGuard VPN tunnel.",
                metadata={
                    "source_document": "security_guidelines.txt",
                    "chunk_index": 1,
                    "section": "Remote Security & Encryption",
                    "page": 2,
                    "token_count": 20
                }
            )
        ]

    def test_extract_citations_from_text(self):
        """Task 1: Test extraction of bracketed inline citations from text."""
        text = "According to policy [1], employees get 15 days PTO. Security requires VPN [2]."
        citations = extract_citations_from_text(text)
        self.assertEqual(citations, ["[1]", "[2]"])

        # Test deduplication & ordering
        text2 = "Claim one [1]. Claim two [2]. Repeated claim [1]."
        self.assertEqual(extract_citations_from_text(text2), ["[1]", "[2]"])

        # Empty text
        self.assertEqual(extract_citations_from_text("No citations here."), [])

    def test_citation_metadata_mapping(self):
        """Task 2: Test mapping citations to metadata (chunk_id, doc, section, page, score)."""
        citation_map = build_citation_map(self.sample_chunks)
        
        self.assertIn("[1]", citation_map)
        self.assertIn("[2]", citation_map)
        
        meta1 = citation_map["[1]"]
        self.assertEqual(meta1["chunk_id"], "chunk_hr_001")
        self.assertEqual(meta1["source_document"], "hr_remote_policy_raw.txt")
        self.assertEqual(meta1["chunk_index"], 0)
        self.assertEqual(meta1["section"], "Paid Time Off & Leave")
        self.assertEqual(meta1["page"], 1)
        self.assertEqual(meta1["similarity_score"], 0.8850)
        self.assertIn("15 days of paid time off", meta1["source_text_snippet"])

    def test_verify_cited_sources_valid(self):
        """Task 3: Test verification of valid cited sources."""
        citation_map = build_citation_map(self.sample_chunks)
        answer = "Employees receive 15 days of paid time off annually [1]. Remote workers must use WireGuard VPN [2]."

        res = verify_cited_answer(answer, citation_map, self.sample_chunks)
        self.assertTrue(res["is_verified"])
        self.assertEqual(res["citations_used"], ["[1]", "[2]"])
        self.assertEqual(res["valid_citations_count"], 2)
        self.assertEqual(len(res["invalid_citations"]), 0)

    def test_verify_cited_sources_invalid_hallucinated_tag(self):
        """Task 3: Test detection of invalid/hallucinated citation tags."""
        citation_map = build_citation_map(self.sample_chunks)
        answer = "Employees get 15 days PTO [1], but extra bonus days apply [99]."

        res = verify_cited_answer(answer, citation_map, self.sample_chunks)
        self.assertFalse(res["is_verified"])
        self.assertIn("[99]", res["invalid_citations"])

    def test_avoid_fabricated_citations_fallback(self):
        """Task 4: Test fallback safeguard when no sources or low-confidence sources exist."""
        # Scenario A: Empty chunks
        res = generate_cited_answer("What is the Mars policy?", [], score_threshold=0.35)
        self.assertTrue(res["is_fallback"])
        self.assertEqual(res["citations_found"], [])
        self.assertEqual(res["citation_map"], {})
        self.assertIn("I don't have access to sufficient verified", res["answer"])
        self.assertTrue(res["verification_status"]["is_verified"])

        # Scenario B: Chunks below score threshold
        low_score_chunks = [
            RetrievedChunk(
                chunk_id="chunk_low_001",
                score=0.1500,
                rank=1,
                source_text="Unrelated text snippet.",
                metadata={"source_document": "doc.txt"}
            )
        ]
        res_low = generate_cited_answer("What is the Mars policy?", low_score_chunks, score_threshold=0.35)
        self.assertTrue(res_low["is_fallback"])
        self.assertEqual(res_low["citations_found"], [])
        self.assertEqual(res_low["citation_map"], {})

    def test_end_to_end_citation_pipeline(self):
        """Task 5: Test end-to-end citation pipeline execution."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve_top_k.return_value = self.sample_chunks

        res = run_citation_pipeline(
            query="How many PTO days do employees get?",
            k=2,
            retriever=mock_retriever
        )

        self.assertIn("answer", res)
        self.assertIn("citation_map", res)
        self.assertIn("verification_status", res)
        self.assertIn("[1]", res["citation_map"])
        self.assertTrue(res["verification_status"]["is_verified"])


if __name__ == "__main__":
    unittest.main()
