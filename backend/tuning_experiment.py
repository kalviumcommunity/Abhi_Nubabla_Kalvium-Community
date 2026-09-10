"""
Root entry point for Retrieval Settings Tuning Experiment & Relevance Benchmarking.
Forwards execution to src.tuning_experiment.
"""

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.tuning_experiment import main

if __name__ == "__main__":
    main()
