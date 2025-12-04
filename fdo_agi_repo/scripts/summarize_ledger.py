from __future__ import annotations
import os
import sys
import json
import time
import argparse
import shutil
from typing import Any, Dict, Iterable, List, Sequence, Tuple

HERE = os.path.dirname(__file__)
REPO = os.path.dirname(HERE)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from orchestrator.memory_bus import LEDGER_PATH, COORD_PATH

DEFAULT_EXCLUDE_PREFIXES: Tuple[str, ...] = (
    "integration_test_",
    "low_confidence_test_",
    "temp_low_conf_",
)


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                # skip broken lines
                pass
    return out


def _within_window(ts: float, cutoff: float) -> bool:
    try:
        return float(ts) >= cutoff
    except Exception:
        return False


def _avg(values: Iterable[float]) -> float:
    vs = [v for v in values if isinstance(v, (int, float))]
    return (sum(vs) / len(vs)) if vs else 0.0


def _matches_prefix(task_id: str | None, prefixes: Sequence[str]) -> bool:
    if not prefixes or not task_id:
        return False
    return any(task_id.startswith(prefix) for prefix in prefixes)


def _is_excluded(event: Dict[str, Any], prefixes: Sequence[str]) -> bool:
    if not prefixes:
        return False

    task_id = event.get("task_id")
    if not task_id:
        task = event.get("task")
        if isinstance(task, dict):
            task_id = task.get("task_id")
    return _matches_prefix(task_id, prefixes)


def summarize(
    last_hours: float = 24.0,
    exclude_prefixes: Sequence[str] | None = None,
    include_default_excludes: bool = True,
) -> Dict[str, Any]:
    now = time.time()
    cutoff = now - (last_hours * 3600.0) if last_hours and last_hours > 0 else 0

    ledger = [r for r in _read_jsonl(LEDGER_PATH) if cutoff == 0 or _within_window(r.get("ts", 0), cutoff)]
    coord = [r for r in _read_jsonl(COORD_PATH) if cutoff == 0 or _within_window(r.get("ts", 0), cutoff)]

    combined: List[str] = []
    if include_default_excludes:
        combined.extend(DEFAULT_EXCLUDE_PREFIXES)
    if exclude_prefixes:
        combined.extend(exclude_prefixes)
    # preserve order and remove duplicates
    seen = dict.fromkeys(combined)
    prefixes: Tuple[str, ...] = tuple(seen.keys())
    if prefixes:
        ledger = [e for e in ledger if not _is_excluded(e, prefixes)]
        coord = [e for e in coord if not _is_excluded(e, prefixes)]

    # Event counts
    event_counts: Dict[str, int] = {}
    for e in ledger:
        ev = e.get("event")
        if not ev:
            continue
        event_counts[ev] = event_counts.get(ev, 0) + 1

    # Confidence / quality
    confidences: List[float] = []
    for e in ledger:
        if e.get("event") == "meta_cognition":
            c = e.get("confidence")
            if isinstance(c, (int, float)):
                confidences.append(float(c))

    qualities: List[float] = []
    for e in ledger:
        if e.get("event") == "eval":
            q = e.get("quality")
            if isinstance(q, (int, float)):
                qualities.append(float(q))

    # Task starts/ends (coordinate)
    starts = [e for e in coord if e.get("event") == "task_start"]
    ends = [e for e in coord if e.get("event") == "task_end"]

    # Distinct task IDs (coord only)
    started_ids = {e.get("task_id") for e in starts if e.get("task_id")}
    ended_ids = {e.get("task_id") for e in ends if e.get("task_id")}

    completion_rate = (len(ended_ids) / len(started_ids)) if started_ids else None
    if isinstance(completion_rate, float) and completion_rate > 1.0:
        completion_rate = 1.0

    # Second pass count
    second_pass = event_counts.get("second_pass", 0)

    # Distinct task IDs (ledger fallback)
    ledger_task_ids = {e.get("task_id") for e in ledger if e.get("task_id")}
    second_pass_rate_per_task = (second_pass / len(ledger_task_ids)) if ledger_task_ids else None

    result: Dict[str, Any] = {
        "window_hours": last_hours,
        "now": now,
        "counts": {
            "events": event_counts,
            "tasks_started": len(starts),
            "tasks_ended": len(ends),
            "distinct_tasks_started": len(started_ids),
            "distinct_tasks_ended": len(ended_ids),
        },
        "metrics": {
            "avg_confidence": round(_avg(confidences), 3) if confidences else None,
            "avg_quality": round(_avg(qualities), 3) if qualities else None,
            "second_pass_total": second_pass,
        },
        "notes": {
            "paths": {
                "ledger": LEDGER_PATH,
                "coordinate": COORD_PATH,
            },
            "exclude_prefixes": list(prefixes),
            "default_excludes_applied": include_default_excludes,
        },
    }
    if completion_rate is not None:
        result["metrics"]["completion_rate"] = round(completion_rate, 3)
    if second_pass_rate_per_task is not None:
        result["metrics"]["second_pass_rate_per_task"] = round(second_pass_rate_per_task, 3)
    return result


