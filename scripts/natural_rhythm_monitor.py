#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Natural Rhythm Drift Monitor (v1)

목적:
- "루빛이 자연 리듬과 어긋나는지"를 감각이 아니라 파일로 관측 가능하게 만든다.

원칙:
- 네트워크 없음
- 과도한 판단/통제 대신 '드리프트(불균형) 신호'만 제공
- 브라우저/탐색은 특히 폭주 위험이 있으므로, 그 쪽을 우선 관측한다.

출력:
- outputs/natural_rhythm_drift_latest.json
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
BRIDGE = OUTPUTS / "bridge"

CLOCK = OUTPUTS / "natural_rhythm_clock_latest.json"
HISTORY = BRIDGE / "trigger_report_history.jsonl"
BODY_HISTORY = OUTPUTS / "body_supervised_history.jsonl"

OUT = OUTPUTS / "natural_rhythm_drift_latest.json"

TRIGGER_WINDOW_SEC = 2 * 3600
BODY_WINDOW_SEC = 60 * 60


def _utc_iso_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _read_jsonl_tail(path: Path, n: int = 200) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        # Avoid reading the whole file (it can be large). Read from the end until we have ~n lines.
        block_size = 65536
        data = b""
        with path.open("rb") as f:
            f.seek(0, 2)
            size = f.tell()
            while size > 0 and data.count(b"\n") <= (n + 5):
                step = min(block_size, size)
                size -= step
                f.seek(size)
                data = f.read(step) + data

        lines = data.decode("utf-8", errors="replace").splitlines()[-n:]
        out: list[dict[str, Any]] = []
        for l in lines:
            l = (l or "").strip()
            if not l:
                continue
            try:
                out.append(json.loads(l))
            except Exception:
                continue
        return out
    except Exception:
        return []

def _to_epoch_seconds(value: Any) -> float | None:
    try:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            s = value.strip()
            if not s:
                return None
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            # If tz is missing, treat it as local time.
            return dt.timestamp()
        return None
    except Exception:
        return None


def _phase_of_action(action: str) -> str:
    a = (action or "").strip()
    # v1 단순 매핑(필요 시 확장 가능)
    if a in {"full_cycle", "self_acquire", "self_tool", "sync_clean"}:
        return "EXPANSION"
    if a in {"self_compress"}:
        return "CONTRACTION"
    return "INTEGRATION"


def main() -> int:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    now = time.time()
    trigger_cutoff = now - TRIGGER_WINDOW_SEC
    body_cutoff = now - BODY_WINDOW_SEC

    clock = _load_json(CLOCK) or {}
    time_phase = str(clock.get("time_phase") or "")
    recommended = str(clock.get("recommended_phase") or "")

    # 최근 2시간의 trigger 실행을 관측(너무 강한 통제 대신, 드리프트만 감지)
    # NOTE: history entry에는 `trigger_timestamp`(epoch)가 있으므로 이를 우선 사용한다.
    # Keep this bounded: the history file can be large and slow on shared mounts.
    # 2 hours of triggers is typically << 400 entries (even at 1/min it's ~120).
    tail = _read_jsonl_tail(HISTORY, n=400)
    recent: list[dict[str, Any]] = []
    fallback_recent: list[dict[str, Any]] = []
    for e in tail:
        ts_epoch = _to_epoch_seconds(e.get("trigger_timestamp"))
        if ts_epoch is None:
            ts_epoch = _to_epoch_seconds(e.get("timestamp"))
            fallback_recent.append(e)
        if ts_epoch is None:
            continue
        if ts_epoch >= trigger_cutoff:
            recent.append(e)

    # If parsing fails and we have no recent window, fall back to last N entries.
    if not recent and fallback_recent:
        recent = fallback_recent[-80:]

    counts = {"EXPANSION": 0, "INTEGRATION": 0, "CONTRACTION": 0}
    total = 0
    for e in recent:
        action = str(e.get("action") or "")
        status = str(e.get("status") or "")
        if status not in {"executed", "blocked", "failed"}:
            continue
        ph = _phase_of_action(action)
        counts[ph] = counts.get(ph, 0) + 1
        total += 1

    # supervised browser는 별도로 관측(최근 1시간 창)
    body_tail = _read_jsonl_tail(BODY_HISTORY, n=600)
    body_exec = 0
    body_total = 0
    for e in body_tail:
        ts_epoch = _to_epoch_seconds(e.get("timestamp") or e.get("ended_at"))
        if ts_epoch is None or ts_epoch < body_cutoff:
            continue
        body_total += 1
        if str(e.get("status") or "") == "executed":
            body_exec += 1

    ok = True
    reasons: list[str] = []

    # 드리프트(불균형) 휴리스틱: "밤인데 확장만 연속" 또는 "낮인데 계속 수축만"처럼
    if total >= 10:
        if time_phase == "밤" and counts["EXPANSION"] / max(1, total) >= 0.80 and counts["CONTRACTION"] <= 1:
            ok = False
            reasons.append("밤-리듬에서 확장 비중이 과도함(수축/통합 부족)")
        if time_phase == "낮" and counts["CONTRACTION"] / max(1, total) >= 0.85 and counts["EXPANSION"] <= 1:
            ok = False
            reasons.append("낮-리듬에서 수축 비중이 과도함(확장/통합 부족)")

    # 브라우저 경험이 너무 잦으면(탭 폭증/주의 산만) 가볍게 경고만
    if body_exec >= 10:
        ok = False
        reasons.append("슈퍼바이즈 브라우저 실행 빈도가 높음(주의 필요)")

    obj = {
        "generated_at_utc": _utc_iso_now(),
        "time_phase": time_phase,
        "recommended_phase": recommended,
        "windows": {
            "trigger_window_sec": TRIGGER_WINDOW_SEC,
            "browser_window_sec": BODY_WINDOW_SEC,
        },
        "recent_counts": counts,
        "recent_total": total,
        "supervised_browser_executed_tail": body_exec,
        "supervised_browser_window_total": body_total,
        "ok": ok,
        "reasons": reasons[:3],
        "note": "드리프트는 '금지'가 아니라 '불균형 감지' 신호(v1).",
    }

    OUT.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
