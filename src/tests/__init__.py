"""Test package configuration for campus simulation."""

from __future__ import annotations

import pathlib
import sys

# Ensure the project src directory is available for imports when running tests
PROJECT_SRC = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_SRC) not in sys.path:
	sys.path.insert(0, str(PROJECT_SRC))
