#!/usr/bin/env python3
"""
Root entry point for Full RAG System Evaluation & Answer Quality Scoring.
Delegates directly to src.rag_evaluator.main().
"""

import sys
from pathlib import Path

# Ensure workspace root is on Python module search path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from src.rag_evaluator import main

if __name__ == "__main__":
    main()
