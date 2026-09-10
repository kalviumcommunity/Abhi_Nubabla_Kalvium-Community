#!/usr/bin/env python3
"""
Streaming Response & Citation Demonstration

This script demonstrates the streaming endpoint with progressive answer display,
inline citation markers, inspectable source chunks, and streaming error handling.

Usage:
    python streaming_demo.py [--auto] [--api-base URL]

Requirements:
    - Backend API running on http://localhost:8000 (or uses in-process streaming fallback)
    - Vector store initialized at data/embedded_chunks.json
"""

import sys
import os
import json
import time
import argparse
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

# Reconfigure stdout/stderr to UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass

# Add project root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import requests
from src.streaming_generator import StreamingAnswerGenerator
from src.similarity_search import VectorStoreRetriever


class StreamingDemo:
    """Demonstrates progressive streaming responses with citations."""

    def __init__(self, api_base: str = "http://localhost:8000"):
        self.api_base = api_base
        self.session = requests.Session()
        self.server_available = self._check_server_health()

    def _check_server_health(self) -> bool:
        """Check if HTTP API server is reachable."""
        try:
            r = self.session.get(f"{self.api_base}/health", timeout=1.5)
            return r.status_code == 200
        except Exception:
            return False

    def stream_query(self, question: str, k: int = 3) -> Dict[str, Any]:
        """
        Send a streaming query and capture the progressive response.
        Uses HTTP SSE if server is running; otherwise uses in-process streaming.
        """
        print(f"\n{'='*80}")
        print("STREAMING QUERY")
        print(f"{'='*80}")
        print(f"Question: {question}")
        print(f"Mode: {'Live HTTP Server (' + self.api_base + ')' if self.server_available else 'Direct In-Process Streaming Engine'}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"{'='*80}\n")

        result = {
            "question": question,
            "answer_tokens": [],
            "citations": [],
            "sources": [],
            "events": [],
            "errors": []
        }

        if self.server_available:
            return self._stream_via_http(question, k, result)
        else:
            return self._stream_in_process(question, k, result)

    def _stream_via_http(self, question: str, k: int, result: Dict) -> Dict:
        """Stream via FastAPI HTTP SSE endpoint."""
        url = f"{self.api_base}/query/stream"
        payload = {"question": question, "k": k, "score_threshold": 0.0}

        try:
            response = self.session.post(url, json=payload, stream=True, timeout=15)
            response.raise_for_status()

            for line in response.iter_lines():
                if line.startswith(b"data: "):
                    try:
                        event_json = json.loads(line[6:].decode('utf-8'))
                        self._process_event(event_json, result)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing event JSON: {e}")

            return result

        except requests.exceptions.RequestException as e:
            err = f"HTTP Request failed: {e}"
            print(f"❌ {err}")
            result["errors"].append(err)
            return result

    def _stream_in_process(self, question: str, k: int, result: Dict) -> Dict:
        """Stream via direct in-process generator."""
        retriever = VectorStoreRetriever()
        generator = StreamingAnswerGenerator(retriever=retriever, stream_delay=0.01)

        for event in generator.stream_grounded_answer(query=question, k=k, score_threshold=0.0):
            event_dict = {
                "type": event.event_type,
                "data": event.data,
                "timestamp": event.timestamp
            }
            self._process_event(event_dict, result)

        return result

    def _process_event(self, event_data: Dict[str, Any], result: Dict) -> None:
        """Process a single streaming event and output progressively."""
        event_type = event_data.get("type")
        data = event_data.get("data", {})
        result["events"].append(event_data)

        if event_type == "start":
            print(f"⏱️  [START] {data.get('message', 'Processing...')}\n")

        elif event_type == "sources":
            sources = data.get("sources", [])
            result["sources"] = sources
            print(f"📚 [SOURCES RETRIEVED] ({len(sources)} chunks):")
            for src in sources:
                tag = src.get("tag") or f"[{src.get('rank')}]"
                print(f"   {tag} {src.get('source_document')} > {src.get('section')}")
                print(f"       Chunk ID: {src.get('chunk_id')} | Score: {src.get('similarity_score', 0):.4f} | Tokens: {src.get('token_count')}")
            print("\n💬 [STREAMING ANSWER]:")
            print("-" * 50)

        elif event_type == "token":
            token = data.get("token", "")
            result["answer_tokens"].append(token)
            sys.stdout.write(token)
            sys.stdout.flush()

        elif event_type == "citation":
            marker = data.get("marker", "")
            source = data.get("source", {})
            result["citations"].append({
                "marker": marker,
                "source": source
            })

        elif event_type == "complete":
            result["complete_data"] = data
            print(f"\n{'-' * 50}")
            print(f"✅ [COMPLETE] Latency: {data.get('latency_ms', 0)}ms | Retrieved: {data.get('retrieval_count', 0)} chunks")

        elif event_type == "error":
            error_msg = f"{data.get('error', 'Error')}: {data.get('message', 'Unknown error')}"
            print(f"\n❌ [ERROR] {error_msg}")
            result["errors"].append(error_msg)

    def print_inspection_summary(self, result: Dict) -> None:
        """Print full citation mapping and retrieved chunk text for source inspection (Task 3)."""
        print(f"\n{'='*80}")
        print("CITED SOURCE INSPECTION (TASK 2 & TASK 3 VERIFICATION)")
        print(f"{'='*80}")

        citations = result.get("citations", [])
        sources = result.get("sources", [])

        if not sources:
            print("No sources were retrieved.")
            return

        print(f"\nTotal Retrieved Sources: {len(sources)}")
        print(f"Citations Emitted: {len(citations)}")

        for idx, src in enumerate(sources, 1):
            tag = src.get("tag") or f"[{idx}]"
            print(f"\n--- Source {tag} ---")
            print(f"Document Name : {src.get('source_document')}")
            print(f"Section       : {src.get('section')}")
            print(f"Chunk ID      : {src.get('chunk_id')}")
            print(f"Score         : {src.get('similarity_score'):.4f}")
            print(f"Token Count   : {src.get('token_count')}")

            # Display the actual chunk text (Task 3 requirement)
            chunk_text = src.get("text", "")
            if chunk_text:
                preview = chunk_text[:280] + "..." if len(chunk_text) > 280 else chunk_text
                print(f"Retrieved Chunk Content (Inspectable):\n  \"{preview}\"")
            else:
                print("Chunk text not available.")

        print(f"\n{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description="Demonstrate RAG streaming responses and inspectable citations.")
    parser.add_argument("--auto", action="store_true", help="Run automatically without pausing between queries")
    parser.add_argument("--api-base", default="http://localhost:8000", help="Base URL of FastAPI server")
    args = parser.parse_args()

    demo = StreamingDemo(api_base=args.api_base)

    sample_questions = [
        "What is the company's PTO policy?",
        "What are the network encryption and VPN requirements?",
        "How do I submit an IT equipment request?"
    ]

    print("=" * 80)
    print("      RAG STREAMING RESPONSES & CITATION INSPECTION DEMONSTRATION")
    print("=" * 80)
    print(f"API Base URL : {demo.api_base}")
    print(f"Server Status: {'CONNECTED' if demo.server_available else 'OFFLINE (Using In-Process Fallback Engine)'}")
    print("=" * 80)

    for i, question in enumerate(sample_questions, 1):
        result = demo.stream_query(question)
        demo.print_inspection_summary(result)

        if not args.auto and i < len(sample_questions):
            print("Press Enter to run next query demonstration...")
            try:
                input()
            except (EOFError, KeyboardInterrupt):
                break


if __name__ == "__main__":
    main()
