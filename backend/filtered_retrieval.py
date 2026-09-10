"""
Root entry point for the Metadata Filtering & Hybrid Vector Retrieval Engine.
Forwards execution to src.filtered_retrieval.
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.filtered_retrieval import (
    main,
    FilteredRetriever,
    MetadataFilter,
    HybridScorer,
    run_filtered_retrieval_benchmark,
)

if __name__ == "__main__":
    main()
