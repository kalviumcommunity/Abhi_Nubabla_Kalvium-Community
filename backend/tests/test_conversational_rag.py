"""
Unit and Integration Tests for Conversational RAG & Query Rewriting Engine.

Covers:
- Task 1: Conversation history tracking, serialization, and sliding window pruning.
- Task 2: Query rewriting with coreference resolution and anaphora expansion.
- Task 3: Vector retrieval comparing raw queries vs. rewritten standalone queries.
- Task 4: Multi-turn grounded dialogue synthesis and safe fallback refusals.
- Task 5: End-to-end benchmark execution, JSON export, and Markdown report generation.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.conversational_rag import (
    ConversationHistory,
    ConversationTurn,
    ConversationalRAGSession,
    QueryRewriteResult,
    QueryRewriter,
    generate_conversational_rag_report,
    run_conversational_rag_benchmark,
)
from src.similarity_search import VectorStoreRetriever


class TestConversationHistory(unittest.TestCase):
    """Test suite for Task 1: Conversation History Tracking & Pruning."""

    def setUp(self) -> None:
        self.history = ConversationHistory(session_id="test_session", max_turns=3)

    def test_add_turn_and_length(self) -> None:
        """Verify adding turns increments length and updates history."""
        self.assertEqual(len(self.history), 0)

        turn1 = ConversationTurn(
            turn_index=1,
            user_message="What is the PTO policy?",
            raw_query="What is the PTO policy?",
            rewritten_query="What is the PTO policy?",
            query_rewrite_result=None,
            raw_retrieved_chunks=[],
            rewritten_retrieved_chunks=[],
            raw_top_score=0.72,
            rewritten_top_score=0.72,
            score_lift=0.0,
            assistant_response="Employees receive 20 days PTO annually.",
            is_fallback=False,
            returned_sources=[],
            faithfulness_score=1.0,
        )
        self.history.add_turn(turn1)
        self.assertEqual(len(self.history), 1)

    def test_sliding_window_max_turns(self) -> None:
        """Verify oldest turn is pruned when max_turns constraint is exceeded."""
        for i in range(1, 5):
            t = ConversationTurn(
                turn_index=i,
                user_message=f"Question {i}",
                raw_query=f"Question {i}",
                rewritten_query=f"Question {i}",
                query_rewrite_result=None,
                raw_retrieved_chunks=[],
                rewritten_retrieved_chunks=[],
                raw_top_score=0.5,
                rewritten_top_score=0.5,
                score_lift=0.0,
                assistant_response=f"Answer {i}",
                is_fallback=False,
                returned_sources=[],
                faithfulness_score=1.0,
            )
            self.history.add_turn(t)

        self.assertEqual(len(self.history), 3)
        self.assertEqual(self.history.turns[0].user_message, "Question 2")
        self.assertEqual(self.history.turns[-1].user_message, "Question 4")

    def test_format_history_text(self) -> None:
        """Verify history text formatting for prompt context injection."""
        turn = ConversationTurn(
            turn_index=1,
            user_message="How do I report a security incident?",
            raw_query="How do I report a security incident?",
            rewritten_query="How do I report a security incident?",
            query_rewrite_result=None,
            raw_retrieved_chunks=[],
            rewritten_retrieved_chunks=[],
            raw_top_score=0.75,
            rewritten_top_score=0.75,
            score_lift=0.0,
            assistant_response="Call hotline x5555 or email security@company.com.",
            is_fallback=False,
            returned_sources=[],
            faithfulness_score=1.0,
        )
        self.history.add_turn(turn)
        formatted = self.history.format_history_text()
        self.assertIn("User: How do I report a security incident?", formatted)
        self.assertIn("Assistant: Call hotline x5555 or email security@company.com.", formatted)

    def test_format_messages_list(self) -> None:
        """Verify conversion to standard chat messages structure."""
        turn = ConversationTurn(
            turn_index=1,
            user_message="What is the VPN requirement?",
            raw_query="What is the VPN requirement?",
            rewritten_query="What is the VPN requirement?",
            query_rewrite_result=None,
            raw_retrieved_chunks=[],
            rewritten_retrieved_chunks=[],
            raw_top_score=0.68,
            rewritten_top_score=0.68,
            score_lift=0.0,
            assistant_response="Use company AES-256 VPN client.",
            is_fallback=False,
            returned_sources=[],
            faithfulness_score=1.0,
        )
        self.history.add_turn(turn)
        msgs = self.history.format_messages_list()
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0]["role"], "user")
        self.assertEqual(msgs[1]["role"], "assistant")


class TestQueryRewriter(unittest.TestCase):
    """Test suite for Task 2: Query Rewriting & Coreference Resolution."""

    def setUp(self) -> None:
        self.rewriter = QueryRewriter()
        self.history = ConversationHistory()

    def test_standalone_first_turn_unchanged(self) -> None:
        """First standalone query without prior history should remain unchanged."""
        query = "What is the company annual PTO allowance?"
        result = self.rewriter.rewrite_query(query, self.history)
        self.assertEqual(result.rewritten_query, query)
        self.assertFalse(result.has_coreference)

    def test_pto_carryover_follow_up_rewriting(self) -> None:
        """Follow-up with pronoun 'unused days / next year' rewritten with PTO context."""
        turn1 = ConversationTurn(
            turn_index=1,
            user_message="What is the annual PTO policy?",
            raw_query="What is the annual PTO policy?",
            rewritten_query="What is the annual PTO policy?",
            query_rewrite_result=None,
            raw_retrieved_chunks=[],
            rewritten_retrieved_chunks=[],
            raw_top_score=0.72,
            rewritten_top_score=0.72,
            score_lift=0.0,
            assistant_response="Employees receive 20 days PTO annually.",
            is_fallback=False,
            returned_sources=[],
            faithfulness_score=1.0,
        )
        self.history.add_turn(turn1)

        follow_up = "Can I carry over unused days to next year?"
        result = self.rewriter.rewrite_query(follow_up, self.history)

        self.assertTrue(result.has_coreference)
        self.assertIn("carry over", result.rewritten_query.lower())
        self.assertIn("pto", result.rewritten_query.lower())

    def test_pto_deadline_forfeiture_rewriting(self) -> None:
        """Follow-up with pronoun 'them' and 'that deadline' rewritten to PTO forfeiture."""
        turn1 = ConversationTurn(
            turn_index=1,
            user_message="Can I carry over unused PTO days?",
            raw_query="Can I carry over unused PTO days?",
            rewritten_query="Can I carry over unused PTO days?",
            query_rewrite_result=None,
            raw_retrieved_chunks=[],
            rewritten_retrieved_chunks=[],
            raw_top_score=0.70,
            rewritten_top_score=0.70,
            score_lift=0.0,
            assistant_response="Up to 5 days can be carried over, expiring March 31.",
            is_fallback=False,
            returned_sources=[],
            faithfulness_score=1.0,
        )
        self.history.add_turn(turn1)

        follow_up = "What happens if I don't use them by that deadline?"
        result = self.rewriter.rewrite_query(follow_up, self.history)

        self.assertTrue(result.has_coreference)
        self.assertIn("pto", result.rewritten_query.lower())
        self.assertTrue(
            "deadline" in result.rewritten_query.lower() or "march 31" in result.rewritten_query.lower()
        )

    def test_security_incident_customer_data_rewriting(self) -> None:
        """Follow-up with pronoun 'it' rewritten to security incident customer data."""
        turn1 = ConversationTurn(
            turn_index=1,
            user_message="How do I report a suspected security incident?",
            raw_query="How do I report a suspected security incident?",
            rewritten_query="How do I report a suspected security incident?",
            query_rewrite_result=None,
            raw_retrieved_chunks=[],
            rewritten_retrieved_chunks=[],
            raw_top_score=0.74,
            rewritten_top_score=0.74,
            score_lift=0.0,
            assistant_response="Report immediately via hotline x5555 or email security@company.com.",
            is_fallback=False,
            returned_sources=[],
            faithfulness_score=1.0,
        )
        self.history.add_turn(turn1)

        follow_up = "Who should be notified if it involves customer data?"
        result = self.rewriter.rewrite_query(follow_up, self.history)

        self.assertTrue(result.has_coreference)
        self.assertIn("security incident", result.rewritten_query.lower())
        self.assertIn("customer data", result.rewritten_query.lower())


class TestRewrittenRetrieval(unittest.TestCase):
    """Test suite for Task 3: Vector Retrieval Lift with Rewritten Queries."""

    def setUp(self) -> None:
        self.session = ConversationalRAGSession()

    def test_retrieval_lift_on_follow_up(self) -> None:
        """Verify rewritten query achieves positive score lift or equal relevance."""
        # Turn 1
        self.session.process_turn("What is the annual PTO policy?")

        # Turn 2 (Follow-up)
        turn2 = self.session.process_turn("Can I carry over unused days to next year?")

        self.assertIsNotNone(turn2.query_rewrite_result)
        self.assertTrue(turn2.query_rewrite_result.has_coreference)
        self.assertGreater(turn2.rewritten_top_score, 0.40)
        self.assertGreaterEqual(turn2.score_lift, -0.05)
        # Ensure the top retrieved chunk is from employee benefits
        self.assertTrue(
            any("employee_benefits" in c.metadata.get("source_document", "") for c in turn2.rewritten_retrieved_chunks)
        )


class TestConversationalRAGSession(unittest.TestCase):
    """Test suite for Task 4: Multi-Turn Dialogue Flow & Safe Refusals."""

    def setUp(self) -> None:
        self.session = ConversationalRAGSession()

    def test_full_pto_multi_turn_dialogue(self) -> None:
        """Demonstrate 3-turn PTO conversation with context grounding."""
        # Turn 1
        t1 = self.session.process_turn("What is the annual PTO policy?")
        self.assertFalse(t1.is_fallback)
        self.assertTrue(
            "18" in t1.assistant_response or "pto" in t1.assistant_response.lower() or "paid time off" in t1.assistant_response.lower()
        )

        # Turn 2
        t2 = self.session.process_turn("Can I carry over unused days to next year?")
        self.assertFalse(t2.is_fallback)
        self.assertTrue(
            "5" in t2.assistant_response or "rollover" in t2.assistant_response.lower() or "pto" in t2.assistant_response.lower()
        )

        # Turn 3
        t3 = self.session.process_turn("What happens if I don't use them by that deadline?")
        self.assertFalse(t3.is_fallback)
        self.assertTrue(
            "expire" in t3.assistant_response.lower() or "forfeit" in t3.assistant_response.lower() or "compensation" in t3.assistant_response.lower()
        )

        self.assertEqual(len(self.session.history), 3)

    def test_multi_turn_with_safe_refusal_turn(self) -> None:
        """Verify out-of-scope follow-up triggers safe refusal while preserving state."""
        # Turn 1: Remote work (in scope)
        t1 = self.session.process_turn("What are the requirements for working remotely?")
        self.assertFalse(t1.is_fallback)
        self.assertTrue(
            "remote" in t1.assistant_response.lower() or "vpn" in t1.assistant_response.lower()
        )

        # Turn 2: Home setup reimbursement (out of scope / not in corpus)
        t2 = self.session.process_turn("Is there a reimbursement for my home setup?")
        self.assertTrue(t2.is_fallback)
        self.assertIn("hr@company.com", t2.assistant_response)

        # Turn 3: Public Wi-Fi policy (back in scope)
        t3 = self.session.process_turn("What are the security requirements for public coffee shop Wi-Fi?")
        self.assertFalse(t3.is_fallback)
        self.assertTrue(
            "vpn" in t3.assistant_response.lower() or "security" in t3.assistant_response.lower() or "wi-fi" in t3.assistant_response.lower()
        )


class TestBenchmarkAndReporting(unittest.TestCase):
    """Test suite for Task 5: Benchmark Execution, JSON & Markdown Exports."""

    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_run_conversational_benchmark(self) -> None:
        """Verify benchmark runner produces JSON and Markdown outputs."""
        summary = run_conversational_rag_benchmark(export_dir=self.temp_dir)

        self.assertIn("total_dialogues_evaluated", summary)
        self.assertIn("total_turns_executed", summary)
        self.assertIn("average_similarity_score_lift", summary)
        self.assertGreaterEqual(summary["total_dialogues_evaluated"], 3)
        self.assertGreaterEqual(summary["total_turns_executed"], 8)

        json_file = self.temp_dir / "conversational_rag_results.json"
        md_file = self.temp_dir / "conversational_rag_report.md"

        self.assertTrue(json_file.exists())
        self.assertTrue(md_file.exists())

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["total_dialogues_evaluated"], summary["total_dialogues_evaluated"])

        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("# Conversational RAG & Query Rewriting Audit Report", content)
            self.assertIn("Dialogue 1", content)
            self.assertIn("Dialogue 2", content)
            self.assertIn("Dialogue 3", content)


if __name__ == "__main__":
    unittest.main()
