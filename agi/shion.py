from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any, Optional


def _now_ts() -> float:
    return time.time()


def _workspace_root() -> Path:
    here = Path(__file__).resolve()
    return here.parent.parent


def _append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(obj, ensure_ascii=False) + "\n")


class JsonlLogger:
    def __init__(self, path: Path) -> None:
        self._path = path

    def write(self, level: str, event: str, **fields: Any) -> None:
        payload: dict[str, Any] = {"ts": _now_ts(), "level": level, "event": event, "pid": os.getpid()}
        if fields:
            payload.update(fields)
        _append_jsonl(self._path, payload)


def run(*, mode: str, heartbeat_interval_sec: float, log_dir: Path) -> int:
    log_dir.mkdir(parents=True, exist_ok=True)
    app_log = JsonlLogger(log_dir / "shion.jsonl")
    vitals_log = JsonlLogger(log_dir / "shion.vitals.jsonl")

    app_log.write("INFO", "shion_start", mode=mode, heartbeat_interval_sec=heartbeat_interval_sec)
    while True:
        vitals_log.write("INFO", "heartbeat")
        time.sleep(max(0.25, float(heartbeat_interval_sec)))


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Shion (silent heart)")
    parser.add_argument("--silent-mode", action="store_true")
    parser.add_argument("--heartbeat-interval-sec", type=float, default=3.0)
    parser.add_argument("--log-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    root = _workspace_root()
    log_dir = args.log_dir or (root / "log")
    mode = "silent" if args.silent_mode else "normal"
    return run(mode=mode, heartbeat_interval_sec=args.heartbeat_interval_sec, log_dir=log_dir)


if __name__ == "__main__":
    raise SystemExit(main())
