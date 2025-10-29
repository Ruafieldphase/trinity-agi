from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional


DEFAULT_PROMPTS: List[str] = [
    "Design an ethical AI assistant for hospital triage that balances patient safety and data privacy.",
    "Assess the risks of deploying AGI in public education and propose safeguards.",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run multiple E3 persona orchestration sessions and summarise results."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/persona_registry_e3.json"),
        help="Persona registry configuration (default: configs/persona_registry_e3.json).",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=1,
        help="Recursion depth (default: 1).",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path("outputs/persona_runs/E3"),
        help="Directory to store JSONL logs (default: outputs/persona_runs/E3).",
    )
    parser.add_argument(
        "--prompt-file",
        type=Path,
        help="Optional text file containing prompts (one per line).",
    )
    parser.add_argument(
        "--prompts",
        nargs="*",
        help="Prompts to execute (overrides default prompt set if provided).",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("outputs/E3_RESULTS_SUMMARY.md"),
        help="Path to write summary markdown (default: outputs/E3_RESULTS_SUMMARY.md).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum rows to keep in summary table (default: 10).",
    )
    return parser.parse_args()


def load_prompts(args: argparse.Namespace) -> List[str]:
    if args.prompts:
        return [prompt.strip() for prompt in args.prompts if prompt.strip()]
    if args.prompt_file and args.prompt_file.exists():
        return [
            line.strip()
            for line in args.prompt_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    return DEFAULT_PROMPTS


def slugify(text: str) -> str:
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-_"
    slug = "".join(
        ch if ch.lower() in allowed else "-" for ch in text.lower().strip()
    )
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "session"


def run_session(
    prompt: str,
    config: Path,
    depth: int,
    log_dir: Path,
) -> Path:
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"{slugify(prompt)[:40] or 'session'}_{timestamp}.jsonl"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / filename

    cmd = [
        "python",
        "orchestration\\persona_orchestrator.py",
        "--config",
        str(config),
        "--prompt",
        prompt,
        "--depth",
        str(depth),
        "--log",
        str(log_path),
    ]
    print(f"[run] {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    return log_path


def extract_resonance(path: Path) -> Optional[dict]:
    resonance = None
    try:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                metrics = payload.get("resonance_metrics")
                if metrics:
                    resonance = metrics
    except FileNotFoundError:
        return None
    return resonance


def update_summary(log_paths: Iterable[Path], summary_path: Path, limit: int) -> None:
    rows: List[dict] = []
    for path in log_paths:
        resonance = extract_resonance(path)
        if not resonance:
            continue
        rows.append(
            {
                "name": path.name,
                "verifiability": float(resonance.get("verifiability") or 0.0),
                "impact": float(resonance.get("impact_score") or 0.0),
                "transparency": float(resonance.get("transparency") or 0.0),
                "reproducibility": float(resonance.get("reproducibility") or 0.0),
                "notes": resonance.get("notes", ""),
            }
        )

    rows.sort(key=lambda r: r["verifiability"], reverse=True)
    table_rows = rows[:limit]
    lines = [
        "# E3 Batch Run Summary",
        "",
        f"총 {len(rows)}개의 실행 중 상위 {len(table_rows)}개만 Verifiability 순으로 정렬했습니다.",
        "",
        "| Run | Verifiability | Impact | Transparency | Notes |",
        "|-----|----------------|--------|--------------|-------|",
    ]
    for row in table_rows:
        notes = row["notes"]
        if len(notes) > 60:
            notes = notes[:57] + "..."
        lines.append(
            f"| `{row['name']}` | {row['verifiability']:.2f} | "
            f"{row['impact']:.2f} | {row['transparency']:.2f} | {notes} |"
        )

    lines.append("")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[summary] updated {summary_path}")


def main() -> None:
    args = parse_args()
    prompts = load_prompts(args)
    if not prompts:
        print("No prompts provided; aborting.")
        return

    executed_logs: List[Path] = []
    for prompt in prompts:
        log_path = run_session(prompt, args.config, args.depth, args.log_dir)
        executed_logs.append(log_path)

    update_summary(executed_logs, args.summary, args.limit)


if __name__ == "__main__":
    main()
