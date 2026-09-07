"""
Root entry point for End-to-End Grounded RAG Pipeline Architecture.
Forwards execution to src.rag_pipeline.
"""

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.rag_pipeline import main

if __name__ == "__main__":
    main()
