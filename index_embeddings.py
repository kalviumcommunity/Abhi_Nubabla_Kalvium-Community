"""
Root entry point for Vector Database Collection Indexing & Integrity Storage Engine.
Forwards execution to src.index_embeddings.
"""

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.index_embeddings import main

if __name__ == "__main__":
    main()
