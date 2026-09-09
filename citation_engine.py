#!/usr/bin/env python3
"""
Root entry point for Verifiable Source Citations and Metadata Attribution Engine.
Delegates directly to src.citation_engine.main().
"""

import sys
from pathlib import Path

# Ensure workspace root is on Python module search path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from src.citation_engine import main

if __name__ == "__main__":
    main()
