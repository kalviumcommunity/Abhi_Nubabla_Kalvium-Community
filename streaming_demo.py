#!/usr/bin/env python3
"""
Streaming Response & Citation Demonstration

This script demonstrates the streaming endpoint with progressive answer display
and citation markers. Run this to see the streaming RAG in action.

Usage:
    python streaming_demo.py
    
Requirements:
    - Backend API running on http://localhost:8000
    - Vector store initialized at data/embedded_chunks.json
"""

import requests
import json
import sys
from typing import Dict, Any
from datetime import datetime
import time


class StreamingDemo:
    """Demonstrates streaming responses with citations."""
    
    def __init__(self, api_base: str = "http://localhost:8000"):
        self.api_base = api_base
        self.session = requests.Session()
    
    def stream_query(self, question: str, k: int = 3) -> Dict[str, Any]:
        """
        Send a streaming query and capture the response.
        
        Args:
            question: User question
            k: Number of chunks to retrieve
            
        Returns:
            Dictionary containing full answer, sources, and metadata
        """
        url = f"{self.api_base}/query/stream"
        
        payload = {
            "question": question,
            "k": k,
            "score_threshold": 0.0
        }
        
        print(f"\n{'='*80}")
        print(f"STREAMING QUERY")
        print(f"{'='*80}")
        print(f"Question: {question}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"{'='*80}\n")
        
        try:
            response = self.session.post(url, json=payload, stream=True)
            response.raise_for_status()
            
            result = {
                "answer_tokens": [],
                "citations": [],
                "sources": [],
                "events": [],
                "errors": []
            }
            
            # Process streaming events
            for line in response.iter_lines():
                if line.startswith(b"data: "):
                    try:
                        event_json = json.loads(line[6:].decode('utf-8'))
                        event = self._process_event(event_json, result)
                        result["events"].append(event)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing event: {e}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return {"error": str(e)}
    
    def _process_event(self, event_data: Dict[str, Any], result: Dict) -> Dict:
        """Process a single streaming event."""
        event_type = event_data.get("type")
        data = event_data.get("data", {})
        timestamp = event_data.get("timestamp", "")
        
        event_info = {
            "type": event_type,
            "timestamp": timestamp,
            "data": data
        }
        
        if event_type == "start":
            print(f"⏱️  START: {data.get('message', 'Processing...')}")
        
        elif event_type == "sources":
            print(f"\n📚 SOURCES RETRIEVED:")
            sources = data.get("sources", [])
            for src in sources:
                print(f"   [{src.get('rank')}] {src.get('source_document')} - {src.get('section')}")
                print(f"       Score: {src.get('similarity_score'):.3f} | Tokens: {src.get('token_count')}")
            result["sources"] = sources
        
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
            # Citations are printed with tokens
        
        elif event_type == "complete":
            print(f"\n\n✅ COMPLETE")
            print(f"   Latency: {data.get('latency_ms', 'N/A')}ms")
            print(f"   Citations: {len(data.get('citations', []))}")
            print(f"   Sources used: {data.get('retrieval_count', 0)}")
            
            result["complete_data"] = data
        
        elif event_type == "error":
            error_msg = f"{data.get('error', 'Unknown')}: {data.get('message', 'No message')}"
            print(f"\n❌ ERROR: {error_msg}")
            result["errors"].append(error_msg)
        
        return event_info
    
    def print_results_summary(self, result: Dict) -> None:
        """Print a summary of the streaming results."""
        print(f"\n{'='*80}")
        print(f"RESULTS SUMMARY")
        print(f"{'='*80}")
        
        if "error" in result:
            print(f"❌ Failed: {result['error']}")
            return
        
        answer_text = "".join(result.get("answer_tokens", []))
        print(f"\n📝 FULL ANSWER ({len(answer_text)} chars):")
        print(f"{'-'*80}")
        print(answer_text[:500] + ("..." if len(answer_text) > 500 else ""))
        print(f"{'-'*80}")
        
        sources = result.get("sources", [])
        if sources:
            print(f"\n🔗 CITATIONS ({len(sources)} sources):")
            for src in sources:
                print(f"   • [{src.get('rank')}] {src.get('source_document')}")
                print(f"      Section: {src.get('section')}")
                print(f"      Chunk ID: {src.get('chunk_id')}")
                print(f"      Relevance: {src.get('similarity_score'):.3f}")
        
        errors = result.get("errors", [])
        if errors:
            print(f"\n⚠️  ERRORS ({len(errors)}):")
            for err in errors:
                print(f"   • {err}")
        
        metrics = result.get("complete_data", {})
        if metrics:
            print(f"\n⏱️  METRICS:")
            print(f"   • Latency: {metrics.get('latency_ms', 'N/A')}ms")
            print(f"   • Retrieved chunks: {metrics.get('retrieval_count', 0)}")
        
        print(f"\n{'='*80}")


def main():
    """Run the streaming demo."""
    demo = StreamingDemo()
    
    # Sample questions to demonstrate streaming
    sample_questions = [
        "What is the company's PTO policy?",
        "How should I report a security incident?",
        "What VPN requirements do we have?"
    ]
    
    print("""
    ╔════════════════════════════════════════════════════════════════════════════╗
    ║                  RAG STREAMING & CITATION DEMO                             ║
    ║                                                                            ║
    ║  This demo shows progressive answer streaming with inline citations.      ║
    ║  Watch as the answer appears token-by-token with [n] citation markers.    ║
    ║  Click on citations in the UI to view source documents.                   ║
    ╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Check API health
    try:
        health = demo.session.get(f"{demo.api_base}/health", timeout=2).json()
        print(f"✅ API Status: {health.get('status')}")
        print(f"   Service: {health.get('service')}")
        print(f"   Version: {health.get('version')}\n")
    except Exception as e:
        print(f"❌ Cannot connect to API at {demo.api_base}")
        print(f"   Make sure the API is running: uvicorn src.api:app --reload")
        sys.exit(1)
    
    # Run demos
    for i, question in enumerate(sample_questions, 1):
        result = demo.stream_query(question)
        demo.print_results_summary(result)
        
        if i < len(sample_questions):
            print("\n" + "="*80)
            print("Press Enter to continue to next question...")
            input()


if __name__ == "__main__":
    main()
