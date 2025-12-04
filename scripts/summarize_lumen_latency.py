#!/usr/bin/env python3
import argparse
import json
import os
import statistics
from datetime import datetime
from typing import Any, Dict, List, Optional


def load_jsonl(path: str, debug: bool = False) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    if not os.path.exists(path):
        if debug:
            print(f"DEBUG load_jsonl: Path does not exist: {path}")
        return records
    # Use utf-8-sig to handle BOM if present
    with open(path, 'r', encoding='utf-8-sig') as f:
        content = f.read().strip()
        if debug:
            print(f"DEBUG load_jsonl: Read {len(content)} chars")
            print(f"DEBUG load_jsonl: Content preview: {content[:200]}")
        if not content:
            if debug:
                print("DEBUG load_jsonl: Empty content")
            return records
        
        # Try to parse as single JSON object first (PowerShell format)
        try:
            obj = json.loads(content)
            if isinstance(obj, dict):
                records.append(obj)
                if debug:
                    print(f"DEBUG load_jsonl: Parsed as single JSON object")
                return records
            elif isinstance(obj, list):
                records.extend([r for r in obj if isinstance(r, dict)])
                if debug:
                    print(f"DEBUG load_jsonl: Parsed as JSON array, {len(records)} dicts")
                return records
        except Exception as e:
            if debug:
                print(f"DEBUG load_jsonl: Not a single JSON object: {e}")
        
        # Fall back to line-by-line JSONL parsing
        for i, line in enumerate(content.split('\n')):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    records.append(obj)
                    if debug:
                        print(f"DEBUG load_jsonl: Parsed line {i+1} as dict")
            except Exception as e:
                # skip bad line
                if debug:
                    print(f"DEBUG load_jsonl: Failed to parse line {i+1}: {e}")
                continue
    if debug:
        print(f"DEBUG load_jsonl: Total records: {len(records)}")
    return records


def pct(values: List[float], p: float) -> Optional[float]:
    if not values:
        return None
    values_sorted = sorted(values)
    k = (len(values_sorted) - 1) * p
    f = int(k)
    c = min(f + 1, len(values_sorted) - 1)
    if f == c:
        return float(values_sorted[int(k)])
    d0 = values_sorted[f] * (c - k)
    d1 = values_sorted[c] * (k - f)
    return float(d0 + d1)


