"""
Run one cycle of the Self-Expansion Engine.

Usage:
    python scripts/self_expansion/run_engine_once.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]  # c:/workspace/agi
sys.path.append(str(ROOT))

from scripts.self_expansion import SelfExpansionEngine


def main():
    engine = SelfExpansionEngine(ROOT)
    result = engine.run_once()
    print(result)


if __name__ == "__main__":
    main()
