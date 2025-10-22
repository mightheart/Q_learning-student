"""Quick launcher for the campus simulation."""

import sys
from pathlib import Path

# Ensure src is in path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import and run main
from main import main

if __name__ == "__main__":
    main()
