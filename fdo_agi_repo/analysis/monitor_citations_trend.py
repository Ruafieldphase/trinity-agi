#!/usr/bin/env python3
"""
Monitor citations/replan/quality trends over recent hours and output JSON summary.
Usage:
  python monitor_citations_trend.py --hours 24 --out ../../outputs/citations_summary.json
Defaults:
  hours=24, out=../../outputs/citations_summary.json
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

LEDGER_PATH = Path(__file__).parent.parent / "memory" / "resonance_ledger.jsonl"


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--out", type=str, default=str(Path(__file__).parents[2] / "outputs" / "citations_summary.json"))
    return ap.parse_args()


def load_events():
    events = []
    if not LEDGER_PATH.exists():
        return events
    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception:
                pass
    return events


def within_window(ev, since_dt):
    ts = ev.get("timestamp")
    if not ts:
        return True  # if missing, keep
    try:
        # tolerate both "2025-10-27T11:45:23.123456" and similar
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt >= since_dt
    except Exception:
        return True


def summarize(events, hours: int):
    now = datetime.now()
    since = now - timedelta(hours=hours)

    # task_id -> aggregate fields
    tasks = {}
    for ev in events:
        if not within_window(ev, since):
            continue
        tid = ev.get("task_id")
        if not tid:
            continue
        t = tasks.setdefault(tid, {
            "task_id": tid,
            "thesis_citations": None,
            "synthesis_citations": None,
            "quality": None,
            "evidence_ok": None,
            "replan": None,
        })
        et = ev.get("event")
        if et == "thesis_end" and "citations" in ev:
            t["thesis_citations"] = ev["citations"]
        elif et == "synthesis_end" and "citations" in ev:
            t["synthesis_citations"] = ev["citations"]
        elif et == "eval":
            t["quality"] = ev.get("quality")
            t["evidence_ok"] = ev.get("evidence_ok")
        elif et == "rune":
            t["replan"] = (ev.get("rune", {}) or {}).get("replan")

    improved = [t for t in tasks.values() if t["thesis_citations"] is not None]
    completed = [t for t in improved if t["replan"] is not None]
    replans = [t for t in completed if t["replan"]]
    noreplans = [t for t in completed if t["replan"] is False]

    def avg(vals):
        vals = [v for v in vals if isinstance(v, (int, float))]
        return (sum(vals) / len(vals)) if vals else 0.0

    summary = {
        "window_hours": hours,
        "generated_at": now.isoformat(),
        "counts": {
            "tasks_total": len(tasks),
            "improved_with_citations": len(improved),
            "completed": len(completed),
            "replans": len(replans),
            "noreplans": len(noreplans),
            "pending": len(improved) - len(completed),
        },
        "rates": {
            "replan_rate": (len(replans) / len(completed) * 100.0) if completed else 0.0,
            "evidence_ok_rate": (sum(1 for t in noreplans if t.get("evidence_ok")) / len(noreplans) * 100.0) if noreplans else 0.0,
        },
        "citations": {
            "thesis_avg": avg([t.get("thesis_citations") for t in improved]),
            "synthesis_avg": avg([t.get("synthesis_citations") for t in improved]),
        },
        "quality": {
            "noreplan_avg": avg([t.get("quality") for t in noreplans]),
        },
        "samples": noreplans[:5],
    }
    return summary


def main():
    args = parse_args()
    events = load_events()
    summary = summarize(events, args.hours)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
