#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Media Intake (Self-Acquisition helper)

목표:
- 비노체의 영상/오디오/이미지(예: 자전거 서울 영상 80개)를 '자율 루프가 읽을 수 있는 형태'로
  최소한의 메타데이터(파일 목록/수정시각/크기/태그)를 고정한다.
- 외부 네트워크/무거운 디코딩 없이 표준 라이브러리만으로 동작한다.

입력:
- 기본 스캔 루트: `<workspace>/inputs/media`
  (필요 시 환경변수 `AGI_MEDIA_INPUT_DIRS`로 추가 루트 지정 가능; ; 로 구분)

출력:
- `<workspace>/outputs/media_intake_latest.json`
- `<workspace>/outputs/media_intake_history.jsonl` (append)
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import sys
from workspace_root import get_workspace_root
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))



VIDEO_EXT = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def guess_kind(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in VIDEO_EXT:
        return "video"
    if ext in AUDIO_EXT:
        return "audio"
    if ext in IMAGE_EXT:
        return "image"
    return "other"


def split_dirs(raw: str) -> list[str]:
    items = []
    for part in (raw or "").split(";"):
        p = part.strip()
        if p:
            items.append(p)
    return items


def extract_tags(path: Path, root: Path, max_tags: int = 12) -> list[str]:
    try:
        rel = path.relative_to(root)
    except Exception:
        rel = path
    parts = [p for p in rel.parts[:-1] if p and p not in (".", "..")]
    tags: list[str] = []
    for p in parts:
        t = str(p).strip()
        if not t:
            continue
        tags.append(t)
        if len(tags) >= max_tags:
            break
    return tags


@dataclass
class MediaEntry:
    path: str
    relpath: str
    kind: str
    ext: str
    size: int
    mtime: float
    mtime_iso: str
    tags: list[str]


def load_latest(latest_path: Path) -> dict[str, Any]:
    if not latest_path.exists():
        return {}
    try:
        obj = json.loads(latest_path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def scan_media_roots(workspace_root: Path, roots: list[Path]) -> dict[str, Any]:
    latest_path = workspace_root / "outputs" / "media_intake_latest.json"
    prev = load_latest(latest_path)
    prev_paths = set()
    try:
        for e in prev.get("files", []):
            p = e.get("relpath") or e.get("path")
            if isinstance(p, str) and p:
                prev_paths.add(p)
    except Exception:
        prev_paths = set()

    files: list[MediaEntry] = []
    skipped_dirs: list[str] = []

    for root in roots:
        if not root.exists():
            continue
        try:
            for path in root.rglob("*"):
                try:
                    if path.is_dir():
                        continue
                except Exception:
                    continue

                try:
                    st = path.stat()
                except Exception:
                    continue

                kind = guess_kind(path)
                rel = str(path.relative_to(workspace_root)) if str(path).startswith(str(workspace_root)) else str(path)
                entry = MediaEntry(
                    path=str(path),
                    relpath=rel,
                    kind=kind,
                    ext=path.suffix.lower(),
                    size=int(st.st_size),
                    mtime=float(st.st_mtime),
                    mtime_iso=utc_iso(float(st.st_mtime)),
                    tags=extract_tags(path, root),
                )
                files.append(entry)
        except Exception:
            skipped_dirs.append(str(root))

    files.sort(key=lambda e: e.mtime, reverse=True)
    new_files = [e.relpath for e in files if e.relpath not in prev_paths]

    counts: dict[str, int] = {"video": 0, "audio": 0, "image": 0, "other": 0}
    for e in files:
        counts[e.kind] = counts.get(e.kind, 0) + 1

    now = time.time()
    newest = files[0] if files else None
    summary = {
        "ok": True,
        "scanned_at": utc_iso(now),
        "workspace": str(workspace_root),
        "roots": [str(r) for r in roots],
        "counts": counts,
        "total": len(files),
        "new_files_count": len(new_files),
        "new_files": new_files[:50],
        "newest": asdict(newest) if newest else None,
        "skipped_dirs": skipped_dirs,
        "files": [asdict(e) for e in files[:200]],
        "note": "files에는 최근 200개만 포함(요약). 전체는 roots에서 재스캔 가능.",
    }
    return summary


def run_media_intake(workspace_root: Path) -> dict[str, Any]:
    workspace_root = workspace_root.resolve()
    default_root = workspace_root / "inputs" / "media"
    extra = split_dirs(os.environ.get("AGI_MEDIA_INPUT_DIRS", ""))
    roots = [default_root] + [Path(p).expanduser() for p in extra]
    return scan_media_roots(workspace_root, roots)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=str, default=str(get_workspace_root()))
    ap.add_argument("--out", type=str, default=str(Path("outputs") / "media_intake_latest.json"))
    ap.add_argument("--history", type=str, default=str(Path("outputs") / "media_intake_history.jsonl"))
    args = ap.parse_args()

    workspace_root = Path(args.workspace).resolve()
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = (workspace_root / out_path).resolve()
    hist_path = Path(args.history)
    if not hist_path.is_absolute():
        hist_path = (workspace_root / hist_path).resolve()

    result = run_media_intake(workspace_root)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    try:
        with hist_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
    except Exception:
        pass

    print(json.dumps({"ok": True, "out": str(out_path), "total": result.get("total")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

