from __future__ import annotations

import argparse
import json
from pathlib import Path
import glob
from typing import List, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarise persona run JSONL logs (RUNE outputs, verifiability, etc.)."
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="One or more JSONL log files (supports glob patterns via shell).",
    )
    parser.add_argument(
        "--sort-by",
        choices=["verifiability", "impact", "transparency"],
        default="verifiability",
        help="Sort summary rows by the selected metric (default: verifiability).",
    )
    parser.add_argument(
        "--descending",
        action="store_true",
        help="Sort summaries in descending order.",
    )
    return parser.parse_args()


def load_summary(path: Path) -> Optional[dict]:
    resonance: Optional[dict] = None
    turns = 0
    try:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                persona = payload.get("persona") or {}
                persona_id = persona.get("id")
                if persona_id and persona_id not in {"user", "rune"}:
                    turns += 1
                metrics = payload.get("resonance_metrics")
                if metrics:
                    resonance = metrics
    except FileNotFoundError:
        print(f"[warn] file not found: {path}")
        return None

    if not resonance:
        return None

    return {
        "file": str(path),
        "turns": turns,
        "impact": resonance.get("impact_score"),
        "transparency": resonance.get("transparency"),
        "reproducibility": resonance.get("reproducibility"),
        "verifiability": resonance.get("verifiability"),
        "notes": resonance.get("notes"),
    }


def format_row(row: dict) -> str:
    impact = row.get("impact")
    transparency = row.get("transparency")
    reproducibility = row.get("reproducibility")
    verifiability = row.get("verifiability")
    return (
        f"{row['file']}\n"
        f"  turns={row.get('turns')}\n"
        f"  impact={impact:.2f}  transparency={transparency:.2f}  "
        f"reproducibility={reproducibility:.2f}  verifiability={verifiability:.2f}\n"
        f"  notes={row.get('notes')}"
    )


def main() -> None:
    args = parse_args()
    summaries: List[dict] = []
    expanded: List[Path] = []
    for item in args.files:
        matches = glob.glob(item)
        if matches:
            expanded.extend(Path(match) for match in matches)
        else:
            expanded.append(Path(item))

    for path in expanded:
        candidates = sorted(path.glob("*.jsonl")) if path.is_dir() else [path]
        for candidate in candidates:
            summary = load_summary(candidate)
            if summary:
                summaries.append(summary)

    if not summaries:
        print("No summaries found.")
        return

    key_name = args.sort_by
    summaries.sort(
        key=lambda row: (row.get(key_name) is None, row.get(key_name)),
        reverse=args.descending,
    )

    print(f"Total runs summarised: {len(summaries)}")
    for row in summaries:
        print(format_row(row))


if __name__ == "__main__":
    main()
