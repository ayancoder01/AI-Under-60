"""Test suite for AI Under 60."""

from pathlib import Path
import sys

# Ensure src directory is in sys.path for test discovery
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
