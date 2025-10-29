from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Sequence

DEFAULT_PROMPTS: List[str] = [
    "Design an empathic AI coach for creative writers (E1 baseline).",
    "Assess emotional resilience for remote research teams (E1 baseline).",
]


def read_prompts(path: Path) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(f"Prompts file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            prompts = [str(item).strip() for item in data if str(item).strip()]
            if not prompts:
                raise ValueError(f"Empty prompt list in {path}")
            return prompts
        if isinstance(data, dict):
            candidate = data.get("prompts") or data.get("seeds")
            if isinstance(candidate, list):
                prompts = [str(item).strip() for item in candidate if str(item).strip()]
                if prompts:
                    return prompts
            value = data.get("prompt") or data.get("seed") or data.get("text")
            if value:
                return [str(value).strip()]
        raise ValueError(f"Unsupported JSON structure in {path}")

    if suffix == ".jsonl":
        prompts: List[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                value = payload.get("prompt") or payload.get("seed") or payload.get("text")
                if value:
                    prompts.append(str(value).strip())
            elif isinstance(payload, str):
                prompts.append(payload.strip())
        if prompts:
            return prompts
        raise ValueError(f"No prompts found in {path}")

    # treat as plain text (one prompt per line, blank lines ignored)
    prompts = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not prompts:
        raise ValueError(f"No prompts found in {path}")
    return prompts


def slugify(text: str) -> str:
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_-"
    slug = []
    for ch in text.lower():
        if ch in allowed:
            slug.append(ch)
        elif ch.isspace() or ch in {"/", "\\", ":", ",", "."}:
            slug.append("-")
    cleaned = "".join(slug).strip("-")
    return cleaned or "prompt"


def build_command(prompt: str, log_path: Path, depth: int, config: Path | None, strict_cli: bool) -> List[str]:
    cmd = [
        sys.executable,
        str(Path("orchestration") / "persona_orchestrator.py"),
        "--prompt",
        prompt,
        "--depth",
        str(depth),
        "--log",
        str(log_path),
    ]
    if config:
        cmd.extend(["--config", str(config)])
    if strict_cli:
        cmd.append("--strict-cli")
    return cmd


def run_orchestrator(cmd: Sequence[str], dry_run: bool) -> int:
    print(f"[run] {' '.join(cmd)}")
    if dry_run:
        return 0
    completed = subprocess.run(cmd, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"Orchestrator exited with code {completed.returncode}")
    return completed.returncode


def summarise_metrics(outdir: Path) -> str:
    summary_path = outdir / "symmetry_summary.txt"
    if summary_path.exists():
        return summary_path.read_text(encoding="utf-8").strip()
    return "symmetry_summary.txt가 생성되지 않았습니다."


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run E1 residual band sweep experiments.")
    parser.add_argument("--prompts-file", type=Path, help="Optional file containing prompts (one per line or JSON array).")
    parser.add_argument("--runs-per-prompt", type=int, default=1, help="How many sessions to run per prompt (default: 1).")
    parser.add_argument("--depth", type=int, default=1, help="Recursion depth for each run (default: 1).")
    parser.add_argument("--config", type=Path, help="Persona registry JSON to pass through.")
    parser.add_argument("--outdir", type=Path, default=Path("outputs/persona_runs/E1"), help="Directory to store JSONL logs.")
    parser.add_argument("--strict-cli", action="store_true", help="Forward --strict-cli to the orchestrator.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them.")
    parser.add_argument("--metrics", action="store_true", help="Run analysis/persona_metrics.py --symmetry --plots on the produced logs.")
    parser.add_argument("--append", action="store_true", help="Do not delete existing logs in the target directory.")
    return parser.parse_args(argv)


def ensure_outdir(path: Path, append: bool) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if append:
        return
    existing = list(path.glob("*.jsonl"))
    if existing:
        for file in existing:
            file.unlink()


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)

    prompts: List[str]
    if args.prompts_file:
        prompts = read_prompts(args.prompts_file)
    else:
        prompts = DEFAULT_PROMPTS

    ensure_outdir(args.outdir, args.append)

    generated_logs: List[Path] = []
    timestamp_prefix = datetime.now().strftime("%Y%m%d_%H%M%S")

    for prompt_index, prompt in enumerate(prompts, start=1):
        slug = slugify(prompt) or f"prompt{prompt_index}"
        for run_index in range(1, args.runs_per_prompt + 1):
            log_name = f"E1_{timestamp_prefix}_{slug}_r{run_index:02d}.jsonl"
            log_path = args.outdir / log_name
            cmd = build_command(prompt, log_path, args.depth, args.config, args.strict_cli)
            try:
                run_orchestrator(cmd, args.dry_run)
            except RuntimeError as exc:
                print(f"[error] {exc}")
                continue
            generated_logs.append(log_path)

    if args.metrics and generated_logs:
        metrics_outdir = Path("outputs") / "persona_metrics" / "E1"
        metrics_cmd = [
            sys.executable,
            str(Path("analysis") / "persona_metrics.py"),
            *[str(path) for path in generated_logs],
            "--outdir",
            str(metrics_outdir),
            "--symmetry",
            "--plots",
            "--band-mode",
            "--bollinger-k",
            "1.64",
        ]
        print(f"[metrics] {' '.join(metrics_cmd)}")
        if not args.dry_run:
            subprocess.run(metrics_cmd, check=True)
            summary = summarise_metrics(metrics_outdir)
            print("\n[요약]\n" + summary)

    print(f"완료: 총 {len(generated_logs)}개의 로그가 {args.outdir}에 저장되었습니다.")


if __name__ == "__main__":
    main()
