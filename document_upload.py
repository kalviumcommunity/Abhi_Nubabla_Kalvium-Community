"""
CLI Entrypoint for Runtime Document Upload, Ingestion, Dynamic Indexing & REST API.

Usage Examples:
    # Run the end-to-end runtime searchability demo and benchmark:
    python document_upload.py --demo

    # Start the live RAG REST API HTTP server:
    python document_upload.py --server --port 8000

    # Upload a document directly to the local RAG engine:
    python document_upload.py --upload sample_corpus/ai_guidelines.md

    # Query the live vector store and get grounded answers:
    python document_upload.py --query "What are the rules for AI code assistants?"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.document_uploader import (
    RuntimeDocumentUploader,
    run_runtime_searchability_demo,
    start_server,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Runtime Document Upload, Dynamic Indexing & REST API for Staff RAG Assistant."
    )
    parser.add_argument(
        "--server",
        action="store_true",
        help="Start the multi-threaded RAG REST API HTTP server."
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address for API server (default: 127.0.0.1)."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port number for API server (default: 8000)."
    )
    parser.add_argument(
        "--upload",
        type=str,
        default=None,
        help="Path to a local document file to ingest, embed, and index dynamically."
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Query the live knowledge base."
    )
    parser.add_argument(
        "--k",
        type=int,
        default=3,
        help="Number of top chunks to retrieve (default: 3)."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run end-to-end runtime searchability demo and negative test suite."
    )
    parser.add_argument(
        "--export-dir",
        type=str,
        default="data",
        help="Output directory for generated JSON and Markdown reports."
    )

    args = parser.parse_args()

    # 1. Server mode
    if args.server:
        start_server(host=args.host, port=args.port)
        return

    uploader = RuntimeDocumentUploader()

    # 2. Upload mode
    if args.upload:
        file_path = Path(args.upload)
        if not file_path.exists():
            print(f"Error: File not found at '{args.upload}'")
            sys.exit(1)

        content = file_path.read_bytes()
        result = uploader.upload_and_index_document(filename=file_path.name, content=content)
        print("=" * 70)
        print(f"  Upload Status: {result.status} (HTTP {result.status_code})")
        print(f"  Message:       {result.message}")
        print(f"  Chunks Added:  {result.chunks_created}")
        print(f"  Tokens Added:  {result.tokens_indexed}")
        print(f"  Indexing Time: {result.indexing_time_sec:.4f}s")
        print(f"  Total Chunks:  {len(uploader.retriever.chunks_data)}")
        print("=" * 70)
        if result.status != "SUCCESS":
            sys.exit(1)
        return

    # 3. Query mode
    if args.query:
        query_resp = uploader.query(query_text=args.query, k=args.k)
        print("=" * 70)
        print(f"  Query:         {query_resp.query}")
        print(f"  Top Score:     {query_resp.top_score:.4f}")
        print(f"  Fallback:      {query_resp.is_fallback}")
        print(f"  Response Time: {query_resp.query_time_sec:.4f}s")
        print("=" * 70)
        print(f"\nAnswer:\n{query_resp.answer}\n")
        if query_resp.citations:
            print("Citations:")
            for cit in query_resp.citations:
                print(f"  - {cit}")
        return

    # 4. Demo mode (default if no args specified)
    print("=" * 70)
    print("  Running Runtime Document Upload & Dynamic Indexing Demonstration")
    print("=" * 70)

    export_dir = Path(args.export_dir)
    results = run_runtime_searchability_demo(uploader=uploader, export_dir=export_dir)

    print(f"\nDemonstration completed successfully in {results['total_elapsed_sec']:.3f}s!")
    print(f"Initial Chunks: {results['initial_corpus_chunks']}")
    print(f"Final Chunks:   {results['steps'][2]['total_chunks_after_upload']}")
    print(f"Retrieval Lift: +{results['steps'][2]['score_lift']:.4f}")
    print(f"\nArtifacts Exported:")
    print(f"  - JSON Results:   {export_dir / 'document_upload_results.json'}")
    print(f"  - Markdown Audit: {export_dir / 'document_upload_report.md'}")


if __name__ == "__main__":
    main()
