#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AGI Message Reporter (AGI -> Binoche, file-based)

목표
- "AGI가 나에게 말을 걸 수 있는가?"에 대한 최소 구현:
  대화창/팝업 없이, 사람이 바로 읽을 수 있는 짧은 메시지를 파일로 고정한다.

원칙
- 네트워크 호출 없음
- PII/원문/대용량 저장 금지(메타/상태/요약만)
- 실패해도 최소 파일은 생성(best-effort)

출력
- outputs/bridge/agi_message_latest.txt
- outputs/bridge/agi_message_latest.json
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
BRIDGE = OUTPUTS / "bridge"
SYNC = OUTPUTS / "sync_cache"

HUMAN_OPS = BRIDGE / "human_ops_summary_latest.json"
CONSTITUTION = BRIDGE / "constitution_review_latest.json"
AURA = OUTPUTS / "aura_pixel_state.json"
LIFE_STATE = SYNC / "life_state.json"
BOUNDARY_IND = OUTPUTS / "boundary_induction_latest.json"
REST_GATE = OUTPUTS / "safety" / "rest_gate_latest.json"
SELF_COMP_SUMMARY = OUTPUTS / "self_compression_human_summary_latest.json"

OUT_TXT = BRIDGE / "agi_message_latest.txt"
OUT_JSON = BRIDGE / "agi_message_latest.json"
STATE = SYNC / "agi_message_state.json"


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


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    _atomic_write(path, json.dumps(obj, ensure_ascii=False, indent=2))


