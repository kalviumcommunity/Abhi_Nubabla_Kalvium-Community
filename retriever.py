"""
Root entry point for the RAG Top-K Vector Store Retriever Module.
Forwards execution to src.retriever.
"""

import sys
from pathlib import Path

# Add project root and src to sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.retriever import main, VectorStoreRetriever, DenseSemanticEmbedder, cosine_similarity

if __name__ == "__main__":
    main()
