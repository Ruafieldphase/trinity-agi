#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sanitize resonance_ledger.jsonl by filtering or lightly repairing malformed JSON lines.

- Input (default): ../memory/resonance_ledger.jsonl
- Output: ../memory/resonance_ledger_clean.jsonl
- Bad lines: ../memory/resonance_ledger_bad_lines.txt (line_no \t reason \t raw)

Usage (Windows PowerShell):
  python scripts/sanitize_ledger.py
  python scripts/sanitize_ledger.py --in <path-to-ledger.jsonl> --out <clean.jsonl>

Design notes:
- We do not try to fix complex corruption. We attempt minimal fixes:
  * Strip UTF-8 BOM if present
  * Trim whitespace
  * Remove a trailing comma before a closing object/array (common copy artefact)
- If still invalid, we skip the line and record it in bad_lines file.
"""
from __future__ import annotations
import argparse
import io
import json
import os
import re
from typing import Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_IN = os.path.abspath(os.path.join(HERE, "..", "memory", "resonance_ledger.jsonl"))
DEFAULT_OUT = os.path.abspath(os.path.join(HERE, "..", "memory", "resonance_ledger_clean.jsonl"))
DEFAULT_BAD = os.path.abspath(os.path.join(HERE, "..", "memory", "resonance_ledger_bad_lines.txt"))

TRAILING_COMMA_OBJ = re.compile(r",\s*}\s*$")
TRAILING_COMMA_ARR = re.compile(r",\s*]\s*$")


def try_minimal_fix(line: str) -> str:
    # Remove BOM and strip whitespace
    s = line.lstrip("\ufeff").strip()
    if not s:
        return s
    # Remove trailing comma before } or ]
    s = TRAILING_COMMA_OBJ.sub("}", s)
    s = TRAILING_COMMA_ARR.sub("]", s)
    return s


def process(in_path: str, out_path: str, bad_path: str) -> Tuple[int, int, int]:
    total = 0
    kept = 0
    bad = 0
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with io.open(in_path, "r", encoding="utf-8", errors="replace") as fin, \
         io.open(out_path, "w", encoding="utf-8", newline="\n") as fout, \
         io.open(bad_path, "w", encoding="utf-8", newline="\n") as fbad:
        for idx, raw in enumerate(fin, start=1):
            total += 1
            s = try_minimal_fix(raw)
            if not s:
                # empty after strip; skip silently but record
                bad += 1
                fbad.write(f"{idx}\tempty_or_whitespace\t{raw}\n")
                continue
            try:
                obj = json.loads(s)
            except Exception as e:
                bad += 1
                fbad.write(f"{idx}\t{type(e).__name__}: {str(e)}\t{s}\n")
                continue
            # Write as normalized JSON (compact) to reduce drift
            fout.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")
            kept += 1
    return total, kept, bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", default=DEFAULT_IN, help="Input ledger .jsonl path")
    ap.add_argument("--out", dest="out_path", default=DEFAULT_OUT, help="Output cleaned .jsonl path")
    ap.add_argument("--bad", dest="bad_path", default=DEFAULT_BAD, help="Output bad lines report path")
    args = ap.parse_args()

    if not os.path.exists(args.in_path):
        print(f"[sanitize_ledger] Input not found: {args.in_path}")
        return 1

    total, kept, bad = process(args.in_path, args.out_path, args.bad_path)
    print(f"[sanitize_ledger] Total lines: {total}")
    print(f"[sanitize_ledger] Kept (valid): {kept}")
    print(f"[sanitize_ledger] Skipped (bad): {bad}")
    if total > 0:
        print(f"[sanitize_ledger] Valid ratio: {kept/total:.2%}")
    print(f"[sanitize_ledger] Clean file: {args.out_path}")
    print(f"[sanitize_ledger] Bad lines: {args.bad_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
