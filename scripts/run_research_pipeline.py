from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "configs" / "persona_registry.json"
SCENARIO_PATH = ROOT / "scripts" / "prompt_scenarios.json"


def run_command(command: Sequence[str], cwd: Path, label: str) -> None:
    print(f"\n=== [{label}] {' '.join(command)} ===")
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    if result.returncode != 0:
        raise RuntimeError(f"Step '{label}' failed with exit code {result.returncode}.")


def load_scenario(prompt: str | None, scenario_id: str | None) -> Tuple[str, int]:
    if prompt:
        return prompt, 1
    if scenario_id:
        if not SCENARIO_PATH.exists():
            raise FileNotFoundError(f"Scenario file not found: {SCENARIO_PATH}")
        payload = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
        scenarios: Dict[str, Dict] = {
            item["id"]: item for item in payload.get("scenarios", [])
        }
        if scenario_id not in scenarios:
            raise ValueError(f"Scenario '{scenario_id}' not defined.")
        info = scenarios[scenario_id]
        return info["prompt"], int(info.get("depth", 1))
    return "Design an empathic AI coach for creative writers.", 2


def detect_claude_available(config_path: Path) -> bool:
    if not config_path.exists():
        return False
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    backends = payload.get("backends") or {}
    claude = backends.get("claude_cli")
    if not claude:
        return False
    command = claude.get("command")
    if not command or shutil.which(command) is None:
        return False
    try:
        result = subprocess.run(
            [command, "status"], capture_output=True, text=True, timeout=5
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    output = (result.stdout + result.stderr).lower()
    if "expired" in output or ("token" in output and "invalid" in output):
        return False
    return result.returncode == 0


def override_antithesis_backend(config_path: Path, fallback_backend: str) -> None:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    personas = payload.get("personas") or []
    modified = False
    for persona in personas:
        if persona.get("id") == "antithesis":
            persona["backend"] = fallback_backend
            persona["name"] = persona.get("name", "Boundary Challenger (fallback)")
            persona["role"] = persona.get("role", "Critical reflector")
            modified = True
            break
    if modified:
        config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Antithesis backend switched to '{fallback_backend}'")


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Run the end-to-end NAEDA research pipeline."
    )
    parser.add_argument(
        "--skip-orchestrator",
        action="store_true",
        help="Skip persona orchestration (useful when CLI backends are unavailable).",
    )
    parser.add_argument(
        "--prompt",
        help="Seed prompt for the orchestration demo (overrides scenario).",
    )
    parser.add_argument(
        "--scenario",
        help="Scenario ID defined in scripts/prompt_scenarios.json.",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=0,
        help="Recursion depth (overrides scenario depth when >0).",
    )
    parser.add_argument(
        "--force-external",
        action="store_true",
        help="Do not fall back to local personas when CLAUDE CLI is unavailable.",
    )
    parser.add_argument(
        "--fallback-backend",
        default="local_ollama",
        help="Persona backend to use when CLAUDE CLI is unavailable.",
    )
    args = parser.parse_args(argv)

    seed_prompt, default_depth = load_scenario(args.prompt, args.scenario)
    depth = args.depth if args.depth > 0 else default_depth

    claude_available = detect_claude_available(CONFIG_PATH)
    if not claude_available and not args.force_external and not args.skip_orchestrator:
        print("Claude CLI unavailable; using local fallback for antithesis.")
        override_antithesis_backend(CONFIG_PATH, args.fallback_backend)

    steps: List[tuple[str, Sequence[str]]] = [
        (
            "phase_dataset",
            [
                sys.executable,
                "scripts/prepare_phase_injection_dataset.py",
                "--config",
                "batch_config.json",
                "--summary",
                "batch_summary.json",
            ],
        ),
        (
            "phase_metrics",
            [
                sys.executable,
                "analysis/phase_metrics.py",
                "--plots",
            ],
        ),
        (
            "conversation_metrics",
            [
                sys.executable,
                "analysis/conversation_diversity.py",
                "--input",
                "outputs/ai_conversations_combined.csv",
                "--plots",
            ],
        ),
    ]

    log_path = ROOT / "outputs" / "persona_runs" / "auto_session.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    if not args.skip_orchestrator:
        steps.extend(
            [
                (
                    "persona_orchestrator",
                    [
                        sys.executable,
                        "orchestration/persona_orchestrator.py",
                        "--prompt",
                        seed_prompt,
                        "--depth",
                        str(depth),
                        "--config",
                        "configs/persona_registry.json",
                        "--log",
                        str(log_path),
                    ],
                ),
                (
                    "persona_metrics",
                    [
                        sys.executable,
                        "analysis/persona_metrics.py",
                        str(log_path),
                        "--plots",
                    ],
                ),
            ]
        )

    for label, command in steps:
        run_command(command, ROOT, label)

    print("\nPipeline completed successfully.")
    if not args.skip_orchestrator:
        print(f"Persona log saved to {log_path}")


if __name__ == "__main__":
    main()
