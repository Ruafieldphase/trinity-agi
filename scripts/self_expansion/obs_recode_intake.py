#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OBS Recode Intake (Behavior Data Index)

목표:
- OBS 화면 녹화(키/마우스 오버레이 포함 가능)를 "학습/분석용 원본"으로 보존하되,
  자율 루프가 부담 없이 인지할 수 있도록 '메타데이터 인덱스'만 고정한다.
- 무거운 프레임 추출/모델 호출은 여기서 하지 않는다. (원본은 그대로 둔다)

입력(자동 탐색):
- <workspace>/input/obs_recode
- <workspace>/inputs/obs_recode
- (Windows) E:\\Backup\\obs_recode
- (옵션) 환경변수 AGI_OBS_RECODE_DIRS 로 추가 지정
  - 구분자: ; 또는 : (둘 다 지원)

출력:
- <workspace>/outputs/obs_recode_intake_latest.json
- <workspace>/outputs/obs_recode_intake_history.jsonl (append)
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import sys
from workspace_root import get_workspace_root
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))



VIDEO_EXT = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}


def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _append_task_log(path: Path, line: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(line.rstrip() + "\n")
    except Exception:
        return


def split_dirs(raw: str) -> list[str]:
    items: list[str] = []
    if not raw:
        return items
    # 지원: ; 또는 :
    for sep in (";", ":"):
        raw = raw.replace(sep, ";")
    for part in raw.split(";"):
        p = part.strip()
        if p:
            items.append(p)
    return items


def _default_windows_obs_backup() -> Optional[Path]:
    # 사용자가 제공한 대표 경로. 존재하면 자동 포함.
    try:
        p = Path(r"E:\Backup\obs_recode")
        return p if p.exists() else None
    except Exception:
        return None


def resolve_roots(workspace_root: Path) -> list[Path]:
    roots: list[Path] = []
    candidates = [
        workspace_root / "input" / "obs_recode",
        workspace_root / "inputs" / "obs_recode",
    ]
    wb = _default_windows_obs_backup()
    if wb:
        candidates.append(wb)

    extra = split_dirs(os.environ.get("AGI_OBS_RECODE_DIRS", ""))
    candidates.extend(Path(p).expanduser() for p in extra)

    seen = set()
    for c in candidates:
        try:
            cp = c.resolve()
        except Exception:
            cp = c
        key = str(cp).lower()
        if key in seen:
            continue
        seen.add(key)
        roots.append(cp)
    return roots


@dataclass
class ObsRecodeEntry:
    path: str
    relpath: str
    ext: str
    size: int
    mtime: float
    mtime_iso: str


def _safe_load_json(path: Path) -> Optional[dict[str, Any]]:
    if not path.exists():
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def load_latest_obs_recode_intake(workspace_root: Path) -> Optional[dict[str, Any]]:
    """이미 생성된 최신 인덱스를 읽는다(예: Windows 백그라운드 인덱서가 생성)."""
    p = workspace_root / "outputs" / "obs_recode_intake_latest.json"
    return _safe_load_json(p)


def run_obs_recode_intake(workspace_root: Path, max_files: int = 200) -> dict[str, Any]:
    workspace_root = workspace_root.resolve()
    roots = resolve_roots(workspace_root)

    latest_path = workspace_root / "outputs" / "obs_recode_intake_latest.json"
    prev = _safe_load_json(latest_path) or {}
    prev_paths = set()
    try:
        for e in prev.get("files", []):
            rp = e.get("relpath") or e.get("path")
            if isinstance(rp, str) and rp:
                prev_paths.add(rp)
    except Exception:
        prev_paths = set()

    entries: list[ObsRecodeEntry] = []
    skipped_dirs: list[str] = []

    for root in roots:
        if not root.exists():
            continue
        try:
            # 기본은 재귀 스캔(폴더 구조가 깊은 경우가 많음).
            for path in root.rglob("*"):
                try:
                    if path.is_dir():
                        continue
                except Exception:
                    continue

                ext = path.suffix.lower()
                if ext not in VIDEO_EXT:
                    continue

                try:
                    st = path.stat()
                except Exception:
                    continue

                rel = (
                    str(path.relative_to(workspace_root))
                    if str(path).startswith(str(workspace_root))
                    else str(path)
                )
                entries.append(
                    ObsRecodeEntry(
                        path=str(path),
                        relpath=rel,
                        ext=ext,
                        size=int(st.st_size),
                        mtime=float(st.st_mtime),
                        mtime_iso=utc_iso(float(st.st_mtime)),
                    )
                )
        except Exception:
            skipped_dirs.append(str(root))

    entries.sort(key=lambda e: e.mtime, reverse=True)
    newest = entries[0] if entries else None
    new_files = [e.relpath for e in entries if e.relpath not in prev_paths]

    now = time.time()
    summary: dict[str, Any] = {
        "ok": True,
        "scanned_at": utc_iso(now),
        "workspace": str(workspace_root),
        "roots": [str(r) for r in roots],
        "total": len(entries),
        "new_files_count": len(new_files),
        "new_files": new_files[:50],
        "newest": asdict(newest) if newest else None,
        "skipped_dirs": skipped_dirs,
        "files": [asdict(e) for e in entries[:max_files]],
        "safety": {
            "raw_files_copied": False,
            "content_analysis": "none",
            "note": "이 인덱스는 메타데이터만 포함한다(프레임/오디오 추출 없음).",
        },
        "note": f"files에는 최근 {max_files}개만 포함(요약). 원본은 roots에 그대로 존재.",
    }
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=str, default=str(get_workspace_root()))
    ap.add_argument("--out", type=str, default=str(Path("outputs") / "obs_recode_intake_latest.json"))
    ap.add_argument("--history", type=str, default=str(Path("outputs") / "obs_recode_intake_history.jsonl"))
    ap.add_argument("--task-log", type=str, default=str(Path("outputs") / "obs_recode_intake_task.log"))
    ap.add_argument("--max-files", type=int, default=200)
    args = ap.parse_args()

    workspace_root = Path(args.workspace).resolve()
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = (workspace_root / out_path).resolve()
    hist_path = Path(args.history)
    if not hist_path.is_absolute():
        hist_path = (workspace_root / hist_path).resolve()

    task_log = Path(getattr(args, "task_log", str(Path("outputs") / "obs_recode_intake_task.log")))
    if not task_log.is_absolute():
        task_log = (workspace_root / task_log).resolve()

    try:
        result = run_obs_recode_intake(workspace_root, max_files=int(args.max_files))
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

        try:
            with hist_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
        except Exception:
            pass

        newest = result.get("newest") if isinstance(result.get("newest"), dict) else {}
        newest_path = str(newest.get("relpath") or newest.get("path") or "")
        _append_task_log(
            task_log,
            f"{utc_iso(time.time())} ok total={result.get('total')} new_files={result.get('new_files_count')} newest={newest_path}",
        )
        print(json.dumps({"ok": True, "out": str(out_path), "total": result.get("total")}, ensure_ascii=False))
        return 0
    except Exception as e:
        fail = {
            "ok": False,
            "scanned_at": utc_iso(time.time()),
            "workspace": str(workspace_root),
            "error": f"{type(e).__name__}: {e}",
            "note": "obs_recode_intake failed (best-effort).",
        }
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(fail, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
        _append_task_log(task_log, f"{utc_iso(time.time())} error={type(e).__name__}: {e}")
        print(json.dumps({"ok": False, "out": str(out_path), "error": str(e)}, ensure_ascii=False))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
