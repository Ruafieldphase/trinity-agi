#!/usr/bin/env python3
"""
Summarize outputs/core_probe_log.jsonl into ASCII-safe digest and JSON.

Metrics over a sliding window (default 24h):
- success_rate, count, last_status, last_ok, p50/p95 latency, avg latency

Outputs:
- outputs/core_probe_summary_latest.json
- outputs/core_probe_summary_latest.md (ASCII digest)
"""
import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean
from typing import List, Dict, Any
from workspace_root import get_workspace_root


ROOT = get_workspace_root()
LOG = ROOT / "outputs" / "core_probe_log.jsonl"
OUT_JSON = ROOT / "outputs" / "core_probe_summary_latest.json"
OUT_MD = ROOT / "outputs" / "core_probe_summary_latest.md"


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=24)
    return ap.parse_args()


@dataclass
class Rec:
    ts: datetime
    ok: bool
    ms: int
    status: int | None
    url: str | None
    method: str | None
    tag: str | None


def load(last_hours: int) -> List[Rec]:
    since = datetime.utcnow() - timedelta(hours=last_hours)
    out: List[Rec] = []
    if not LOG.exists():
        return out
    with LOG.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                j = json.loads(line)
            except Exception:
                continue
            ts_s = j.get("ts")
            try:
                ts = datetime.fromisoformat(str(ts_s).replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                ts = datetime.utcnow()
            if ts < since:
                continue
            out.append(
                Rec(
                    ts=ts,
                    ok=bool(j.get("ok")),
                    ms=int(j.get("ms") or 0),
                    status=(int(j.get("status")) if j.get("status") is not None else None),
                    url=(j.get("url") or None),
                    method=(j.get("method") or None),
                    tag=(j.get("tag") or None),
                )
            )
    out.sort(key=lambda r: r.ts)
    return out


def percentile(data: List[float], p: float) -> float:
    if not data:
        return 0.0
    data = sorted(data)
    k = int(round((p / 100.0) * (len(data)))) - 1
    k = max(0, min(k, len(data) - 1))
    return float(data[k])


def to_summary(recs: List[Rec], hours: int) -> Dict[str, Any]:
    if not recs:
        return {
            "hours": hours,
            "count": 0,
            "success_rate": 0.0,
            "last_ok": None,
            "last_status": None,
            "p50_ms": 0.0,
            "p95_ms": 0.0,
            "avg_ms": 0.0,
        }
    oks = [r for r in recs if r.ok]
    ms_vals = [float(r.ms) for r in recs if r.ms is not None]
    last = recs[-1]
    return {
        "hours": hours,
        "count": len(recs),
        "success_rate": (len(oks) / len(recs) * 100.0) if recs else 0.0,
        "last_ok": last.ok,
        "last_status": last.status,
        "p50_ms": percentile(ms_vals, 50.0),
        "p95_ms": percentile(ms_vals, 95.0),
        "avg_ms": mean(ms_vals) if ms_vals else 0.0,
        "last_ts": last.ts.isoformat(),
        "last_url": last.url,
        "last_method": last.method,
        "last_tag": last.tag,
    }


def write_outputs(summary: Dict[str, Any]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    # JSON
    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    # MD
    lines: List[str] = []
    lines.append("[Core PROBE SUMMARY - ASCII SAFE]")
    lines.append("")
    lines.append(f"- Window: last {summary.get('hours')} hours")
    lines.append(f"- Count: {summary.get('count')}")
    lines.append(f"- Success rate: {summary.get('success_rate', 0.0):.1f}%")
    lines.append(
        f"- Latency ms: p50={summary.get('p50_ms',0.0):.0f}  p95={summary.get('p95_ms',0.0):.0f}  avg={summary.get('avg_ms',0.0):.0f}"
    )
    lines.append(
        f"- Last: ok={summary.get('last_ok')} status={summary.get('last_status')} at {summary.get('last_ts','')}"
    )
    url = summary.get("last_url") or ""
    if url:
        lines.append(f"- URL: {url}")
    tag = summary.get("last_tag") or ""
    if tag:
        lines.append(f"- Tag: {tag}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("Append-only log: outputs/core_probe_log.jsonl")
    with OUT_MD.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    args = parse_args()
    recs = load(args.hours)
    summary = to_summary(recs, args.hours)
    write_outputs(summary)
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

