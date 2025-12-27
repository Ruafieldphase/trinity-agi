#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binoche Note Intake (AGI Inbox) v1

목표
- 사용자가 남긴 "짧은 메모"를 시스템이 받아서(질문 없이)
  탐색 세션으로 물질화(materialize)한다.
- 이 메모는 '대화 원문 저장'이 아니라, 경계/리듬 습득을 위한
  저용량 메타 신호로 취급한다.

입력
- signals/binoche_note.json
  {
    "text": "...",          # 사용자 입력(최대 길이 제한 + redaction 적용)
    "timestamp":  ...,
    "origin": "binoche"
  }

출력
- outputs/bridge/binoche_note_intake_latest.json
- outputs/bridge/binoche_note_intake_history.jsonl
- inputs/intake/exploration/sessions/auto_experience_<ts>_binoche_note.json

원칙
- 네트워크 호출 없음
- PII/URL/경로 등은 저장 전에 마스킹
- 실패해도 latest 파일은 생성(best-effort)
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WORKSPACE = Path(__file__).resolve().parents[2]
SIGNALS = WORKSPACE / "signals"
OUTPUTS = WORKSPACE / "outputs"
BRIDGE = OUTPUTS / "bridge"
SESSIONS = WORKSPACE / "inputs" / "intake" / "exploration" / "sessions"

IN_NOTE = SIGNALS / "binoche_note.json"
OUT_LATEST = BRIDGE / "binoche_note_intake_latest.json"
OUT_HISTORY = BRIDGE / "binoche_note_intake_history.jsonl"

CONSTITUTION = BRIDGE / "constitution_review_latest.json"
REST_GATE = OUTPUTS / "safety" / "rest_gate_latest.json"


def _utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        obj = json.loads(path.read_text(encoding="utf-8-sig"))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _cap(s: str, n: int = 280) -> str:
    s = (s or "").strip()
    if len(s) <= n:
        return s
    return s[:n].rstrip() + "…"


def _redact_text(s: str) -> str:
    """
    URL/Email/Path 마스킹 (Windows + Linux/Mac 경로 지원)
    """
    s = (s or "").strip()
    if not s:
        return ""
    # URL (http/https)
    s = re.sub(r"https?://[^\s)\]]+", "[REDACTED_URL]", s, flags=re.IGNORECASE)
    # Email
    s = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", s)
    # Windows path (C:\, D:\, etc.)
    s = re.sub(r"\b[A-Za-z]:\\[^\s]+", "[REDACTED_PATH]", s)
    # Linux/Mac path (/home/, /Users/, /var/, /etc/, etc.)
    s = re.sub(r"/(home|Users|var|etc|opt|tmp|usr)/[^\s]+", "[REDACTED_PATH]", s)
    return s


def _get_safety_status() -> str:
    c = _load_json(CONSTITUTION) or {}
    st = str((c.get("status") or "")).upper().strip()
    return st or "UNKNOWN"


def _rest_gate_active(now: float) -> bool:
    rg = _load_json(REST_GATE) or {}
    try:
        if isinstance(rg, dict) and str(rg.get("status") or "").upper() == "REST":
            until = rg.get("rest_until_epoch")
            if until is None:
                return True
            if isinstance(until, (int, float)) and now < float(until):
                return True
    except Exception:
        return False
    return False


def _detect_boundary_keywords(text: str) -> list[str]:
    """
    경계 씨앗 키워드 감지 (확장/수축/혼합/경계/여백)
    원문은 저장하지 않고, 메타 태그만 반환
    """
    keywords = []
    text_lower = text.lower()

    # 확장 (expansion)
    if any(kw in text_lower for kw in ["확장", "expansion", "grow", "넓히", "펼치", "열어"]):
        keywords.append("expansion")

    # 수축 (contraction)
    if any(kw in text_lower for kw in ["수축", "contraction", "줄이", "좁히", "닫", "압축"]):
        keywords.append("contraction")

    # 혼합 (mixed)
    if any(kw in text_lower for kw in ["혼합", "mixed", "섞", "균형", "조화"]):
        keywords.append("mixed")

    # 경계 (boundary)
    if any(kw in text_lower for kw in ["경계", "boundary", "한계", "제한", "선"]):
        keywords.append("boundary")

    # 여백 (margin/space)
    if any(kw in text_lower for kw in ["여백", "margin", "space", "쉼", "휴식", "idle"]):
        keywords.append("margin")

    return keywords


def _write_session(now: float, text_redacted: str) -> Path:
    SESSIONS.mkdir(parents=True, exist_ok=True)
    path = SESSIONS / f"auto_experience_{int(now)}_binoche_note.json"

    # 경계 씨앗 키워드 감지 (원문 저장 금지, 메타만)
    boundary_keywords = _detect_boundary_keywords(text_redacted)

    # 기본 태그 + 감지된 경계 키워드
    tags = ["binoche", "message", "boundary_seed"]
    tags.extend(boundary_keywords)

    payload: dict[str, Any] = {
        "source": "binoche_note",
        "title": "binoche_note: user message",
        "tags": tags,
        "notes": _cap(text_redacted, 240),
        "timestamp": float(now),
        "where": {"platform": "windows", "layer": "binoche_note_intake"},
        "who": {"role": "human", "origin": "binoche"},
        "boundaries": [
            {"polarity": "deny", "text": "개인정보/계정/비밀번호/토큰/키 추출·저장 금지"},
            {"polarity": "deny", "text": "대용량 원문 저장 금지(메타/요약만)"},
            {"polarity": "allow", "text": "Idle/쉼/여백은 정상 생존"},
            {"polarity": "caution", "text": "메모는 경계 씨앗(seed)이며, 맥락에 따라 강화/감쇠한다"},
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_binoche_note_intake(workspace_root: Path) -> dict[str, Any]:
    now = time.time()
    BRIDGE.mkdir(parents=True, exist_ok=True)

    if not IN_NOTE.exists():
        res = {"ok": True, "skipped": True, "reason": "no_note", "timestamp_utc": _utc_iso(now)}
        _atomic_write_json(OUT_LATEST, res)
        _append_jsonl(OUT_HISTORY, res)
        return res

    # We always accept note even under BLOCK/REST, but we do NOT expand actions here.
    safety = _get_safety_status()
    rest = _rest_gate_active(now)

    note = _load_json(IN_NOTE) or {}
    raw = str(note.get("text") or "")
    red = _cap(_redact_text(raw), 600)
    if not red:
        try:
            IN_NOTE.unlink(missing_ok=True)
        except Exception:
            pass
        res = {"ok": True, "skipped": True, "reason": "empty_after_redaction", "timestamp_utc": _utc_iso(now)}
        _atomic_write_json(OUT_LATEST, res)
        _append_jsonl(OUT_HISTORY, res)
        return res

    session_path = _write_session(now, text_redacted=red)

    # consume signal
    try:
        IN_NOTE.unlink(missing_ok=True)
    except Exception:
        pass

    res = {
        "ok": True,
        "timestamp_utc": _utc_iso(now),
        "safety": safety,
        "rest_gate_active": bool(rest),
        "created_session_file": str(session_path),
        "text_preview": _cap(red, 120),
    }
    _atomic_write_json(OUT_LATEST, res)
    _append_jsonl(OUT_HISTORY, res)
    return res


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=str, default=str(WORKSPACE))
    args = ap.parse_args()
    res = run_binoche_note_intake(Path(args.workspace).resolve())
    print(json.dumps({"ok": bool(res.get("ok")), "created": bool(res.get("created_session_file")), "reason": res.get("reason")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