def summarize(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    latencies = [float(r.get('latencyMs')) for r in records if isinstance(r.get('latencyMs'), (int, float))]
    oks = [r for r in records if r.get('ok') is True]
    warns = [r for r in records if r.get('warn') is True]
    criticals = [r for r in records if r.get('critical') is True]
    total = len(records)
    last_ts = records[-1]['timestamp'] if records else None

    summary: Dict[str, Any] = {
        'count': total,
        'ok_count': len(oks),
        'warn_count': len(warns),
        'critical_count': len(criticals),
        'ok_pct': (len(oks) / total * 100.0) if total else None,
        'warn_pct': (len(warns) / total * 100.0) if total else None,
        'critical_pct': (len(criticals) / total * 100.0) if total else None,
        'last_timestamp': last_ts,
        'latency': {
            'min': min(latencies) if latencies else None,
            'max': max(latencies) if latencies else None,
            'avg': statistics.fmean(latencies) if latencies else None,
            'median': statistics.median(latencies) if latencies else None,
            'p90': pct(latencies, 0.90),
            'p95': pct(latencies, 0.95),
            'p99': pct(latencies, 0.99),
        }
    }
    return summary


def format_source_path(path: str) -> str:
    norm = os.path.normpath(path)
    try:
        rel = os.path.relpath(norm, start=os.getcwd())
        if not rel.startswith('..'):
            return rel.replace('\\', '/')
    except ValueError:
        pass
    return norm.replace('\\', '/')


def to_markdown(summary: Dict[str, Any], source: str) -> str:
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lat = summary.get('latency') or {}
    def fmt(x: Any) -> str:
        return '-' if x is None else f"{x:.0f}"

    md = []
    md.append(f"# Lumen Latency Report")
    md.append("")
    md.append(f"Generated: {now}")
    md.append(f"Source: `{source}`")
    md.append("")
    md.append("## Summary")
    md.append("")
    md.append(f"- Records: {summary.get('count', 0)}")
    def fmt_pct(value: Optional[float]) -> str:
        return '-' if value is None else f"{value:.0f}%"

    md.append(
        "- OK: {ok_count} ({ok_pct})  |  Warn: {warn_count} ({warn_pct})  |  Critical: {critical_count} ({critical_pct})".format(
            ok_count=summary.get('ok_count', 0),
            warn_count=summary.get('warn_count', 0),
            critical_count=summary.get('critical_count', 0),
            ok_pct=fmt_pct(summary.get('ok_pct')),
            warn_pct=fmt_pct(summary.get('warn_pct')),
            critical_pct=fmt_pct(summary.get('critical_pct')),
        )
    )
    if summary.get('last_timestamp'):
        md.append(f"- Last Timestamp: {summary['last_timestamp']}")
    md.append("")
    md.append("## Latency (ms)")
    md.append("")
    md.append("| metric | value |")
    md.append("|---|---:|")
    md.append(f"| min | {fmt(lat.get('min'))} |")
    md.append(f"| p50 | {fmt(lat.get('median'))} |")
    md.append(f"| avg | {fmt(lat.get('avg'))} |")
    md.append(f"| p90 | {fmt(lat.get('p90'))} |")
    md.append(f"| p95 | {fmt(lat.get('p95'))} |")
    md.append(f"| p99 | {fmt(lat.get('p99'))} |")
    md.append(f"| max | {fmt(lat.get('max'))} |")
    md.append("")
    return "\n".join(md)


def main():
    ap = argparse.ArgumentParser(description='Summarize Lumen latency JSONL into Markdown and JSON.')
    ap.add_argument('--input', '-i', default='outputs/lumen_probe_history.jsonl', help='Input JSONL path')
    ap.add_argument('--out-md', default='outputs/lumen_latency_latest.md', help='Output Markdown path')
    ap.add_argument('--out-json', default='outputs/lumen_latency_summary.json', help='Output JSON summary path')
    ap.add_argument('--debug', action='store_true', help='Print debug information')
    args = ap.parse_args()

    if args.debug:
        print(f"DEBUG: Reading from {args.input}")
        print(f"DEBUG: File exists: {os.path.exists(args.input)}")
    
    records = load_jsonl(args.input, debug=args.debug)
    
    if args.debug:
        print(f"DEBUG: Loaded {len(records)} records")
        if records:
            print(f"DEBUG: First record: {records[0]}")
    
    if not records:
        # Write a minimal MD noting no data
        os.makedirs(os.path.dirname(args.out_md), exist_ok=True)
        with open(args.out_md, 'w', encoding='utf-8') as f:
            f.write('# Lumen Latency Report\n\n')
            f.write(f'Source: `{format_source_path(args.input)}`\n\n')
            f.write('No data available. Ensure history logging is enabled (non-DryRun).\n')
        # Also write empty summary JSON
        with open(args.out_json, 'w', encoding='utf-8') as f:
            json.dump({'count': 0, 'note': 'no data'}, f, ensure_ascii=False, indent=2)
        if args.debug:
            print(f"DEBUG: Wrote empty report to {args.out_md}")
        else:
            print(f"Wrote empty report to {args.out_md}")
        return 0

    summary = summarize(records)

    os.makedirs(os.path.dirname(args.out_md), exist_ok=True)
    with open(args.out_md, 'w', encoding='utf-8') as f:
        f.write(to_markdown(summary, format_source_path(args.input)))
    with open(args.out_json, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"Report written: {args.out_md}")
    print(f"Summary JSON: {args.out_json}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
