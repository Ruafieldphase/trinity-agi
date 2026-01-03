"""
Run one cycle of the Self-Expansion Engine.

Usage:
    python scripts/self_expansion/run_engine_once.py
"""
from pathlib import Path
import sys
from workspace_root import get_workspace_root
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


ROOT = get_workspace_root()  # c:/workspace/agi
sys.path.append(str(ROOT))

from scripts.self_expansion import SelfExpansionEngine


def main():
    engine = SelfExpansionEngine(ROOT)
    result = engine.run_once()
    print(result)


if __name__ == "__main__":
    main()