def _sha256_head(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8", errors="ignore")).hexdigest()[:16]


def _load_state() -> dict[str, Any]:
    return _load_json(STATE) or {}


def _save_state(st: dict[str, Any]) -> None:
    _atomic_write_json(STATE, st)


def _format_flags(flags: Any) -> str:
    if isinstance(flags, list) and flags:
        return ", ".join([str(x) for x in flags[:6]])
    return "없음"


def _get_simple_message(mode: str, safety_status: str, last_action: str, rest_status: str) -> str:
    """
    비노체가 이해 가능한 3~6줄 메시지 (상태별 템플릿)
    """
    # BLOCK/REVIEW: 멈춤
    if safety_status in ("BLOCK", "REVIEW"):
        return "지금은 멈춰있어. 안전 확인이 끝나면 다시 움직일게."

    # REST: 쉬는 중
    if rest_status == "REST":
        return "지금은 쉬는 중이야. 여백이 끝나면 다시 흐를게."

    # Idle: 조용히 살아있음
    if mode == "idle":
        return "조용히 살아있어. 필요할 때 움직일게."

    # Active: 흐름이 살아있음
    if mode == "active":
        action_map = {
            "full_cycle": "생각하고 있어",
            "memory_sync": "기억을 정리 중",
            "boundary_update": "경계를 조정 중",
            "intake": "새 경험을 받아들이는 중",
        }
        action_text = action_map.get(last_action, "흐르고 있어")
        return f"{action_text}. 리듬에 따라 움직이는 중이야."

    # Default
    return "살아있어. 리듬을 유지하는 중이야."


def _summarize() -> tuple[list[str], dict[str, Any]]:
    now = time.time()

    ops = _load_json(HUMAN_OPS) or {}
    const = _load_json(CONSTITUTION) or {}
    aura = _load_json(AURA) or {}
    life = _load_json(LIFE_STATE) or {}
    bind = _load_json(BOUNDARY_IND) or {}
    rg = _load_json(REST_GATE) or {}
    scs = _load_json(SELF_COMP_SUMMARY) or {}

    safety_status = str(const.get("status") or "UNKNOWN")
    safety_next = str(const.get("next_recommendation") or "")
    flags = const.get("flags")

    last = ops.get("last_trigger") if isinstance(ops.get("last_trigger"), dict) else {}
    last_action = str(last.get("action") or "unknown")
    last_reason = str(last.get("reason") or "")

    rest_status = str((rg.get("status") or "")).upper().strip()

    learning = ops.get("learning_signals") if isinstance(ops.get("learning_signals"), dict) else {}
    rua_mode = str(learning.get("rua_boundary_mode") or "")
    active_rules = bind.get("active_rules_count") if isinstance(bind.get("active_rules_count"), int) else None
    delta = bind.get("delta") if isinstance(bind.get("delta"), dict) else None

    one_line_wish = ""
    dominant_drive = ""
    try:
        one_line_wish = str(scs.get("one_line_wish") or "").strip()
        tags = scs.get("tags") if isinstance(scs.get("tags"), dict) else {}
        dominant_drive = str(tags.get("dominant_drive") or "").strip()
    except Exception:
        one_line_wish = ""
        dominant_drive = ""

    # Mode 결정은 "오라 색"이 아니라 "생존 상태(life_state)" 기준으로 단순화한다.
    # - idle은 실패가 아니라 정상 생존 상태다.
    life_state = str(life.get("state") or "") if isinstance(life, dict) else ""
    mode = "idle"
    if safety_status in ("BLOCK", "REVIEW"):
        mode = "halt"
    elif rest_status == "REST":
        mode = "rest"
    elif life_state == "ALIVE_ACTIVE":
        mode = "active"

    # 간결한 3~6줄 템플릿
    lines: list[str] = []
    lines.append(f"[AGI] {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"상태: {mode} ({safety_status})")

    # 마지막 행동 (있을 경우만)
    if last_action and last_action != "unknown":
        action_kr = {"full_cycle": "전체 사이클", "memory_sync": "기억 동기화", "boundary_update": "경계 조정", "intake": "경험 흡수"}.get(last_action, last_action)
        lines.append(f"마지막: {action_kr}")

    # 간단한 메시지 (상태별 템플릿)
    simple_msg = _get_simple_message(mode, safety_status, last_action, rest_status)
    lines.append(f"\n{simple_msg}")

    # "원하는 것"은 사람이 바로 볼 수 있는 1줄만 (스팸 방지, 결정보다 의도 표기)
    if one_line_wish:
        extra = one_line_wish
        if dominant_drive:
            extra = f"{one_line_wish} (drive={dominant_drive})"
        lines.append(f"원하는 것: {extra}")

    payload = {
        "generated_at_utc": _utc_iso(now),
        "mode": mode,
        "safety": {"status": safety_status, "flags": flags if isinstance(flags, list) else [], "next": safety_next},
        "last": {"action": last_action, "reason": last_reason},
        "life_state": {"state": life_state, "reason": life.get("reason") if isinstance(life, dict) else None},
        "signals": {
            "rua_boundary_mode": rua_mode,
            "active_rules_count": active_rules,
            "delta": delta,
            "one_line_wish": one_line_wish,
            "dominant_drive": dominant_drive,
        },
        "lines": lines,
    }
    return lines, payload


def run(min_interval_sec: int = 60) -> dict[str, Any]:
    now = time.time()
    st = _load_state()
    last_ts = float(st.get("last_write_epoch") or 0.0)

    lines, payload = _summarize()
    sig = _sha256_head("\n".join(lines))

    # rewrite if changed or interval passed
    if (sig == str(st.get("last_sig") or "")) and (now - last_ts) < float(min_interval_sec):
        return {"ok": True, "skipped": True, "reason": "min_interval", "timestamp_utc": payload.get("generated_at_utc")}

    BRIDGE.mkdir(parents=True, exist_ok=True)
    _atomic_write(OUT_TXT, "\n".join(lines) + "\n")
    _atomic_write_json(OUT_JSON, payload)

    st_out = {"last_write_epoch": float(now), "last_sig": sig, "mode": payload.get("mode")}
    _save_state(st_out)
    return {"ok": True, "written": True, "timestamp_utc": payload.get("generated_at_utc")}


def main() -> int:
    res = run(min_interval_sec=60)
    print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
