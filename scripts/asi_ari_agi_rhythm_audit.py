#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASI / ARI / AGI 3층 리듬 점검 (사실 기반)

목표:
- "리듬 기반 vs 고정 폴링" 충돌을 사실(파일/프로세스/스케줄)로만 기록한다.
- 비노체가 터미널/코드 없이도 읽을 수 있게 TXT 요약을 함께 생성한다.

원칙:
- 네트워크 없음
- best-effort: 실패해도 최소 출력 파일 생성
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workspace_root import get_workspace_root


ROOT = get_workspace_root()
OUTPUTS = ROOT / "outputs"
BRIDGE = OUTPUTS / "bridge"

OUT_JSON = BRIDGE / "asi_ari_agi_rhythm_audit_latest.json"
OUT_TXT = BRIDGE / "asi_ari_agi_rhythm_audit_latest.txt"


def _utc_iso_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _load_json_best_effort(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        obj = json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def _file_obs(path: Path) -> dict[str, Any]:
    try:
        st = path.stat()
        return {
            "exists": True,
            "mtime": float(st.st_mtime),
            "mtime_iso_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
            "age_sec": max(0.0, time.time() - float(st.st_mtime)),
            "size": int(st.st_size),
        }
    except Exception:
        return {"exists": False}


def _atomic_write(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    except Exception:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        except Exception:
            return


def _powershell_json(cmd: str, timeout: float = 6.0) -> list[dict[str, Any]]:
    if os.name != "nt":
        return []
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if out.returncode != 0 or not (out.stdout or "").strip():
            return []
        items = json.loads(out.stdout)
        if isinstance(items, dict):
            return [items]
        if isinstance(items, list):
            return [x for x in items if isinstance(x, dict)]
        return []
    except Exception:
        return []


def _list_python_processes() -> list[dict[str, Any]]:
    if os.name == "nt":
        cmd = (
            "Get-CimInstance Win32_Process | "
            "Where-Object { $_.Name -match '^python(\\.exe|w\\.exe)$' } | "
            "Select-Object ProcessId,Name,CommandLine,CreationDate | ConvertTo-Json -Compress"
        )
        items = _powershell_json(cmd, timeout=6.0)
        out: list[dict[str, Any]] = []
        for it in items:
            out.append(
                {
                    "pid": int(it.get("ProcessId") or 0),
                    "name": str(it.get("Name") or ""),
                    "cmd": str(it.get("CommandLine") or ""),
                    "created": str(it.get("CreationDate") or ""),
                }
            )
        return out

    # posix best-effort
    try:
        res = subprocess.run(
            ["bash", "-lc", "ps -eo pid,comm,args | grep -E 'python(3)?' | grep -v grep"],
            capture_output=True,
            text=True,
            timeout=4,
        )
        if res.returncode != 0:
            return []
        out: list[dict[str, Any]] = []
        for line in (res.stdout or "").splitlines():
            line = (line or "").strip()
            if not line:
                continue
            parts = line.split(maxsplit=2)
            if len(parts) < 2:
                continue
            pid = int(parts[0])
            comm = parts[1]
            args = parts[2] if len(parts) > 2 else ""
            out.append({"pid": pid, "name": comm, "cmd": args})
        return out
    except Exception:
        return []


def _find_agi_tasks() -> list[str]:
    if os.name != "nt":
        return []
    try:
        res = subprocess.run(["schtasks", "/Query", "/FO", "LIST"], capture_output=True, text=True, timeout=10)
        if res.returncode != 0:
            return []
        tasks: list[str] = []
        for line in (res.stdout or "").splitlines():
            line = (line or "").strip()
            if not line.lower().startswith("taskname:"):
                continue
            name = line.split(":", 1)[1].strip()
            if "\\AGI" in name:
                tasks.append(name)
        return sorted(set(tasks))
    except Exception:
        return []


def _task_detail(name: str) -> dict[str, Any]:
    if os.name != "nt":
        return {"task": name, "ok": False}
    try:
        res = subprocess.run(["schtasks", "/Query", "/TN", name, "/XML"], capture_output=True, text=True, timeout=10)
        if res.returncode != 0 or not (res.stdout or "").strip():
            return {"task": name, "ok": False}
        root = ET.fromstring(res.stdout)

        ns = ""
        if root.tag.startswith("{") and "}" in root.tag:
            ns = root.tag.split("}", 1)[0].strip("{")

        def _find_text(path: str) -> str | None:
            try:
                node = root.find(path.format(ns=ns))
                if node is None:
                    return None
                t = node.text
                return str(t).strip() if t is not None else None
            except Exception:
                return None

        interval = _find_text(".//{{{ns}}}Repetition/{{{ns}}}Interval")
        command = _find_text(".//{{{ns}}}Exec/{{{ns}}}Command")
        arguments = _find_text(".//{{{ns}}}Exec/{{{ns}}}Arguments")
        hidden = _find_text(".//{{{ns}}}Settings/{{{ns}}}Hidden")
        enabled = _find_text(".//{{{ns}}}Enabled")

        detail: dict[str, Any] = {
            "task": name,
            "ok": True,
            "interval": interval,
            "command": command,
            "arguments": arguments,
            "hidden": hidden,
            "enabled": enabled,
        }
        # Also capture runtime status from schtasks list output (facts: Ready/Running/Disabled).
        try:
            info = subprocess.run(["schtasks", "/Query", "/TN", name, "/FO", "LIST"], capture_output=True, text=True, timeout=8)
            if info.returncode == 0:
                for line in (info.stdout or "").splitlines():
                    line = (line or "").strip()
                    if not line:
                        continue
                    if line.lower().startswith("status:"):
                        detail["status"] = line.split(":", 1)[1].strip()
                    elif line.lower().startswith("next run time:"):
                        detail["next_run_time"] = line.split(":", 1)[1].strip()
                    elif line.lower().startswith("last run time:"):
                        detail["last_run_time"] = line.split(":", 1)[1].strip()
        except Exception:
            pass
        return detail
    except Exception:
        return {"task": name, "ok": False}


_RE_SLEEP = re.compile(r"\b(time|asyncio)\.(sleep)\((?P<arg>[^)]*)\)")
_RE_SLEEP_LITERAL = re.compile(r"^\s*\d+(\.\d+)?\s*$")
_RE_WHILE_TRUE = re.compile(r"^\s*while\s+True\s*:\s*$", re.MULTILINE)
_RE_INTERVAL_CONST = re.compile(r"^\s*[A-Z0-9_]*INTERVAL[A-Z0-9_]*\s*=\s*\d+", re.MULTILINE)


@dataclass
class SleepHit:
    line_no: int
    line: str
    kind: str  # literal | expr


def _scan_sleep_patterns(path: Path) -> dict[str, Any]:
    try:
        txt = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {"ok": False}

    hits: list[SleepHit] = []
    for i, line in enumerate(txt.splitlines(), start=1):
        m = _RE_SLEEP.search(line)
        if not m:
            continue
        arg = (m.group("arg") or "").strip()
        kind = "literal" if _RE_SLEEP_LITERAL.match(arg or "") else "expr"
        hits.append(SleepHit(line_no=i, line=line.strip(), kind=kind))

    return {
        "ok": True,
        "sleep_calls": [{"line": h.line_no, "kind": h.kind, "text": h.line} for h in hits[:20]],
        "sleep_call_count": int(len(hits)),
        "has_while_true": bool(_RE_WHILE_TRUE.search(txt)),
        "has_interval_constant": bool(_RE_INTERVAL_CONST.search(txt)),
    }


def main() -> int:
    BRIDGE.mkdir(parents=True, exist_ok=True)

    processes = _list_python_processes()
    proc_cmds = "\n".join((p.get("cmd") or "") for p in processes)

    components = {
        "ASI": {
            "code": {
                "agi_core/internal_state.py": _file_obs(ROOT / "agi_core" / "internal_state.py"),
                "agi_core/heartbeat_loop.py": _file_obs(ROOT / "agi_core" / "heartbeat_loop.py"),
            },
            "signals": {
                "memory/agi_internal_state.json": _file_obs(ROOT / "memory" / "agi_internal_state.json"),
                "outputs/mitochondria_state.json": _file_obs(OUTPUTS / "mitochondria_state.json"),
                "outputs/safety/rest_gate_latest.json": _file_obs(OUTPUTS / "safety" / "rest_gate_latest.json"),
                "outputs/sync_cache/rhythm_pain_latest.json": _file_obs(OUTPUTS / "sync_cache" / "rhythm_pain_latest.json"),
            },
        },
        "ARI": {
            "code": {
                "services/ari_engine.py": _file_obs(ROOT / "services" / "ari_engine.py"),
                "services/Core_bridge_client.py": _file_obs(ROOT / "services" / "Core_bridge_client.py"),
            },
            "signals": {
                "memory/ari_learning_buffer.json": _file_obs(ROOT / "memory" / "ari_learning_buffer.json"),
                "outputs/feeling_latest.json": _file_obs(OUTPUTS / "feeling_latest.json"),
                "outputs/ari_response.txt": _file_obs(OUTPUTS / "ari_response.txt"),
            },
        },
        "AGI": {
            "code": {
                "scripts/rhythm_think.py": _file_obs(ROOT / "scripts" / "rhythm_think.py"),
                "scripts/trigger_listener.py": _file_obs(ROOT / "scripts" / "trigger_listener.py"),
                "scripts/master_daemon_loop.py": _file_obs(ROOT / "scripts" / "master_daemon_loop.py"),
            },
            "signals": {
                "outputs/thought_stream_latest.json": _file_obs(OUTPUTS / "thought_stream_latest.json"),
                "outputs/natural_rhythm_clock_latest.json": _file_obs(OUTPUTS / "natural_rhythm_clock_latest.json"),
                "outputs/rhythm_health_latest.json": _file_obs(OUTPUTS / "rhythm_health_latest.json"),
                "outputs/bridge/trigger_report_latest.json": _file_obs(BRIDGE / "trigger_report_latest.json"),
            },
        },
    }

    # Daemon/polling scripts scan (scripts/*.py)
    candidates: list[Path] = []
    for p in (ROOT / "scripts").rglob("*.py"):
        name = p.name.lower()
        if any(k in name for k in ("daemon", "loop", "watch", "watchdog", "monitor", "scheduler", "listener")):
            candidates.append(p)
    candidates = sorted(set(candidates))

    daemon_scan: list[dict[str, Any]] = []
    for p in candidates:
        scan = _scan_sleep_patterns(p)
        if not scan.get("ok"):
            continue
        running = str(p).lower() in (proc_cmds or "").lower()
        daemon_scan.append(
            {
                "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                "running": bool(running),
                **scan,
            }
        )

    # Windows scheduled tasks
    tasks = []
    for tname in _find_agi_tasks():
        tasks.append(_task_detail(tname))

    # Build a short human-readable summary (facts only).
    running_named = [
        p for p in processes if any(k in (p.get("cmd") or "").lower() for k in ("\\workspace\\agi\\scripts\\", "/workspace/agi/scripts/"))
    ]

    def _fmt_age(age: float | None) -> str:
        if age is None:
            return "-"
        if age < 60:
            return f"{int(age)}s"
        if age < 3600:
            return f"{int(age // 60)}m"
        return f"{int(age // 3600)}h"

    lines: list[str] = []
    lines.append("ASI/ARI/AGI 리듬 점검(사실 기반)")
    lines.append(f"- 생성: {_utc_iso_now()}")
    lines.append("")
    lines.append("[1] 실행 중 프로세스(python*)")
    if running_named:
        for it in sorted(running_named, key=lambda x: int(x.get("pid") or 0)):
            cmd = str(it.get("cmd") or "")
            cmd_short = cmd.replace(str(ROOT), "<workspace_root>").strip()
            lines.append(f"- pid={it.get('pid')} {it.get('name')}: {cmd_short}")
    else:
        lines.append("- (AGI 관련 python 프로세스 없음)")

    lines.append("")
    lines.append("[2] 3층 핵심 관측 파일")
    for layer in ("ASI", "ARI", "AGI"):
        lines.append(f"- {layer}")
        sigs = components[layer]["signals"]
        for k, v in sigs.items():
            age = v.get("age_sec")
            exists = bool(v.get("exists"))
            lines.append(f"  - {k}: exists={exists} age={_fmt_age(age if isinstance(age, (int, float)) else None)}")

    lines.append("")
    lines.append("[3] AGI_* 스케줄러 작업(Windows)")
    if tasks:
        for t in tasks:
            if not t.get("ok"):
                lines.append(f"- {t.get('task')}: (읽기 실패)")
                continue
            lines.append(
                f"- {t.get('task')}: interval={t.get('interval') or '-'} cmd={t.get('command') or '-'} args={(t.get('arguments') or '-').strip()}"
            )
    else:
        lines.append("- (AGI_* 작업 없음/읽기 실패)")

    lines.append("")
    lines.append("[4] daemon/loop 스크립트 sleep 패턴(요약)")
    shown = 0
    for d in sorted(daemon_scan, key=lambda x: (-int(x.get("sleep_call_count") or 0), x.get("path") or "")):
        if int(d.get("sleep_call_count") or 0) <= 0:
            continue
        if shown >= 12:
            break
        shown += 1
        literals = sum(1 for x in d.get("sleep_calls") or [] if x.get("kind") == "literal")
        exprs = sum(1 for x in d.get("sleep_calls") or [] if x.get("kind") == "expr")
        lines.append(
            f"- {d.get('path')}: running={bool(d.get('running'))} while_true={bool(d.get('has_while_true'))} sleep_calls={int(d.get('sleep_call_count') or 0)} (literal={literals}, expr={exprs})"
        )

    payload = {
        "generated_at_utc": _utc_iso_now(),
        "processes": processes,
        "components": components,
        "windows_tasks": tasks,
        "daemon_sleep_scan": daemon_scan,
    }

    _atomic_write(OUT_JSON, json.dumps(payload, ensure_ascii=False, indent=2))
    _atomic_write(OUT_TXT, "\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
