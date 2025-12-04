"""
Deprecated probe script for ExecutionEngine.

This script was used for ad-hoc local probing and is now intentionally
disabled to avoid confusion. Please use the official test suite or VS Code
Tasks instead:

- VS Code Task: "Python: Run All Tests (repo venv)"
- Or run a specific test file under fdo_agi_repo/tests

Exiting with code 0.
"""

import sys

if __name__ == "__main__":
    sys.stdout.write("[info] tmp_probe_execution_engine.py is deprecated. Use the test suite.\n")
    sys.exit(0)
