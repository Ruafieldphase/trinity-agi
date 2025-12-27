from __future__ import annotations

import argparse
import json
import os
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional


def _now_ts() -> float:
    return time.time()


def _find_workspace_root(start: Path) -> Path:
    start = start.resolve()
    for candidate in (start, *start.parents):
        candidate_dir = candidate if candidate.is_dir() else candidate.parent
        if (candidate_dir / "agi").is_dir():
            return candidate_dir
    return start.parent if start.is_dir() else start.parent.parent


def _clamp_watchdog_interval_sec(value: float) -> float:
    try:
        value = float(value)
    except Exception:
        return 12.0
    return min(15.0, max(10.0, value))


def _tail_last_nonempty_line(path: Path, max_bytes: int = 8192) -> Optional[str]:
    try:
        with path.open("rb") as file:
            file.seek(0, os.SEEK_END)
            end = file.tell()
            if end <= 0:
                return None
            size = min(max_bytes, end)
            file.seek(-size, os.SEEK_END)
            data = file.read(size)
    except FileNotFoundError:
        return None
    except OSError:
        return None

    for raw in reversed(data.splitlines()):
        raw = raw.strip()
        if not raw:
            continue
        try:
            return raw.decode("utf-8")
        except Exception:
            return raw.decode("utf-8", errors="replace")
    return None


def _read_last_jsonl_obj(path: Path) -> Optional[dict[str, Any]]:
    line = _tail_last_nonempty_line(path)
    if not line:
        return None
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def _append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _powershell_exe() -> str:
    return "powershell.exe" if os.name == "nt" else "powershell"


