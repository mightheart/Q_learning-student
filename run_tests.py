"""Test runner script that ensures correct module paths."""

import sys
from pathlib import Path

# Add src directory to path before importing
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    import unittest

    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir="src/tests", pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
