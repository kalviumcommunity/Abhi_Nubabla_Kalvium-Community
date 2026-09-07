#!/usr/bin/env python3
"""
Root CLI entry point for the Grounded Answer Generation & Source Accuracy Verification Engine.

Usage:
    python generate_grounded_answer.py [OPTIONS]

Options:
    --query TEXT           Generate a grounded answer for a single query
    --compare-unretrieved  Run side-by-side comparison with vs without retrieval
    --fallback-test        Test missing-context fallback refusal mechanism
    --benchmark            Run full benchmark suite and export reports
    --k INT                Number of chunks to retrieve (default: 3)
    --vector-store PATH    Path to embedded chunks JSON (default: data/embedded_chunks.json)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.grounded_generator import main

if __name__ == "__main__":
    main()
