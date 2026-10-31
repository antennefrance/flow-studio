#!/usr/bin/env python3
"""Project FLOW Studio Entrypoint (Backward Compatibility Bridge).

Delegates execution to the refactored, cleanly structured flow_studio package.
"""

import sys
from pathlib import Path

# Ensure root directory is on PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent))

from flow_studio.main import main

if __name__ == "__main__":
    main()