def _invoke_ps1(script_path: Path, args: list[str], *, cwd: Optional[Path] = None) -> None:
    cmd = [_powershell_exe(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path), *args]
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    subprocess.Popen(
        cmd,
        cwd=str(cwd or script_path.parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags,
    )


@dataclass(frozen=True)
class RhythmGuardianConfig:
    watchdog_interval_sec: float = 12.0
    heartbeat_max_age_sec: float = 15.0
    recovery_cooldown_sec: float = 20.0
    workspace_root: Optional[Path] = None
    shion_vitals_jsonl: Optional[Path] = None
    invoke_shion_ps1: Optional[Path] = None
    log_jsonl: Optional[Path] = None

    def resolved(self) -> "RhythmGuardianConfig":
        root = self.workspace_root or _find_workspace_root(Path(__file__))
        interval = _clamp_watchdog_interval_sec(self.watchdog_interval_sec)
        return RhythmGuardianConfig(
            watchdog_interval_sec=interval,
            heartbeat_max_age_sec=float(self.heartbeat_max_age_sec),
            recovery_cooldown_sec=float(self.recovery_cooldown_sec),
            workspace_root=root,
            shion_vitals_jsonl=self.shion_vitals_jsonl or (root / "log" / "shion.vitals.jsonl"),
            invoke_shion_ps1=self.invoke_shion_ps1 or (root / "invoke_shion.ps1"),
            log_jsonl=self.log_jsonl or (root / "log" / "rhythm_guardian.jsonl"),
        )


class RhythmGuardian:
    def __init__(
        self,
        config: Optional[RhythmGuardianConfig] = None,
        *,
        vital_check_fn: Optional[Callable[[], bool]] = None,
    ) -> None:
        self._config = (config or RhythmGuardianConfig()).resolved()
        self._vital_check_fn = vital_check_fn

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._timer: Optional[threading.Timer] = None
        self._last_recovery_ts: Optional[float] = None

    def start(self) -> None:
        with self._lock:
            if self._timer is not None:
                return
            self._stop_event.clear()
            self._log("INFO", "start", watchdog_interval_sec=self._config.watchdog_interval_sec)
            self._schedule_next(0.0)

    def stop(self) -> None:
        with self._lock:
            self._stop_event.set()
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            self._log("INFO", "stop")

    def _schedule_next(self, delay_sec: float) -> None:
        if self._stop_event.is_set():
            return
        timer = threading.Timer(delay_sec, self._tick)
        timer.daemon = True
        self._timer = timer
        timer.start()

    def _tick(self) -> None:
        started = time.monotonic()
        try:
            if not self._vital_check():
                self._recover(reason="vital_check_failed")
        except Exception as exc:
            self._log("ERROR", "vital_check_exception", error=str(exc))
            self._recover(reason="vital_check_exception", error=str(exc))
        finally:
            elapsed = time.monotonic() - started
            delay = max(0.0, self._config.watchdog_interval_sec - elapsed)
            with self._lock:
                if self._stop_event.is_set():
                    self._timer = None
                    return
                self._schedule_next(delay)

    def _vital_check(self) -> bool:
        if self._vital_check_fn is not None:
            return bool(self._vital_check_fn())

        vitals_path = self._config.shion_vitals_jsonl
        payload = _read_last_jsonl_obj(vitals_path)
        if not payload:
            self._log("WARN", "vitals_missing", path=str(vitals_path))
            return False

        ts = payload.get("ts")
        if not isinstance(ts, (int, float)):
            self._log("WARN", "vitals_invalid", payload=payload)
            return False

        age = _now_ts() - float(ts)
        ok = age <= self._config.heartbeat_max_age_sec
        self._log(
            "INFO" if ok else "WARN",
            "vitals_check",
            ok=ok,
            age_sec=round(age, 3),
            max_age_sec=self._config.heartbeat_max_age_sec,
        )
        return ok

    def _recover(self, *, reason: str, **extra: Any) -> None:
        now = _now_ts()
        if self._last_recovery_ts is not None and (now - self._last_recovery_ts) < self._config.recovery_cooldown_sec:
            self._log("WARN", "recovery_cooldown", reason=reason, cooldown_sec=self._config.recovery_cooldown_sec)
            return

        self._last_recovery_ts = now
        self._log("WARN", "recovery_invoke", reason=reason, **extra)

        script_path = self._config.invoke_shion_ps1
        if not script_path.exists():
            self._log("ERROR", "invoke_shion_missing", path=str(script_path))
            return

        _invoke_ps1(
            script_path,
            ["-WorkspaceRoot", str(self._config.workspace_root), "-Reason", reason],
            cwd=self._config.workspace_root,
        )

    def _log(self, level: str, event: str, **fields: Any) -> None:
        payload: dict[str, Any] = {"ts": _now_ts(), "level": level, "event": event}
        if fields:
            payload.update(fields)
        try:
            _append_jsonl(self._config.log_jsonl, payload)
        except OSError:
            pass


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Rhythm Guardian (vital-check watchdog)")
    parser.add_argument("--watchdog-interval-sec", type=float, default=12.0)
    parser.add_argument("--heartbeat-max-age-sec", type=float, default=15.0)
    parser.add_argument("--recovery-cooldown-sec", type=float, default=20.0)
    parser.add_argument("--workspace-root", type=Path, default=None)
    parser.add_argument("--shion-vitals-jsonl", type=Path, default=None)
    parser.add_argument("--invoke-shion-ps1", type=Path, default=None)
    parser.add_argument("--log-jsonl", type=Path, default=None)
    args = parser.parse_args(argv)

    guardian = RhythmGuardian(
        RhythmGuardianConfig(
            watchdog_interval_sec=args.watchdog_interval_sec,
            heartbeat_max_age_sec=args.heartbeat_max_age_sec,
            recovery_cooldown_sec=args.recovery_cooldown_sec,
            workspace_root=args.workspace_root,
            shion_vitals_jsonl=args.shion_vitals_jsonl,
            invoke_shion_ps1=args.invoke_shion_ps1,
            log_jsonl=args.log_jsonl,
        )
    )
    guardian.start()
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        guardian.stop()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
