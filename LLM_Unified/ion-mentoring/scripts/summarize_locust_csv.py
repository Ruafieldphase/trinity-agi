#!/usr/bin/env python3
"""Summarize Locust *_stats.csv files into a Markdown table."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

Metrics = Dict[str, Any]


def parse_stats_csv(path: Path) -> Metrics:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except FileNotFoundError:
        return {"_missing": True}

    if not rows:
        return {"_empty": True}

    last = rows[-1]

    def ffloat(key: str) -> float:
        raw = last.get(key, "")
        try:
            return float(raw) if raw not in (None, "") else 0.0
        except (TypeError, ValueError):
            return 0.0

    def fint(key: str) -> int:
        raw = last.get(key, "")
        try:
            return int(float(raw)) if raw not in (None, "") else 0
        except (TypeError, ValueError):
            return 0

    return {
        "requests": fint("Request Count"),
        "failures": fint("Failure Count"),
        "avg_ms": ffloat("Average Response Time"),
        "p50_ms": ffloat("50%"),
        "p95_ms": ffloat("95%"),
        "p99_ms": ffloat("99%"),
        "rps": ffloat("Requests/s"),
    }


def scenario_name_from_path(path: Path) -> str:
    stem = path.stem
    if stem.startswith("load_test_") and stem.endswith("_stats"):
        core = stem[len("load_test_") : -len("_stats")]
        parts = core.rsplit("_", 2)
        if (
            len(parts) == 3
            and parts[1].isdigit()
            and len(parts[1]) == 8
            and parts[2].isdigit()
            and len(parts[2]) == 6
        ):
            return parts[0]
        return core
    return stem


def iter_entries(files: Iterable[Path]) -> List[Tuple[str, Metrics]]:
    entries: List[Tuple[str, Metrics]] = []
    for file_path in files:
        metrics = parse_stats_csv(file_path)
        entries.append((scenario_name_from_path(file_path), metrics))
    return entries


def status_symbols(ascii_status: bool) -> Tuple[str, str]:
    if ascii_status:
        return "OK", "FAIL"
    encoding = getattr(sys.stdout, "encoding", None)
    ok_symbol = "✅"
    fail_symbol = "❌"
    if encoding:
        try:
            ok_symbol.encode(encoding)
            fail_symbol.encode(encoding)
        except (LookupError, UnicodeEncodeError):
            return "OK", "FAIL"
    return ok_symbol, fail_symbol


def build_table(
    entries: List[Tuple[str, Metrics]],
    *,
    ascii_status: bool,
    with_success_rate: bool,
    with_overall: bool,
) -> str:
    if with_success_rate:
        header = "| Scenario | Total | Fail | Success (%) | Avg (ms) | P50 | P95 | P99 | Req/s | Status |"
        separator = "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"
    else:
        header = "| Scenario | Total | Fail | Avg (ms) | P50 | P95 | P99 | Req/s | Status |"
        separator = "|---|---:|---:|---:|---:|---:|---:|---:|---|"

    lines = [header, separator]
    valid: List[Tuple[str, Metrics]] = []
    ok_symbol, fail_symbol = status_symbols(ascii_status)

    for name, stats in entries:
        if stats.get("_missing"):
            if with_success_rate:
                lines.append(f"| {name} | - | - | - | - | - | - | - | - | missing |")
            else:
                lines.append(f"| {name} | - | - | - | - | - | - | - | missing |")
            continue
        if stats.get("_empty"):
            if with_success_rate:
                lines.append(f"| {name} | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | empty |")
            else:
                lines.append(f"| {name} | 0 | 0 | 0 | 0 | 0 | 0 | 0 | empty |")
            continue

        status = ok_symbol if stats.get("failures", 0) == 0 else fail_symbol
        if with_success_rate:
            total = stats["requests"]
            failures = stats["failures"]
            success_pct = (100.0 * max(total - failures, 0) / total) if total > 0 else 0.0
            lines.append(
                f"| {name} | {total} | {failures} | {success_pct:.0f}% | {stats['avg_ms']:.0f} | {stats['p50_ms']:.0f} | {stats['p95_ms']:.0f} | {stats['p99_ms']:.0f} | {stats['rps']:.1f} | {status} |"
            )
        else:
            lines.append(
                f"| {name} | {stats['requests']} | {stats['failures']} | {stats['avg_ms']:.0f} | {stats['p50_ms']:.0f} | {stats['p95_ms']:.0f} | {stats['p99_ms']:.0f} | {stats['rps']:.1f} | {status} |"
            )
        valid.append((name, stats))

    if with_overall and valid:
        total_reqs = sum(item["requests"] for _, item in valid)
        total_fail = sum(item["failures"] for _, item in valid)
        weighted_avg = (
            sum(item["avg_ms"] * item["requests"] for _, item in valid) / total_reqs
            if total_reqs
            else 0.0
        )
        sum_rps = sum(item["rps"] for _, item in valid)
        p50 = max(item["p50_ms"] for _, item in valid)
        p95 = max(item["p95_ms"] for _, item in valid)
        p99 = max(item["p99_ms"] for _, item in valid)
        overall_status = ok_symbol if total_fail == 0 else fail_symbol
        if with_success_rate:
            success_pct = (
                (100.0 * max(total_reqs - total_fail, 0) / total_reqs) if total_reqs else 0.0
            )
            lines.append(
                f"| Overall | {total_reqs} | {total_fail} | {success_pct:.0f}% | {weighted_avg:.0f} | {p50:.0f} | {p95:.0f} | {p99:.0f} | {sum_rps:.1f} | {overall_status} |"
            )
        else:
            lines.append(
                f"| Overall | {total_reqs} | {total_fail} | {weighted_avg:.0f} | {p50:.0f} | {p95:.0f} | {p99:.0f} | {sum_rps:.1f} | {overall_status} |"
            )

    return "\n".join(lines) + "\n"


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path, help="Locust *_stats.csv files")
    parser.add_argument("--out", type=Path, help="Write output to file")
    parser.add_argument("--ascii-status", action="store_true", help="Use OK/FAIL instead of emoji")
    parser.add_argument(
        "--with-overall", action="store_true", help="Append an aggregated 'Overall' row"
    )
    parser.add_argument(
        "--with-success-rate", action="store_true", help="Include Success (%%) column"
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    entries = iter_entries(args.files)
    table = build_table(
        entries,
        ascii_status=args.ascii_status,
        with_success_rate=args.with_success_rate,
        with_overall=args.with_overall,
    )

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(table, encoding="utf-8")
    else:
        sys.stdout.write(table)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
