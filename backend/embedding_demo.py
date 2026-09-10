"""
Root entry point for the Embedding Generation & Similarity Demonstration.
Forwards execution to src.embedding_demo.
"""

import sys
from pathlib import Path

# Add project root and src to sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.embedding_demo import main

if __name__ == "__main__":
    main()
