#!/usr/bin/env python3
"""
Root CLI entry point for the Conversational RAG Engine with Query Rewriting.

Usage:
    python conversational_rag.py [OPTIONS]

Options:
    --interactive         Start an interactive terminal multi-turn chat
    --benchmark           Run standard multi-turn benchmark suite and export reports
    --dialogue ID         Run a specific benchmark dialogue by ID
    --export-dir PATH     Output directory for JSON and Markdown reports (default: data)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.conversational_rag import main

if __name__ == "__main__":
    main()
