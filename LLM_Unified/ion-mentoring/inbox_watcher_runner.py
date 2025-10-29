from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from agent_implementations import GitkoAgent, LubitAgent, SianAgent
from agent_inbox_watcher import InboxWatcher, MultiAgentWatcher


def build_agents(names: List[str]):
    name_map = {
        "sian": SianAgent,
        "lubit": LubitAgent,
        "gitko": GitkoAgent,
    }
    agents = []
    for n in names:
        key = n.strip().lower()
        if key in name_map:
            agents.append(name_map[key]())
        else:
            raise ValueError(f"Unknown agent name: {n}")
    return agents


def _write_status(
    status_file: Optional[Path], *, agents: List[str], mode: str, running: bool
) -> None:
    if not status_file:
        return
    status_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "agents": agents,
        "mode": mode,
        "running": running,
    }
    try:
        status_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def run(
    agents: List[str],
    process_immediately: bool = True,
    duration_seconds: float | None = None,
    status_file: Optional[Path] = None,
    status_interval_seconds: float = 1.0,
) -> int:
    names = [a for a in agents]
    mode = "immediate" if process_immediately else "queue"
    if len(names) == 1:
        agent_objs = build_agents(names)
        watcher = InboxWatcher(agent_objs[0], process_immediately=process_immediately)
        watcher.start()
        try:
            if duration_seconds is None:
                print("[runner] Watching single agent indefinitely...")
                while True:
                    _write_status(status_file, agents=names, mode=mode, running=True)
                    time.sleep(status_interval_seconds)
            else:
                print(f"[runner] Watching single agent for {duration_seconds} seconds...")
                deadline = time.time() + duration_seconds
                while time.time() < deadline:
                    _write_status(status_file, agents=names, mode=mode, running=True)
                    time.sleep(status_interval_seconds)
        finally:
            watcher.stop()
            _write_status(status_file, agents=names, mode=mode, running=False)
        return 0
    else:
        agent_objs = build_agents(names)
        maw = MultiAgentWatcher(agent_objs)
        maw.start_all()
        try:
            if duration_seconds is None:
                print("[runner] Watching multiple agents indefinitely...")
                while True:
                    _write_status(status_file, agents=names, mode=mode, running=True)
                    time.sleep(status_interval_seconds)
            else:
                print(f"[runner] Watching multiple agents for {duration_seconds} seconds...")
                deadline = time.time() + duration_seconds
                while time.time() < deadline:
                    _write_status(status_file, agents=names, mode=mode, running=True)
                    time.sleep(status_interval_seconds)
        finally:
            maw.stop_all()
            _write_status(status_file, agents=names, mode=mode, running=False)
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="INBOX watcher runner")
    parser.add_argument(
        "--agents", default="all", help="Comma-separated agent names (sian,lubit,gitko) or 'all'"
    )
    parser.add_argument(
        "--no-immediate",
        action="store_true",
        help="Queue mode: do not process immediately on file create",
    )
    parser.add_argument(
        "--duration-seconds",
        type=float,
        default=None,
        help="If provided, run for N seconds then exit",
    )
    parser.add_argument(
        "--status-file", default=None, help="Optional JSON status file path to update periodically"
    )
    parser.add_argument(
        "--status-interval-seconds", type=float, default=1.0, help="Status update interval seconds"
    )
    args = parser.parse_args()

    if args.agents.strip().lower() == "all":
        agent_names = ["sian", "lubit", "gitko"]
    else:
        agent_names = [x.strip() for x in args.agents.split(",") if x.strip()]
        if not agent_names:
            agent_names = ["sian", "lubit", "gitko"]

    status_path: Optional[Path]
    if args.status_file:
        status_path = Path(args.status_file).resolve()
    else:
        # default outputs path in repo
        status_path = Path(__file__).resolve().parent / "outputs" / "inbox_watcher_status.json"

    return run(
        agent_names,
        process_immediately=(not args.no_immediate),
        duration_seconds=args.duration_seconds,
        status_file=status_path,
        status_interval_seconds=float(args.status_interval_seconds),
    )


if __name__ == "__main__":
    raise SystemExit(main())
