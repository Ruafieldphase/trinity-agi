from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Optional

try:
    # When executed as a module (pytest/import), relative import works
    from .vscode_integration import default_repo_tasks, generate_commands_json, write_tasks_json
except Exception:
    # When executed as a standalone script, fall back to local import
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.append(str(_Path(__file__).resolve().parent))
    from vscode_integration import default_repo_tasks, generate_commands_json, write_tasks_json


def _sanitize_arg_path(arg: str) -> str:
    """Allow trailing inline PowerShell-style comments in args (split at '#')."""
    if "#" in arg:
        return arg.split("#", 1)[0].strip()
    return arg


def sync_vscode_assets(workspace_dir: Path, vscode_rel_dir: str = ".vscode") -> None:
    """
    Generate or update VS Code configuration assets (tasks.json, commands.json).
    This function is idempotent and can be re-run anytime.
    """
    vscode_dir = (workspace_dir / vscode_rel_dir).resolve()
    tasks = default_repo_tasks(workspace_folder_var="${workspaceFolder}")
    write_tasks_json(vscode_dir, tasks)
    generate_commands_json(vscode_dir, tasks)


def run_status_loop(
    state_file: Path, interval_seconds: float = 2.0, max_iterations: Optional[int] = None
) -> int:
    """
    Simple terminal UI: prints orchestrator/monitoring status by tailing a JSON state file.
    - Prints when file changes (size/mtime) or on first run.
    - Designed to be used as a background watch task in VS Code.
    Returns exit code 0 on normal termination.
    """
    last_sig = None
    iterations = 0
    print(f"[status] Watching {state_file}")
    while True:
        try:
            if state_file.exists():
                stat = state_file.stat()
                sig = (stat.st_mtime_ns, stat.st_size)
                if sig != last_sig:
                    last_sig = sig
                    try:
                        data = json.loads(state_file.read_text(encoding="utf-8"))
                        print("[status] --- update ---")
                        print(json.dumps(data, ensure_ascii=False, indent=2))
                    except json.JSONDecodeError:
                        print("[status] file present but not valid JSON yet; waiting...")
            else:
                print("[status] state file not found; waiting...")
        except KeyboardInterrupt:
            print("[status] interrupted")
            return 0
        time.sleep(interval_seconds)
        iterations += 1
        if max_iterations is not None and iterations >= max_iterations:
            return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="VS Code extension-like helpers")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_sync = sub.add_parser("sync", help="Sync VS Code assets (tasks.json, commands.json)")
    p_sync.add_argument(
        "--workspace-dir",
        default=str(Path(__file__).resolve().parents[2]),
        help="Workspace root directory",
    )
    p_sync.add_argument("--vscode-dir", default=".vscode", help="Relative VS Code config dir")

    p_watch = sub.add_parser("watch-status", help="Print status by watching a JSON state file")
    p_watch.add_argument("--state-file", required=True, help="Path to JSON state file to watch")
    p_watch.add_argument("--interval", type=float, default=2.0, help="Polling interval seconds")
    p_watch.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Stop after N iterations (useful for tests)",
    )

    args = parser.parse_args()
    if args.cmd == "sync":
        ws_dir = Path(_sanitize_arg_path(args.workspace_dir))
        sync_vscode_assets(ws_dir, args.vscode_dir)
        print("Synced VS Code assets.")
        return 0
    elif args.cmd == "watch-status":
        state_path = Path(_sanitize_arg_path(args.state_file))
        return run_status_loop(state_path, args.interval, args.max_iterations)
    else:
        print(f"Unknown command: {args.cmd}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
