#!/usr/bin/env python3
"""
Run a single feedback integration pass:
  1) Convert YouTube learner analyses → youtube_feedback_bqi.jsonl
  2) Merge into shadow ledger
  3) Convert RPA queue results → rpa_feedback_bqi.jsonl
  4) Merge into shadow ledger

This is a one-shot prototype to validate the pipeline end-to-end.
"""
from __future__ import annotations
import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable


def run(cmd: list[str]) -> int:
    print("[loop] $", " ".join(cmd))
    return subprocess.call(cmd)


def main() -> int:
    # 1) YouTube → BQI
    yt_py = str(ROOT / "scripts" / "rune" / "youtube_feedback_to_bqi.py")
    rc = run([PY, yt_py])
    if rc != 0:
        print("[loop] WARN: youtube conversion failed")

    # 2) Merge YouTube → shadow ledger
    merge_py = str(ROOT / "scripts" / "rune" / "merge_youtube_feedback_into_ledger.py")
    yt_jsonl = str(ROOT / "outputs" / "youtube_feedback_bqi.jsonl")
    rc = run([PY, merge_py, "--input", yt_jsonl])
    if rc != 0:
        print("[loop] WARN: youtube merge failed")

    # 3) RPA → BQI
    rpa_py = str(ROOT / "scripts" / "rune" / "rpa_feedback_to_bqi.py")
    rc = run([PY, rpa_py, "--server", "http://127.0.0.1:8091", "--count", "50"])  # keep light
    if rc != 0:
        print("[loop] WARN: rpa conversion failed")

    # 4) Merge RPA → shadow ledger
    rpa_jsonl = str(ROOT / "outputs" / "rpa_feedback_bqi.jsonl")
    rc = run([PY, merge_py, "--input", rpa_jsonl])
    if rc != 0:
        print("[loop] WARN: rpa merge failed")

    # 5) Merge all augmented ledgers into canonical ledger
    merge_script = str(ROOT.parent / "scripts" / "merge_augmented_ledgers.ps1")
    rc = run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", merge_script])
    if rc != 0:
        print("[loop] WARN: augmented ledger merge failed")

    print("[loop] done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
