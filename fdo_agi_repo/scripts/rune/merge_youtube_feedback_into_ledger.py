#!/usr/bin/env python3
"""
Merge youtube_feedback_bqi.jsonl into a (shadow) resonance ledger JSONL.

Default (safe): writes to outputs/resonance_ledger_youtube_augmented.jsonl
Use --to-main-ledger to append into memory/resonance_ledger.jsonl (use with care).

For each record, emits 2-3 events aligned with existing ledger schema:
  - run_config: contains bqi_coord and task_id
  - eval:      quality score
  - meta_cognition: confidence score
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

ROOT = Path(__file__).resolve().parents[2]  # .../fdo_agi_repo
IN_JSONL = ROOT / "outputs" / "youtube_feedback_bqi.jsonl"
SHADOW_LEDGER = ROOT / "outputs" / "resonance_ledger_youtube_augmented.jsonl"
MAIN_LEDGER = ROOT / "memory" / "resonance_ledger.jsonl"


def append_jsonl(path: Path, obj: Dict[str, Any]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--to-main-ledger", action="store_true", help="append into memory/resonance_ledger.jsonl")
    ap.add_argument("--input", default=str(IN_JSONL), help="youtube_feedback_bqi.jsonl path")
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"[YouTube→Ledger] Input not found: {in_path}")
        return 1

    out_path = MAIN_LEDGER if args.to_main_ledger else SHADOW_LEDGER

    added = 0
    with in_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            ts = rec.get("ts") or datetime.now(timezone.utc).isoformat()
            task_id = rec.get("task_id") or "yt-unknown"
            bqi_coord = rec.get("bqi_coord") or {"priority": 2, "emotion": ["curious"], "rhythm": "observe"}
            quality = rec.get("quality", 0.5)
            confidence = rec.get("confidence", 0.5)
            meta = rec.get("meta", {})

            # Emit run_config
            append_jsonl(out_path, {
                "event": "run_config",
                "ts": ts,
                "task_id": task_id,
                "bqi_coord": bqi_coord,
                "source": "youtube",
                "meta": meta
            })

            # Emit eval
            append_jsonl(out_path, {
                "event": "eval",
                "ts": ts,
                "task_id": task_id,
                "quality": float(quality),
                "source": "youtube"
            })

            # Emit meta_cognition
            append_jsonl(out_path, {
                "event": "meta_cognition",
                "ts": ts,
                "task_id": task_id,
                "confidence": float(confidence),
                "source": "youtube"
            })

            added += 3

    print(f"[YouTube→Ledger] Appended {added} events → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
