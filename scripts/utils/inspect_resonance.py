from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, List


def load_ledger_entries(base_dir: Path) -> List[dict]:
    if not base_dir.exists():
        raise FileNotFoundError(f"Ledger directory not found: {base_dir}")
    entries: List[dict] = []
    for path in sorted(base_dir.glob("ledger-*.jsonl")):
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                entries.append(json.loads(line))
    return entries


def summarise(entries: Iterable[dict]) -> None:
    total = 0
    resonance = 0
    safety = 0
    impact_sum = transparency_sum = reproducibility_sum = verifiability_sum = 0.0
    for entry in entries:
        total += 1
        event_type = entry.get("event_type", "")
        if event_type == "rune_report":
            resonance += 1
            metrics = entry.get("evaluation") or {}
            impact_sum += metrics.get("impact_score", 0.0)
            transparency_sum += metrics.get("transparency", 0.0)
            reproducibility_sum += metrics.get("reproducibility", 0.0)
            verifiability_sum += metrics.get("verifiability", 0.0)
        if event_type == "safety_check":
            safety += 1
    print("=== Resonance Ledger Overview ===")
    print(f"Total entries: {total}")
    print(f"Safety checks: {safety}")
    if resonance:
        print(f"RUNE reports: {resonance}")
        print(
            "Average RES metrics "
            f"(Impact/Transparency/Reproducibility/Verifiability): "
            f"{impact_sum/resonance:.2f} / "
            f"{transparency_sum/resonance:.2f} / "
            f"{reproducibility_sum/resonance:.2f} / "
            f"{verifiability_sum/resonance:.2f}"
        )
    else:
        print("No RUNE reports logged yet.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Resonance Ledger entries.")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path("outputs/resonance_ledger"),
        help="Directory containing ledger-YYYYMMDD.jsonl files.",
    )
    args = parser.parse_args()

    entries = load_ledger_entries(args.base_dir)
    summarise(entries)


if __name__ == "__main__":
    main()
