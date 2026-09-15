#!/usr/bin/env python3
"""
Enterprise Contract Storage & RAG Backend Entry Point.

Usage:
    python main.py
    python main.py --cli
"""

import sys
import os
import argparse
import uvicorn
from pathlib import Path

# Add backend directory to sys.path to allow clean imports
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import AppConfig, setup_logger
from app.db.supabase import supabase_db
from app.vector_store.pinecone_store import vector_store
from app.rag.generator import contract_qa_generator, get_groq_client, get_openrouter_embedding_client
from app.ingestion.contract_processor import contract_processor

logger = setup_logger("main_entry")


def run_cli_interactive():
    """Interactive command-line client for corporate contract storage and RAG Q&A."""
    print("\n=======================================================")
    print("      Enterprise Contract RAG Terminal Client          ")
    print("=======================================================\n")
    print("Commands:")
    print("  upload <path_to_contract_file>  - Ingest PDF/DOCX/TXT contract")
    print("  list                             - List indexed corporate contracts")
    print("  ask <your question>              - Ask question regarding stored contracts")
    print("  exit                             - Quit terminal client\n")

    embedding_client = get_openrouter_embedding_client()

    while True:
        try:
            cmd_input = input("Contract-RAG> ").strip()
            if not cmd_input:
                continue
            if cmd_input.lower() in ("exit", "quit"):
                print("Goodbye!")
                break

            if cmd_input.lower().startswith("upload "):
                file_path_str = cmd_input[7:].strip().strip('"').strip("'")
                fpath = Path(file_path_str)
                if not fpath.exists():
                    print(f"Error: File not found at '{fpath}'")
                    continue
                print(f"Ingesting contract '{fpath.name}'...")
                chunks = contract_processor.process_file(fpath)
                indexed_count = vector_store.add_contract_chunks(chunks, embedding_client)
                meta = chunks[0]["metadata"]
                print(f"Successfully processed & indexed {indexed_count} chunks for '{meta.get('contract_title')}' (ID: {meta.get('contract_id')}).\n")

            elif cmd_input.lower() == "list":
                contracts = vector_store.list_indexed_contracts()
                if not contracts:
                    print("No corporate contracts currently indexed in vector store.")
                else:
                    print(f"\nFound {len(contracts)} Corporate Contract(s):")
                    for idx, c in enumerate(contracts, 1):
                        print(f"  {idx}. [{c['contract_id']}] {c['title']} | Type: {c['contract_type']} | Chunks: {c['total_chunks']}")
                print()

            elif cmd_input.lower().startswith("ask ") or "?" in cmd_input or len(cmd_input) > 5:
                query_text = cmd_input[4:].strip() if cmd_input.lower().startswith("ask ") else cmd_input
                print("\nSearching contracts & synthesizing grounded answer...\n")
                res = contract_qa_generator.generate_answer(question=query_text)
                print("--- ANSWER ---")
                print(res["answer"])
                print("\n--- SOURCES & CITATIONS ---")
                if not res["sources"]:
                    print("No explicit citations retrieved.")
                for s in res["sources"]:
                    print(f" • [{s['chunk_id']}] {s['contract_title']} ({s['section_title']}) - Match: {s['score']:.2f}")
                print()

            else:
                print("Unknown command. Type 'upload <path>', 'list', 'ask <question>', or 'exit'.")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}\n")


def main():
    parser = argparse.ArgumentParser(description="Enterprise Contract Storage & RAG Backend Server.")
    parser.add_argument("--host", type=str, default=AppConfig.API_HOST, help="API server host binding.")
    parser.add_argument("--port", type=int, default=AppConfig.API_PORT, help="API server port number.")
    parser.add_argument("--cli", action="store_true", help="Launch interactive CLI mode instead of web server.")
    args = parser.parse_args()

    print("\n=======================================================")
    print("      Starting Enterprise Contract RAG Backend        ")
    print("=======================================================")
    print(f" • Supabase Auth & DB Configured: {supabase_db.is_configured()}")
    print(f" • Vector Storage Mode:          {'Pinecone Vector Store' if vector_store.use_pinecone else 'Local Persistent Vector Index'}")
    print(f" • Groq LLM Model:               {AppConfig.GROQ_MODEL}")
    print(f" • OpenRouter Embedding Model:   {AppConfig.EMBEDDING_MODEL}")
    print(f" • Embedding Vector Dimension:   {AppConfig.EMBEDDING_DIMENSION}")
    print("=======================================================\n")

    if args.cli:
        run_cli_interactive()
    else:
        logger.info(f"Launching Uvicorn server on http://{args.host}:{args.port}")
        uvicorn.run(
            "app.main_app:app",
            host=args.host,
            port=args.port,
            reload=AppConfig.API_RELOAD,
            workers=AppConfig.API_WORKERS if not AppConfig.API_RELOAD else 1
        )


if __name__ == "__main__":
    main()