def write_outputs(summary: Dict[str, Any]) -> Tuple[str, str, str, str]:
    out_dir = os.path.join(REPO, "outputs")
    os.makedirs(out_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S", time.localtime(summary.get("now", time.time())))

    json_path = os.path.join(out_dir, f"ledger_summary_{ts}.json")
    md_path = os.path.join(out_dir, f"ledger_summary_{ts}.md")

    # JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # Markdown
    lines: List[str] = []
    lines.append(f"# Ledger Summary (last {summary.get('window_hours')}h)")
    lines.append("")
    lines.append(f"- Generated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(summary.get('now', time.time())))}")
    lines.append(f"- Ledger: {summary['notes']['paths']['ledger']}")
    lines.append(f"- Coordinate: {summary['notes']['paths']['coordinate']}")
    lines.append("")
    if summary["notes"].get("exclude_prefixes"):
        lines.append(f"- Excluded prefixes: {summary['notes']['exclude_prefixes']}")
        lines.append("")
    lines.append("## Counts")
    lines.append("")
    counts = summary["counts"]
    lines.append(f"- Events: {json.dumps(counts['events'], ensure_ascii=False)}")
    lines.append(f"- Tasks started (records): {counts['tasks_started']}")
    lines.append(f"- Tasks ended (records): {counts['tasks_ended']}")
    lines.append(f"- Distinct tasks started: {counts['distinct_tasks_started']}")
    lines.append(f"- Distinct tasks ended: {counts['distinct_tasks_ended']}")
    lines.append("")
    lines.append("## Metrics")
    lines.append("")
    for k, v in summary["metrics"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # Also write/update latest pointers
    latest_json = os.path.join(out_dir, "ledger_summary_latest.json")
    latest_md = os.path.join(out_dir, "ledger_summary_latest.md")
    try:
        shutil.copyfile(json_path, latest_json)
        shutil.copyfile(md_path, latest_md)
    except Exception:
        # non-fatal
        pass

    return json_path, md_path, latest_json, latest_md


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Summarize AGI ledger for a recent time window")
    p.add_argument("--last-hours", type=float, default=24.0, help="Time window in hours (default: 24)")
    p.add_argument(
        "--exclude-prefix",
        action="append",
        default=[],
        help="Exclude tasks whose task_id starts with the given prefix (use multiple times for multiple prefixes)",
    )
    p.add_argument(
        "--no-default-excludes",
        action="store_true",
        help="Disable built-in regression prefixes (integration_test_*, low_confidence_test_*, temp_low_conf_)",
    )
    args = p.parse_args(argv)

    sm = summarize(
        last_hours=args.last_hours,
        exclude_prefixes=args.exclude_prefix,
        include_default_excludes=not args.no_default_excludes,
    )
    json_path, md_path, latest_json, latest_md = write_outputs(sm)
    # Print compact JSON for callers
    print(json.dumps({
        "ok": True,
        "json": json_path,
        "md": md_path,
        "latest_json": latest_json,
        "latest_md": latest_md,
        "metrics": sm.get("metrics", {}),
        "counts": sm.get("counts", {}),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
