#!/usr/bin/env python3
"""
Generate a compact Phase 6.12 feedback integration report from JSONL inputs.
Reads:
  - outputs/youtube_feedback_bqi.jsonl (optional)
  - outputs/rpa_feedback_bqi.jsonl (optional)
Writes:
  - outputs/phase_6_12_report.md
"""
from __future__ import annotations
import json
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[2]
YT = ROOT / "outputs" / "youtube_feedback_bqi.jsonl"
RPA = ROOT / "outputs" / "rpa_feedback_bqi.jsonl"
OUT = ROOT / "outputs" / "phase_6_12_report.md"


def load_jsonl(p: Path):
    items = []
    if not p.exists():
        return items
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                pass
    return items


def safe_mean(values):
    try:
        return mean(values) if values else 0.0
    except Exception:
        return 0.0


def main() -> int:
    yt = load_jsonl(YT)
    rpa = load_jsonl(RPA)

    yt_q = [float(x.get("quality", 0)) for x in yt]
    yt_c = [float(x.get("confidence", 0)) for x in yt]
    rpa_q = [float(x.get("quality", 0)) for x in rpa]
    rpa_c = [float(x.get("confidence", 0)) for x in rpa]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        f.write("# Phase 6.12 Feedback Integration Report\n\n")
        f.write("## YouTube Feedback\n")
        f.write(f"- Records: {len(yt)}\n")
        f.write(f"- Avg Quality: {safe_mean(yt_q):.3f}\n")
        f.write(f"- Avg Confidence: {safe_mean(yt_c):.3f}\n\n")
        f.write("## RPA Feedback\n")
        f.write(f"- Records: {len(rpa)}\n")
        f.write(f"- Avg Quality: {safe_mean(rpa_q):.3f}\n")
        f.write(f"- Avg Confidence: {safe_mean(rpa_c):.3f}\n\n")
        f.write("## Notes\n")
        f.write("- Shadow ledger augmented via run_config/eval/meta_cognition events.\n")
        f.write("- Heuristics v1: lightweight signals; refine with real outcomes.\n")
    print(f"[Summary] Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
