"""
Unit & Integration Tests for RAG Progressive Streaming & Source Citations.

Tests cover:
- Task 1: Progressive answer token streaming via Server-Sent Events (SSE).
- Task 2: Inline citation markers ([1], [2]) and metadata attribution.
- Task 3: Retrieved chunk text availability for user source inspection.
- Task 4: Missing-context fallback streaming and error event handling.
- FastAPI /query/stream and /ui endpoints.
"""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

from fastapi.testclient import TestClient

from src.streaming_generator import (
    StreamingAnswerGenerator,
    StreamEvent,
    CitationMarker,
    STANDARD_FALLBACK_ANSWER
)
from src.similarity_search import VectorStoreRetriever, RetrievedChunk
from src.api import app


class TestStreamingResponsesAndCitations(unittest.TestCase):
    """Test suite for progressive streaming answers and source citations."""

    @classmethod
    def setUpClass(cls):
        cls.retriever = VectorStoreRetriever()
        cls.client = TestClient(app)

    def test_stream_event_sse_serialization(self):
        """Verify StreamEvent serializes correctly to Server-Sent Event (SSE) format."""
        event = StreamEvent(
            event_type="token",
            data={"token": "Hello, world!"},
            timestamp="2026-09-10T12:00:00Z"
        )
        sse_str = event.to_sse()
        self.assertTrue(sse_str.startswith("data: "))
        self.assertTrue(sse_str.endswith("\n\n"))

        payload = json.loads(sse_str[6:].strip())
        self.assertEqual(payload["type"], "token")
        self.assertEqual(payload["data"]["token"], "Hello, world!")
        self.assertEqual(payload["timestamp"], "2026-09-10T12:00:00Z")

    def test_progressive_streaming_event_sequence(self):
        """Task 1 & 2: Test event sequence includes start, sources, token, citation, and complete."""
        generator = StreamingAnswerGenerator(
            retriever=self.retriever,
            min_similarity_threshold=0.0,
            stream_delay=0.0  # Fast execution in tests
        )

        events = list(generator.stream_grounded_answer(
            query="What is the company PTO policy?",
            k=3,
            score_threshold=0.0
        ))

        event_types = [e.event_type for e in events]
        self.assertIn("start", event_types)
        self.assertIn("sources", event_types)
        self.assertIn("token", event_types)
        self.assertIn("complete", event_types)

        # First event must be start
        self.assertEqual(event_types[0], "start")
        # Second event must be sources
        self.assertEqual(event_types[1], "sources")
        # Last event must be complete
        self.assertEqual(event_types[-1], "complete")

        # Verify tokens streamed progressively
        tokens = [e.data["token"] for e in events if e.event_type == "token"]
        self.assertGreater(len(tokens), 5, "Tokens should be streamed progressively in multiple chunks")

        complete_event = events[-1]
        reconstructed_answer = "".join(tokens)
        self.assertEqual(complete_event.data["answer"], reconstructed_answer)
        self.assertFalse(complete_event.data.get("is_fallback", False))

    def test_sources_event_includes_chunk_text_for_inspection(self):
        """Task 3: Test that retrieved sources event contains full chunk text for UI inspection."""
        generator = StreamingAnswerGenerator(
            retriever=self.retriever,
            min_similarity_threshold=0.0,
            stream_delay=0.0
        )

        events = list(generator.stream_grounded_answer(
            query="What is the company PTO policy?",
            k=3
        ))

        sources_events = [e for e in events if e.event_type == "sources"]
        self.assertEqual(len(sources_events), 1)

        sources_data = sources_events[0].data.get("sources", [])
        self.assertGreater(len(sources_data), 0, "Retrieved sources should not be empty")

        for src in sources_data:
            self.assertIn("tag", src, "Source must have citation tag e.g. [1]")
            self.assertIn("chunk_id", src, "Source must include chunk_id")
            self.assertIn("source_document", src, "Source must include document name")
            self.assertIn("section", src, "Source must include section details")
            self.assertIn("similarity_score", src, "Source must include similarity score")
            # TASK 3 CRITICAL: Chunk text must be present for user inspection
            self.assertIn("text", src, "Source must contain original chunk text for user inspection")
            self.assertGreater(len(src["text"]), 10, "Chunk text must not be blank")

    def test_citation_events_and_markers(self):
        """Task 2: Verify citations are extracted and linked to source chunks."""
        generator = StreamingAnswerGenerator(
            retriever=self.retriever,
            min_similarity_threshold=0.0,
            stream_delay=0.0
        )

        events = list(generator.stream_grounded_answer(
            query="What is the company PTO policy?",
            k=3
        ))

        citation_events = [e for e in events if e.event_type == "citation"]
        self.assertGreater(len(citation_events), 0, "At least one citation event should be emitted")

        first_citation = citation_events[0].data
        self.assertIn("marker", first_citation)
        self.assertTrue(first_citation["marker"].startswith("[") and first_citation["marker"].endswith("]"))
        self.assertIn("source", first_citation)
        self.assertIn("source_document", first_citation["source"])
        self.assertIn("chunk_id", first_citation["source"])

    def test_fallback_streaming_when_no_context_found(self):
        """Task 4: Test that queries with no relevant context stream standard refusal without hallucinated citations."""
        generator = StreamingAnswerGenerator(
            retriever=self.retriever,
            min_similarity_threshold=0.999,  # Unattainable threshold
            stream_delay=0.0
        )

        events = list(generator.stream_grounded_answer(
            query="What is the recipe for chocolate chip cookies?",
            k=3,
            score_threshold=0.999
        ))

        complete_event = events[-1]
        self.assertEqual(complete_event.event_type, "complete")
        self.assertTrue(complete_event.data.get("is_fallback", False))
        self.assertEqual(len(complete_event.data.get("citations", [])), 0)

        # Ensure answer streamed the refusal message
        tokens = [e.data["token"] for e in events if e.event_type == "token"]
        answer = "".join(tokens)
        self.assertIn("I don't have access to this information", answer)

    def test_streaming_generator_error_handling(self):
        """Task 4: Test generator yields error event when retriever throws an exception."""
        failing_retriever = MagicMock()
        failing_retriever.retrieve_top_k.side_effect = RuntimeError("Vector database connection lost")

        generator = StreamingAnswerGenerator(
            retriever=failing_retriever,
            stream_delay=0.0
        )

        events = list(generator.stream_grounded_answer(query="Any question"))
        event_types = [e.event_type for e in events]

        self.assertIn("start", event_types)
        self.assertIn("error", event_types)

        error_event = [e for e in events if e.event_type == "error"][0]
        self.assertEqual(error_event.data["error"], "RuntimeError")
        self.assertIn("Vector database connection lost", error_event.data["message"])

    def test_fastapi_query_stream_endpoint(self):
        """Task 1 & FastAPI integration: Test /query/stream HTTP endpoint returns 200 and SSE stream."""
        response = self.client.post(
            "/query/stream",
            json={"question": "What is the PTO policy?", "k": 3}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue("text/event-stream" in response.headers.get("content-type", ""))

        lines = response.text.split("\n")
        data_lines = [l for l in lines if l.startswith("data: ")]
        self.assertGreater(len(data_lines), 3)

        parsed_events = [json.loads(l[6:]) for l in data_lines]
        types = [e["type"] for e in parsed_events]
        self.assertIn("start", types)
        self.assertIn("sources", types)
        self.assertIn("token", types)
        self.assertIn("complete", types)

    def test_fastapi_ui_endpoint(self):
        """Test that /ui route serves the chat UI HTML file."""
        response = self.client.get("/ui")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("text/html" in response.headers.get("content-type", ""))
        self.assertIn("RAG Streaming Assistant", response.text)
        self.assertIn("citation-marker", response.text)
        self.assertIn("answer-citations", response.text)


if __name__ == "__main__":
    unittest.main()

