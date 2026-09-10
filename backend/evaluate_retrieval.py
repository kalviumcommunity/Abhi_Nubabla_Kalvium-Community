#!/usr/bin/env python3
"""
Root entrypoint for the Staff RAG Assistant Retrieval Quality Evaluation Engine.

Usage:
    python evaluate_retrieval.py [OPTIONS]

Options:
    --data PATH            Path to embedded chunks JSON (default: data/results/embedded_chunks.json)
    --output-json PATH     Path to export results JSON (default: data/results/retrieval_evaluation_results.json)
    --output-report PATH   Path to export markdown report (default: data/results/retrieval_evaluation_report.md)
    --inspect              Print verbose failure inspection and diagnostic analysis
    --k-values 1 2 3 5 10  List of k thresholds for metric calculation
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.retrieval_evaluator import main

if __name__ == "__main__":
    main()
