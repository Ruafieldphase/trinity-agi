#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exploration Intake (Geo/Sound)

목표:
- 사용자가 '탐색(Exploration)' 목적으로 수집한 세션 데이터(JSON)와 미디어(영상/사운드)를
  자율 루프가 인지할 수 있도록 스캔하여 메타데이터를 통합한다.
- Google Earth, Street View, Local Sound, Youtube Local File 등

입력:
- 세션: inputs/intake/exploration/sessions/*.json
- 미디어: inputs/intake/exploration/media/*

출력:
- outputs/exploration_intake_latest.json
- outputs/exploration_intake_history.jsonl
"""

from __future__ import annotations

import argparse
import json
import time
import os
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Dict, Optional
import sys
from workspace_root import get_workspace_root
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


# --- Configuration ---
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

def guess_kind(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in VIDEO_EXT: return "video"
    if ext in AUDIO_EXT: return "audio"
    if ext in IMAGE_EXT: return "image"
    return "other"

@dataclass
class ExplorationSession:
    """사용자가 작성한 탐색 세션 정보"""
    path: str
    filename: str
    source: str          # google_earth | street_view | youtube_local | other
    title: str
    tags: List[str]
    notes: str
    timestamp: float     # 사용자 기입 타임스탬프 (없으면 파일 mtime)
    mtime_iso: str       # 파일 수정 시간
    where: Dict[str, Any] = field(default_factory=dict)  # 예: {"country":"JP","city":"Tokyo","lat":...,"lon":...}
    who: Dict[str, Any] = field(default_factory=dict)    # 예: {"role":"Binoche_Observer","mode":"observer"}
    boundaries: List[Dict[str, Any]] = field(default_factory=list)  # allow/deny 규칙(선택)
    comparisons: List[Dict[str, Any]] = field(default_factory=list) # 비교/차이(선택)

@dataclass
class ExplorationMedia:
    """탐색 관련 미디어 파일 메타데이터"""
    path: str
    relpath: str
    kind: str            # video | audio | image | other
    size: int
    mtime_iso: str

@dataclass
class ExplorationSummary:
    ok: bool
    scanned_at: str
    session_count: int
    media_count: int
    sessions: List[Dict[str, Any]]
    media: List[Dict[str, Any]]
    latest_session: Optional[Dict[str, Any]] = None

def _extract_boundaries_from_text(text: str) -> List[Dict[str, Any]]:
    """
    아주 가벼운 휴리스틱 기반 경계 추출.
    - 목적: '학습/모델 호출' 없이도 when/where/who 기반 경계 입력이 존재함을 시스템이 인지하게 하기.
    - 정확도보다 "관측 가능성" 우선 (사람이 세션 파일에 명시하면 더 정확해진다).
    """
    rules: List[Dict[str, Any]] = []
    if not text:
        return rules

    deny_markers = ("하면 안", "하지 말", "금지", "불가", "조심", "주의")
    allow_markers = ("해도 됨", "가능", "허용", "괜찮", "된다")

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        polarity = None
        if any(m in line for m in deny_markers):
            polarity = "deny"
        elif any(m in line for m in allow_markers):
            polarity = "allow"
        if polarity:
            rules.append({"polarity": polarity, "text": line})
        if len(rules) >= 30:
            break
    return rules


def load_session_file(path: Path) -> Optional[ExplorationSession]:
    """
    세션 파일 로더.
    - *.json: 구조화된 세션
    - *.md/*.txt: 비구조화 메모 (제목=첫 줄 or 파일명, notes=본문)
    """
    try:
        st = path.stat()
        suffix = path.suffix.lower()

        data: Dict[str, Any] = {}
        notes = ""
        title = ""

        if suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            notes = data.get("notes", "") if isinstance(data, dict) else ""
            title = data.get("title", "") if isinstance(data, dict) else ""
        elif suffix in (".md", ".txt"):
            content = path.read_text(encoding="utf-8", errors="replace")
            notes = content.strip()
            first = (content.splitlines()[0].strip() if content.splitlines() else "")
            title = first if first else path.stem
            data = {"source": "travel_note" if suffix == ".md" else "note"}
        else:
            return None

        if not title:
            title = path.stem

        # 스키마 매핑 (유연하게)
        timestamp = data.get("timestamp")
        if not isinstance(timestamp, (int, float)):
            timestamp = st.st_mtime

        tags = data.get("tags", [])
        if not isinstance(tags, list):
            tags = []

        where = data.get("where", {})
        if not isinstance(where, dict):
            where = {}

        who = data.get("who", {})
        if not isinstance(who, dict):
            who = {}

        boundaries = data.get("boundaries", [])
        if not isinstance(boundaries, list):
            boundaries = []

        comparisons = data.get("comparisons", [])
        if not isinstance(comparisons, list):
            comparisons = []

        # 비구조화 메모에서는 notes에서 간단 규칙 추출을 붙인다.
        if suffix in (".md", ".txt") and notes:
            extracted = _extract_boundaries_from_text(notes)
            if extracted:
                boundaries = list(boundaries) + extracted

        return ExplorationSession(
            path=str(path),
            filename=path.name,
            source=str(data.get("source", "other")),
            title=str(title),
            tags=[str(x) for x in tags if isinstance(x, (str, int, float))],
            notes=str(notes) if isinstance(notes, str) else "",
            timestamp=float(timestamp),
            mtime_iso=utc_iso(st.st_mtime),
            where=where,
            who=who,
            boundaries=[b for b in boundaries if isinstance(b, dict)],
            comparisons=[c for c in comparisons if isinstance(c, dict)],
        )
    except Exception:
        return None

def scan_exploration(workspace_root: Path) -> ExplorationSummary:
    bg_root = workspace_root / "inputs" / "intake" / "exploration"
    session_dir = bg_root / "sessions"
    media_dir = bg_root / "media"

    # 1. Scan Sessions
    sessions: List[ExplorationSession] = []
    if session_dir.exists():
        for p in session_dir.rglob("*"):
            if not p.is_file():
                continue
            # 템플릿/비활성 파일은 스캔에서 제외
            if p.name.startswith(("_", ".")):
                continue
            if p.suffix.lower() not in (".json", ".md", ".txt"):
                continue
            s = load_session_file(p)
            if s:
                sessions.append(s)
    
    # Sort by timestamp desc
    sessions.sort(key=lambda x: x.timestamp, reverse=True)

    # 2. Scan Media
    media_items: List[ExplorationMedia] = []
    if media_dir.exists():
        for p in media_dir.rglob("*"):
            if not p.is_file(): continue
            try:
                st = p.stat()
                media_items.append(ExplorationMedia(
                    path=str(p),
                    relpath=str(p.relative_to(workspace_root)),
                    kind=guess_kind(p),
                    size=st.st_size,
                    mtime_iso=utc_iso(st.st_mtime)
                ))
            except Exception:
                continue
    
    # Sort media by mtime desc
    # (mtime_iso 문자열 정렬로 충분)
    media_items.sort(key=lambda x: x.mtime_iso, reverse=True)

    summary = ExplorationSummary(
        ok=True,
        scanned_at=utc_iso(time.time()),
        session_count=len(sessions),
        media_count=len(media_items),
        sessions=[asdict(s) for s in sessions[:50]], # 최근 50개만
        media=[asdict(m) for m in media_items[:100]], # 최근 100개만
        latest_session=asdict(sessions[0]) if sessions else None
    )
    
    return summary

def run_exploration_intake(workspace_root: Path) -> dict:
    summary = scan_exploration(workspace_root)
    return asdict(summary)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=str, default=str(get_workspace_root()))
    args = ap.parse_args()
    
    ws = Path(args.workspace).resolve()
    result = run_exploration_intake(ws)
    
    # Save Output
    out_file = ws / "outputs" / "exploration_intake_latest.json"
    hist_file = ws / "outputs" / "exploration_intake_history.jsonl"
    
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    
    try:
        with hist_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
    except Exception:
        pass
        
    print(json.dumps({"ok": True, "out": str(out_file), "count": result["session_count"]}))

if __name__ == "__main__":
    main()
