"""
Unit Tests for Grounded Answer Generation & Source Accuracy Verification Engine.
Tests generation from retrieved context, source accuracy auditing, missing-context fallbacks,
with/without retrieval comparisons, and report generation.
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.grounded_generator import (
    STANDARD_FALLBACK_ANSWER,
    GroundedAnswerGenerator,
    GroundedGenerationResult,
    SourceAccuracyChecker,
    SourceAccuracyAudit,
    RetrievalComparisonResult,
    generate_grounded_generation_report,
    run_grounded_generation_benchmark,
)
from src.similarity_search import RetrievedChunk


class TestSourceAccuracyChecker(unittest.TestCase):
    """Unit tests for claim extraction and source accuracy / faithfulness auditing."""

    def test_extract_claims(self):
        """Test extraction of factual statements from structured answer text."""
        text = (
            "Based on verified internal guidelines in employee_benefits.md: "
            "Full-time regular employees accrue 18 days of Paid Time Off annually. "
            "Employees may roll over a maximum of 5 unused PTO days into the following calendar year."
        )
        claims = SourceAccuracyChecker.extract_claims(text)
        self.assertGreaterEqual(len(claims), 1)
        self.assertTrue(any("18 days" in c for c in claims))

    def test_audit_fully_supported_claims(self):
        """When answer claims exactly match source chunk text, faithfulness should be 1.0."""
        mock_chunks = [
            RetrievedChunk(
                rank=1,
                chunk_id="employee_benefits_chunk_001",
                source_text="Full-time regular employees accrue 18 days of Paid Time Off annually. Employees may roll over a maximum of 5 unused PTO days into the following calendar year.",
                metadata={"source_document": "employee_benefits.md", "section": "PTO Accrual"},
                score=0.92,
            )
        ]
        answer = "Full-time regular employees accrue 18 days of Paid Time Off annually. Up to 5 days can be rolled over."
        
        audit = SourceAccuracyChecker.audit_answer(
            answer=answer,
            retrieved_chunks=mock_chunks,
            is_fallback=False,
        )
        self.assertEqual(audit.faithfulness_score, 1.0)
        self.assertTrue(audit.is_faithful)
        self.assertEqual(len(audit.unsupported_claims), 0)

    def test_audit_detects_unsupported_hallucinated_claims(self):
        """When answer invents facts not present in chunks, faithfulness should drop."""
        mock_chunks = [
            RetrievedChunk(
                rank=1,
                chunk_id="sec_chunk_001",
                source_text="Suspected security breaches must be reported to the 24/7 IT Security Incident Hotline at extension 4357.",
                metadata={"source_document": "it_security_policy.md"},
                score=0.88,
            )
        ]
        # Inverted / hallucinated claims with numbers not in context (e.g. 500 dollars bonus, 48 hours deadline)
        hallucinated_answer = "Employees receive a $500 bonus for reporting within 48 hours to HR desk 9999."
        
        audit = SourceAccuracyChecker.audit_answer(
            answer=hallucinated_answer,
            retrieved_chunks=mock_chunks,
            is_fallback=False,
        )
        self.assertLess(audit.faithfulness_score, 0.5)
        self.assertFalse(audit.is_faithful)
        self.assertGreaterEqual(len(audit.unsupported_claims), 1)

    def test_audit_fallback_answer_is_safe(self):
        """Refusal fallback answers must be audited as safe with zero unsupported claims."""
        audit = SourceAccuracyChecker.audit_answer(
            answer=STANDARD_FALLBACK_ANSWER,
            retrieved_chunks=[],
            is_fallback=True,
        )
        self.assertEqual(audit.faithfulness_score, 1.0)
        self.assertTrue(audit.is_faithful)
        self.assertEqual(audit.total_claims_extracted, 0)


class TestGroundedAnswerGenerator(unittest.TestCase):
    """Unit and integration tests for grounded answer generation and context injection."""

    @classmethod
    def setUpClass(cls):
        chunks_path = Path(__file__).resolve().parent.parent / "data" / "embedded_chunks.json"
        if not chunks_path.exists():
            raise unittest.SkipTest(f"Required corpus file missing: {chunks_path}")
        cls.generator = GroundedAnswerGenerator(vector_store_path=str(chunks_path))

    def test_generate_grounded_answer_pto(self):
        """Test generating a grounded answer for PTO query produces cited factual details."""
        query = "How many days of paid time off do employees get each year, and can unused PTO be rolled over?"
        result = self.generator.generate_grounded_answer(query=query, k=3)
        
        self.assertIsInstance(result, GroundedGenerationResult)
        self.assertEqual(result.query, query)
        self.assertFalse(result.is_fallback)
        self.assertGreater(result.retrieved_chunk_count, 0)
        self.assertGreater(len(result.returned_sources), 0)
        
        # Verify PTO policy facts (18 days, 5 days rollover) in answer
        self.assertIn("18", result.answer)
        self.assertIn("employee_benefits.md", result.returned_sources[0]["source_document"])
        
        # Verify audit passed
        self.assertIsNotNone(result.source_accuracy_audit)
        self.assertTrue(result.source_accuracy_audit.is_faithful)

    def test_generate_grounded_answer_security_incident(self):
        """Test generating a grounded answer for Security Incident hotline query."""
        query = "What is the procedure for reporting suspected security breaches and active malware?"
        result = self.generator.generate_grounded_answer(query=query, k=3)
        
        self.assertFalse(result.is_fallback)
        self.assertIn("it_security_policy.md", result.returned_sources[0]["source_document"])
        self.assertTrue(result.source_accuracy_audit.is_faithful)

    def test_missing_context_fallback_out_of_scope(self):
        """Out-of-scope query with no corpus match must return standard refusal fallback."""
        query = "What is the stock option strike price and 4-year equity vesting schedule for executives?"
        result = self.generator.generate_grounded_answer(query=query, k=3)
        
        self.assertTrue(result.is_fallback)
        self.assertIn("I don't have access to this information", result.answer)
        self.assertIn("hr@company.com", result.answer)
        self.assertEqual(result.retrieved_chunk_count, 0)
        self.assertEqual(len(result.returned_sources), 0)

    def test_forced_fallback_mode(self):
        """Explicitly forced fallback must return standard refusal."""
        query = "Any random query"
        result = self.generator.generate_grounded_answer(query=query, force_fallback=True)
        
        self.assertTrue(result.is_fallback)
        self.assertEqual(result.answer, STANDARD_FALLBACK_ANSWER)

    def test_minimum_relevant_chunk_guardrail(self):
        """Sparse above-threshold retrieval must refuse when more support is required."""
        generator = GroundedAnswerGenerator(
            vector_store_path=self.generator.vector_store_path,
            min_relevant_chunks=2,
        )
        generator.retriever.retrieve_top_k = lambda query, k: [
            RetrievedChunk(
                rank=1,
                chunk_id="single_supporting_chunk",
                source_text="A policy detail with enough similarity but insufficient support.",
                metadata={"source_document": "policy.md"},
                score=0.91,
            )
        ]

        result = generator.generate_grounded_answer("What is the policy?", k=3)

        self.assertTrue(result.is_fallback)
        self.assertIn("at least 2 required", result.fallback_reason)
        self.assertEqual(result.retrieved_chunk_count, 0)

    def test_unfaithful_generated_answer_is_refused(self):
        """A high-score context cannot bypass the final source-faithfulness gate."""
        generator = GroundedAnswerGenerator(
            vector_store_path=self.generator.vector_store_path,
        )
        generator._call_llm_api = lambda user_prompt, system_prompt: (
            "Employees receive a $500 bonus for reporting incidents within 48 hours."
        )

        result = generator.generate_grounded_answer(
            "What is the procedure for reporting suspected security breaches?",
            k=3,
        )

        self.assertTrue(result.is_fallback)
        self.assertEqual(result.answer, STANDARD_FALLBACK_ANSWER)
        self.assertIn("source-faithfulness audit", result.fallback_reason)
        self.assertEqual(result.returned_sources, [])


class TestComparativeGrounding(unittest.TestCase):
    """Unit tests for side-by-side with vs. without retrieval comparison (Task 4)."""

    @classmethod
    def setUpClass(cls):
        chunks_path = Path(__file__).resolve().parent.parent / "data" / "embedded_chunks.json"
        if not chunks_path.exists():
            raise unittest.SkipTest(f"Required corpus file missing: {chunks_path}")
        cls.generator = GroundedAnswerGenerator(vector_store_path=str(chunks_path))

    def test_compare_with_and_without_retrieval(self):
        """Test side-by-side comparison on PTO policy query."""
        query = "How many days of paid time off do employees get each year, and can unused PTO be rolled over?"
        comp = self.generator.compare_with_and_without_retrieval(
            query=query,
            category="HR Benefits",
            k=3,
        )
        
        self.assertIsInstance(comp, RetrievalComparisonResult)
        self.assertEqual(comp.query, query)
        
        # With retrieval: high faithfulness, verified sources
        self.assertGreater(comp.with_retrieval.retrieved_chunk_count, 0)
        self.assertTrue(comp.with_retrieval.source_accuracy_audit.is_faithful)
        
        # Without retrieval: unverified, 0 sources
        self.assertEqual(comp.without_retrieval.retrieved_chunk_count, 0)
        self.assertEqual(comp.without_retrieval.source_accuracy_audit.faithfulness_score, 0.0)
        
        # Verify discrepancy identification
        self.assertGreater(len(comp.factual_discrepancies), 0)
        self.assertTrue(comp.hallucination_detected_without_rag)
        self.assertGreater(len(comp.specificity_gain), 5)


class TestBenchmarkAndReportGeneration(unittest.TestCase):
    """Tests end-to-end benchmark execution and Markdown report formatting (Task 5)."""

    @classmethod
    def setUpClass(cls):
        chunks_path = Path(__file__).resolve().parent.parent / "data" / "embedded_chunks.json"
        if not chunks_path.exists():
            raise unittest.SkipTest(f"Required corpus file missing: {chunks_path}")
        cls.chunks_path = str(chunks_path)

    def test_run_benchmark_structure(self):
        """Test running benchmark returns expected top-level keys and populated scenarios."""
        data = run_grounded_generation_benchmark(
            vector_store_path=self.chunks_path,
            save_artifacts=False,
        )
        
        self.assertIn("metadata", data)
        self.assertIn("grounded_answers", data)
        self.assertIn("fallback_demonstrations", data)
        self.assertIn("retrieval_comparisons", data)
        
        self.assertGreater(len(data["grounded_answers"]), 0)
        self.assertGreater(len(data["fallback_demonstrations"]), 0)
        self.assertGreater(len(data["retrieval_comparisons"]), 0)

    def test_generate_report_markdown(self):
        """Test Markdown report generator produces formatted sections and comparison tables."""
        data = run_grounded_generation_benchmark(
            vector_store_path=self.chunks_path,
            save_artifacts=False,
        )
        report_md = generate_grounded_generation_report(data)
        
        self.assertIn("# Grounded Answer Generation & Source Accuracy Verification Audit Report", report_md)
        self.assertIn("## 1. Executive Summary & Architecture", report_md)
        self.assertIn("## 2. Grounded Generation & Source Accuracy Verification", report_md)
        self.assertIn("## 3. Missing-Context Fallback Demonstrations", report_md)
        self.assertIn("## 4. Comparative Analysis: With vs. Without Retrieval", report_md)
        self.assertIn("## 5. Summary Findings & Production Guidelines", report_md)


if __name__ == "__main__":
    unittest.main(verbosity=2)
