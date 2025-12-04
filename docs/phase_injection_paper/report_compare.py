#!/usr/bin/env python3
"""
Aggregate summary for multiple System C v8 CSV outputs.

Usage:
    python report_compare.py file1.v8.report.csv file2.v8.report.csv ...
"""
import argparse
import csv
from pathlib import Path
from typing import Dict, List


def load_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader if row.get("sample") and row["sample"].upper() != "AVERAGE"]
    return rows


def parse_float(row: Dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "0") or 0)
    except ValueError:
        return 0.0


def compute_summary(path: Path) -> Dict[str, float]:
    rows = load_csv(path)
    if not rows:
        return {
            "file": str(path),
            "samples": 0,
            "avg_total_after": 0.0,
            "avg_total_delta": 0.0,
            "pass_rate": 0.0,
            "avg_risk_after": 0.0,
            "avg_quote_after": 0.0,
        }
    total_after_sum = sum(parse_float(r, "total_after") for r in rows)
    total_delta_sum = sum(parse_float(r, "total_delta") for r in rows)
    risk_after_sum = sum(parse_float(r, "risk_total") for r in rows)
    quote_after_sum = sum(parse_float(r, "quote_total") for r in rows)
    pass_count = sum(1 for r in rows if (r.get("label_after") or "").lower() == "pass")
    samples = len(rows)
    return {
        "file": path.name,
        "samples": samples,
        "avg_total_after": total_after_sum / samples,
        "avg_total_delta": total_delta_sum / samples,
        "pass_rate": (pass_count / samples) * 100.0,
        "avg_risk_after": risk_after_sum / samples,
        "avg_quote_after": quote_after_sum / samples,
    }


def format_markdown(summaries: List[Dict[str, float]]) -> str:
    lines = [
        "| File | Samples | Avg Total (After) | Avg Total Δ | Pass % | Avg Risk Count | Avg Quote Count |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for s in summaries:
        lines.append(
            f"| {s['file']} | {s['samples']} | {s['avg_total_after']:.3f} | "
            f"{s['avg_total_delta']:.3f} | {s['pass_rate']:.1f} | "
            f"{s['avg_risk_after']:.3f} | {s['avg_quote_after']:.3f} |"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Compare System C v8 CSV reports.")
    parser.add_argument("csv_files", nargs="+", help="Paths to *.v8.report.csv files")
    args = parser.parse_args()

    summaries = []
    for file_path in args.csv_files:
        path = Path(file_path)
        if not path.exists():
            print(f"[WARN] File not found: {path}")
            continue
        summaries.append(compute_summary(path))

    if not summaries:
        print("No valid CSV files supplied.")
        return

    print(format_markdown(summaries))


if __name__ == "__main__":
    main()
