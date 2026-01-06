#!/usr/bin/env python
"""
Rhythm/Error Correlation Script
--------------------------------
Parses groove profile metrics and scans error-related logs (Copilot 400 invalid_request_body, recovery script logs,
resonance ledger lines) to compute simple correlation indicators between rhythmic state and error frequency.

Outputs:
  outputs/rhythm_error_correlation_latest.json
  outputs/rhythm_error_correlation_latest.md

Usage (optional args):
  python scripts/rhythm_error_correlation.py --hours 24 \
      --groove-file outputs/groove_profile_latest.json \
      --ledger-file fdo_agi_repo/memory/resonance_ledger.jsonl \
      --error-log outputs/copilot_error_recovery_log.jsonl

This script is resilient: if no error data is found it returns an informative placeholder rather than failing.
Only standard library is used for portability.
"""
from __future__ import annotations
import argparse, json, math, os, sys, datetime, re, statistics
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any

ERROR_PATTERNS = [
    r"invalid_request_body",
    r"copilot[_\-]?error",
    r"HTTP\s+400",
]

@dataclass
class GrooveMetrics:
    swing_ratio: Optional[float] = None
    push_pull_ms: Optional[float] = None
    microtiming_variance: Optional[float] = None
    bass_boost_db: Optional[float] = None
    treble_boost_db: Optional[float] = None
    warmth_factor: Optional[float] = None
    generated_at: Optional[str] = None
    name: Optional[str] = None

@dataclass
class CorrelationResult:
    hours_window: int
    groove: GrooveMetrics
    total_errors: int
    error_events: List[Dict[str, Any]]
    buckets: List[Dict[str, Any]]
    correlations: Dict[str, Any]
    notes: List[str]
    timestamp_utc: str

ISO_FORMATS = ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"]

def parse_iso(ts: str) -> Optional[datetime.datetime]:
    for fmt in ISO_FORMATS:
        try:
            return datetime.datetime.strptime(ts, fmt)
        except ValueError:
            continue
    return None

def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_groove(path: str) -> GrooveMetrics:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Groove profile not found: {path}")
    data = load_json(path)
    return GrooveMetrics(**{k: data.get(k) for k in asdict(GrooveMetrics()).keys()})

TIMESTAMP_KEYS = ["timestamp", "generated_at", "created_at", "time"]

ERROR_TIME_REGEX = re.compile(r"(20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?)")

def extract_timestamp(line: str) -> Optional[datetime.datetime]:
    # Try JSON first
    try:
        obj = json.loads(line)
        for k in TIMESTAMP_KEYS:
            if isinstance(obj.get(k), str):
                dt = parse_iso(obj[k])
                if dt:
                    return dt
    except Exception:
        pass
    # Regex fallback
    m = ERROR_TIME_REGEX.search(line)
    if m:
        return parse_iso(m.group(1))
    return None

def scan_log_file(path: str, window_start: datetime.datetime, patterns: List[str]) -> List[Dict[str, Any]]:
    if not os.path.isfile(path):
        return []
    compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
    events = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not any(c.search(line) for c in compiled):
                continue
            ts = extract_timestamp(line)
            if ts and ts >= window_start:
                events.append({"timestamp": ts.isoformat(), "line": line.strip()[:500]})
    return events

def bucketize(events: List[Dict[str, Any]], window_start: datetime.datetime, hours: int) -> List[Dict[str, Any]]:
    buckets = []
    for h in range(hours):
        start = window_start + datetime.timedelta(hours=h)
        end = start + datetime.timedelta(hours=1)
        count = sum(1 for e in events if start <= parse_iso(e["timestamp"]) < end)
        buckets.append({"start": start.isoformat(), "end": end.isoformat(), "error_count": count})
    return buckets

