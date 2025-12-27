"""
Run Self-Expansion Engine in a loop (daemon-style).

Usage:
    python scripts/self_expansion/run_engine_daemon.py --interval 60
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # c:/workspace/agi
sys.path.append(str(ROOT))

from scripts.self_expansion import SelfExpansionEngine  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=60, help="Seconds between cycles")
    args = parser.parse_args()

    engine = SelfExpansionEngine(ROOT)
    while True:
        try:
            result = engine.run_once()
            print(result)
        except Exception as e:
            print(f"[SelfExpansion] error: {e}")
        time.sleep(max(1, args.interval))


if __name__ == "__main__":
    main()
