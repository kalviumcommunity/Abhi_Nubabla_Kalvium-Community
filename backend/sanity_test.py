"""
Root entry point for the Retrieval Sanity-Testing & Quality Check Suite.
Forwards execution to src.sanity_test.
"""

import sys
from pathlib import Path

# Add project root and src to sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.sanity_test import main

if __name__ == "__main__":
    main()