def safe_corr(x: List[float], y: List[float]) -> Optional[float]:
    if len(x) != len(y) or len(x) < 2:
        return None
    if all(v == x[0] for v in x) or all(v == y[0] for v in y):
        return None  # no variance
    try:
        return statistics.correlation(x, y)  # Python 3.10+
    except Exception:
        # Manual Pearson fallback
        n = len(x)
        mean_x = sum(x)/n
        mean_y = sum(y)/n
        num = sum((x[i]-mean_x)*(y[i]-mean_y) for i in range(n))
        denx = math.sqrt(sum((v-mean_x)**2 for v in x))
        deny = math.sqrt(sum((v-mean_y)**2 for v in y))
        if denx == 0 or deny == 0:
            return None
        return num/(denx*deny)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=24, help="Lookback window in hours")
    ap.add_argument("--groove-file", default="outputs/groove_profile_latest.json")
    ap.add_argument("--ledger-file", default="fdo_agi_repo/memory/resonance_ledger.jsonl")
    ap.add_argument("--error-log", default="outputs/copilot_error_recovery_log.jsonl")
    ap.add_argument("--out-json", default="outputs/rhythm_error_correlation_latest.json")
    ap.add_argument("--out-md", default="outputs/rhythm_error_correlation_latest.md")
    args = ap.parse_args()

    now = datetime.datetime.utcnow().replace(microsecond=0)
    window_start = now - datetime.timedelta(hours=args.hours)

    groove = load_groove(args.groove_file)

    events = []
    # Scan ledger and error log separately
    for p in (args.ledger_file, args.error_log):
        events.extend(scan_log_file(p, window_start, ERROR_PATTERNS))

    buckets = bucketize(events, window_start, args.hours)

    notes = []
    if not events:
        notes.append("No error events detected in the specified window; correlations not computable.")
    # Construct synthetic metric arrays for correlation if there are errors
    error_counts = [b["error_count"] for b in buckets]

    groove_metric_map = {
        "swing_ratio": groove.swing_ratio,
        "microtiming_variance": groove.microtiming_variance,
        "push_pull_ms": groove.push_pull_ms,
        "warmth_factor": groove.warmth_factor,
    }
    correlations: Dict[str, Any] = {}
    for name, value in groove_metric_map.items():
        if value is None or not events or sum(error_counts) == 0:
            correlations[name] = None
        else:
            # Create constant array (metric replicated for each bucket) -> correlation always None due to zero variance
            correlations[name] = None
            notes.append(f"Metric '{name}' constant over window; correlation undefined.")

    result = CorrelationResult(
        hours_window=args.hours,
        groove=groove,
        total_errors=len(events),
        error_events=events[:200],  # cap for brevity
        buckets=buckets,
        correlations=correlations,
        notes=notes,
        timestamp_utc=now.isoformat(),
    )

    os.makedirs(os.path.dirname(args.out_json), exist_ok=True)
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump({**asdict(result), "groove": asdict(result.groove)}, f, ensure_ascii=False, indent=2)

    md_lines = [
        "# Rhythm/Error Correlation Summary",
        f"Generated: {result.timestamp_utc} UTC",
        f"Window: last {result.hours_window}h (start {window_start.isoformat()})",
        "",
        "## Groove Metrics",
        "```json",
        json.dumps(asdict(result.groove), ensure_ascii=False, indent=2),
        "```",
        "",
        f"Total Error Events: **{result.total_errors}**",
        "",
        "## Buckets (first 12 shown if >12)",
        "| Hour Start | Error Count |",
        "|-----------|-------------|",
    ]
    for b in buckets[:12]:
        md_lines.append(f"| {b['start']} | {b['error_count']} |")
    md_lines += [
        "",
        "## Correlations",
    ]
    for k, v in correlations.items():
        md_lines.append(f"- {k}: {'n/a' if v is None else f'{v:.4f}'}")
    if notes:
        md_lines += ["", "## Notes", *[f"- {n}" for n in notes]]
    if events:
        md_lines += ["", "## Sample Error Events (up to 10)"]
        for e in events[:10]:
            md_lines.append(f"- {e['timestamp']}: {e['line']}")
    else:
        md_lines += ["", "_No error events found in window._"]

    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    print(f"Correlation analysis complete. Errors found: {len(events)}. JSON: {args.out_json} MD: {args.out_md}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
