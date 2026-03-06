"""Standalone entry point — adds src/ to path so the package can be
imported without installing it.  Used by run.sh (WSL → Windows python.exe).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from idle_boss_rush_auto_freeze.__main__ import main

if __name__ == "__main__":
    main()
