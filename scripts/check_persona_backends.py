from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Sequence


DEFAULT_CONFIG = Path("configs/persona_registry.json")


def load_config(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"Persona config not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def check_command(command: Optional[str]) -> Dict[str, str]:
    if not command:
        return {"available": "no", "error": "command missing"}

    resolved = shutil.which(command)
    if resolved is None:
        return {"available": "no", "error": f"'{command}' not on PATH"}

    try:
        # Use shell=True on Windows to handle .cmd, .bat, and other script extensions reliably
        is_windows = sys.platform == "win32"
        subprocess.run(
            [resolved, "--help"] if not is_windows else f'"{resolved}" --help',
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=5,
            check=False,
            shell=is_windows
        )
        return {"available": "yes", "path": resolved}
    except subprocess.TimeoutExpired:
        return {"available": "unknown", "error": "timeout on --help"}
    except Exception as exc:  # noqa: BLE001
        return {"available": "unknown", "error": str(exc)}


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Check availability of persona backends defined in the config."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Persona registry JSON (defaults to configs/persona_registry.json).",
    )
    args = parser.parse_args(argv)

    payload = load_config(args.config)
    backends = payload.get("backends") or {}
    if not backends:
        print("No backend definitions found.", file=sys.stderr)
        sys.exit(1)

    print(f"Checking backends in {args.config}:")
    for backend_id, cfg in backends.items():
        info = check_command(cfg.get("command"))
        line = f"- {backend_id}: {info.get('available')}"
        if "path" in info:
            line += f" ({info['path']})"
        if "error" in info:
            line += f" -> {info['error']}"
        print(line)


if __name__ == "__main__":
    main()
