from __future__ import annotations

import argparse
import glob
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a markdown summary of persona run logs."
    )
    parser.add_argument(
        "pattern",
        nargs="+",
        help="One or more path patterns (files or directories) to scan for JSONL logs.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/E3_RESULTS_SUMMARY.md"),
        help="Output markdown file (default: outputs/E3_RESULTS_SUMMARY.md).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of runs to include in table (default: 10).",
    )
    return parser.parse_args()


def collect_logs(patterns: List[str]) -> List[Path]:
    paths: List[Path] = []
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            paths.extend(Path(match) for match in matches)
        else:
            paths.append(Path(pattern))
    expanded: List[Path] = []
    for path in paths:
        if path.is_dir():
            expanded.extend(sorted(path.glob("*.jsonl")))
        else:
            expanded.append(path)
    return expanded


def extract_metrics(path: Path) -> Optional[Dict[str, object]]:
    resonance: Optional[dict] = None
    turns = 0
    total_citations = 0
    total_words = 0.0
    quality_decisions: Dict[str, Counter] = defaultdict(Counter)
    issue_counter: Counter = Counter()
    non_keep_flags: List[Tuple[str, str]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            persona = payload.get("persona", {}).get("id")
            if persona and persona not in {"user", "rune"}:
                turns += 1
                response_text = payload.get("response") or ""
                total_citations += response_text.count("[Source:")

                word_count = (
                    payload.get("evaluation_metrics", {})
                    .get("length", {})
                    .get("word_count")
                )
                if isinstance(word_count, (int, float)):
                    total_words += float(word_count)

                phase_meta = payload.get("phase") or {}
                validators = (
                    phase_meta.get("validators", {})
                    .get(persona, {})
                )
                quality_payload = validators.get("quality") or {}
                decision = quality_payload.get("decision")
                if decision:
                    quality_decisions[persona][decision] += 1
                    if decision != "keep":
                        non_keep_flags.append((persona, decision))
                for issue in quality_payload.get("issues", []):
                    issue_type = issue.get("type", "unknown_issue")
                    issue_counter[issue_type] += 1

            metrics = payload.get("resonance_metrics")
            if metrics:
                resonance = metrics
    except FileNotFoundError:
        return None

    if not resonance:
        return None

    return {
        "file": str(path),
        "name": path.name,
        "turns": turns,
        "impact": float(resonance.get("impact_score") or 0.0),
        "transparency": float(resonance.get("transparency") or 0.0),
        "reproducibility": float(resonance.get("reproducibility") or 0.0),
        "verifiability": float(resonance.get("verifiability") or 0.0),
        "notes": resonance.get("notes", ""),
        "avg_citations": (total_citations / turns) if turns else 0.0,
        "avg_words": (total_words / turns) if turns else 0.0,
        "quality_decisions": {
            persona: dict(counter) for persona, counter in quality_decisions.items()
        },
        "quality_flags": non_keep_flags,
        "quality_issue_counts": dict(issue_counter),
    }


def build_markdown(rows: List[Dict[str, object]], limit: int) -> str:
    if not rows:
        return "# E3 Results Summary\n\nNo runs found.\n"

    sorted_rows = sorted(
        rows, key=lambda row: row.get("verifiability", 0.0), reverse=True
    )
    table_rows = sorted_rows[:limit]

    lines = [
        "# E3 Results Summary",
        "",
        f"Reviewing {len(rows)} run logs; table lists the top {len(table_rows)} by verifiability.",
        "",
        "| Run | Turns | Verifiability | Impact | Avg Citations | Avg Words | Quality Flags | Notes |",
        "|-----|-------|----------------|--------|---------------|-----------|----------------|-------|",
    ]

    for row in table_rows:
        notes = row.get("notes") or ""
        notes_short = notes if len(notes) <= 60 else notes[:57] + "..."
        avg_citations = row.get("avg_citations", 0.0) or 0.0
        avg_words = row.get("avg_words", 0.0) or 0.0
        quality_flags = row.get("quality_flags") or []
        if quality_flags:
            flag_summary = ", ".join(
                f"{persona}:{decision}" for persona, decision in quality_flags
            )
        else:
            flag_summary = "-"
        lines.append(
            f"| `{row['name']}` | {row['turns']} | {row['verifiability']:.2f} | "
            f"{row['impact']:.2f} | {avg_citations:.1f} | {avg_words:.0f} | {flag_summary} | {notes_short} |"
        )

    lines.append("")
    best = table_rows[0]
    best_flags = best.get("quality_flags") or []
    best_flag_text = (
        ", ".join(f"{persona}:{decision}" for persona, decision in best_flags)
        if best_flags
        else "None"
    )
    lines.append(
        "## Top Run\n"
        f"- **{best['name']}** - Verifiability {best['verifiability']:.2f}, "
        f"Impact {best['impact']:.2f}, Transparency {best['transparency']:.2f}\n"
        f"- Avg citations per persona: {best.get('avg_citations', 0.0):.1f}\n"
        f"- Avg words per persona: {best.get('avg_words', 0.0):.0f}\n"
        f"- Quality flags: {best_flag_text}\n"
        f"- Notes: {best.get('notes') or 'N/A'}"
    )

    aggregate_issue_counter: Counter = Counter()
    aggregate_decision_counter: Counter = Counter()
    for row in rows:
        for issue, count in (row.get("quality_issue_counts") or {}).items():
            aggregate_issue_counter[issue] += count
        for persona, decisions in (row.get("quality_decisions") or {}).items():
            for decision, count in (decisions or {}).items():
                key = f"{persona}:{decision}"
                aggregate_decision_counter[key] += count

    if aggregate_issue_counter:
        lines.append("")
        lines.append("## Frequent Quality Issues")
        for issue, count in aggregate_issue_counter.most_common(8):
            lines.append(f"- {issue}: {count}")

    if aggregate_decision_counter:
        lines.append("")
        lines.append("## Quality Decision Breakdown")
        for key, count in aggregate_decision_counter.most_common():
            lines.append(f"- {key}: {count}")

    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    paths = collect_logs(args.pattern)
    metrics: List[Dict[str, object]] = []
    for path in paths:
        info = extract_metrics(path)
        if info:
            metrics.append(info)

    content = build_markdown(metrics, args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    print(f"Wrote summary to {args.output}")


if __name__ == "__main__":
    main()
