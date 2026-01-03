#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Drive State Update (best-effort, local-only)

목표:
- "호기심/지루함/욕망(drives)"이 비어 보이는 문제를 해결하기 위해,
  현재 워크스페이스의 관측 신호(파일 age/안전/ATP)를 기반으로
  memory/agi_internal_state.json에 최소한의 drive 상태를 갱신한다.

원칙:
- 네트워크 사용 없음
- 원문/PII 저장 금지(메타/숫자만)
- 실패해도 조용히 종료(best-effort)
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from workspace_root import get_workspace_root


ROOT = get_workspace_root()
OUTPUTS = ROOT / "outputs"
BRIDGE = OUTPUTS / "bridge"
MEMORY = ROOT / "memory"

INTERNAL_STATE = MEMORY / "agi_internal_state.json"
MITO = OUTPUTS / "mitochondria_state.json"
REST_GATE = OUTPUTS / "safety" / "rest_gate_latest.json"
CONSTITUTION = BRIDGE / "constitution_review_latest.json"
EXPL_EVENT = OUTPUTS / "exploration_session_event_latest.json"
TRIGGER_LATEST = BRIDGE / "trigger_report_latest.json"


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8", errors="replace") or "{}")
    except Exception:
        return {}


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        pass


def _file_age_s(path: Path, now: float) -> float | None:
    try:
        if not path.exists():
            return None
        return max(0.0, now - float(path.stat().st_mtime))
    except Exception:
        return None


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _atp_to_energy(atp: float | None) -> float:
    if atp is None:
        return 0.5
    # 경험적으로 0~100 범위로 오는 값이 많아 간단히 정규화한다.
    return _clamp01(float(atp) / 100.0)


@dataclass
class DriveVector:
    explore: float
    avoid: float
    self_focus: float
    connect: float
    rest: float

    def as_dict(self) -> dict[str, float]:
        return {
            "explore": float(self.explore),
            "avoid": float(self.avoid),
            "self_focus": float(self.self_focus),
            "connect": float(self.connect),
            "rest": float(self.rest),
        }


def compute_drives(now: float) -> tuple[float, float, DriveVector, dict[str, Any]]:
    mito = _load_json(MITO)
    atp = None
    try:
        atp = float(mito.get("atp_level"))
    except Exception:
        atp = None
    energy = _atp_to_energy(atp)

    rg = _load_json(REST_GATE)
    rest_status = str(rg.get("status") or "").upper().strip()

    c = _load_json(CONSTITUTION)
    cstat = str(c.get("status") or "").upper().strip()

    last_action = ""
    try:
        tr = _load_json(TRIGGER_LATEST)
        last_action = str(tr.get("action") or "")
    except Exception:
        last_action = ""

    explore_age = _file_age_s(EXPL_EVENT, now)
    # 탐색이 오래 없으면 지루함↑, 최근 탐색이면 호기심↑
    # (정확도보다 관측 가능성/일관성 우선)
    if explore_age is None:
        boredom = 0.55
        curiosity = 0.45
    else:
        # 0~6h를 0~1로 매핑(6h 이상이면 1)
        boredom = _clamp01(explore_age / (6 * 3600.0))
        # 최근 30분 이내면 1, 3시간 넘어가면 0에 가깝게
        curiosity = _clamp01(1.0 - (explore_age / (3 * 3600.0)))

    # RestGate가 켜져 있으면 "휴식"이 지배적이어야 한다.
    rest_drive = 1.0 if rest_status == "REST" else _clamp01(1.0 - energy + 0.25)

    # Safety가 불안정하면 avoid↑
    avoid = 0.0
    if cstat in {"BLOCK", "REVIEW"}:
        avoid = 0.9
    elif cstat == "CAUTION":
        avoid = 0.6

    # explore는 에너지와 지루함의 함수(단, avoid/rest가 높으면 억제)
    explore = _clamp01((0.55 * energy) + (0.65 * boredom) - (0.6 * avoid) - (0.5 * max(0.0, rest_drive - 0.6)))

    # self_focus는 최근 self_compress/heartbeat_check가 많을수록↑ (단순히 last_action 기반)
    self_focus = 0.35
    if last_action in {"self_compress", "heartbeat_check"}:
        self_focus = 0.55
    if last_action == "full_cycle":
        self_focus = 0.45

    # connect는 현재는 입력 채널이 없으므로 낮게 유지(추후 binoche_note/대화 인테이크로 강화 가능)
    connect = 0.15

    # 정규화(완전 합 1 강제는 하지 않고, 0~1의 강도 벡터로 유지)
    drives = DriveVector(
        explore=_clamp01(explore),
        avoid=_clamp01(avoid),
        self_focus=_clamp01(self_focus),
        connect=_clamp01(connect),
        rest=_clamp01(rest_drive),
    )

    debug = {
        "atp_level": atp,
        "energy": energy,
        "exploration_event_age_s": explore_age,
        "rest_gate": rest_status,
        "constitution": cstat,
        "last_action": last_action,
    }
    return energy, boredom, drives, debug


def main() -> int:
    now = time.time()
    prev = _load_json(INTERNAL_STATE)
    if not isinstance(prev, dict):
        prev = {}

    energy, boredom, drives, debug = compute_drives(now)
    # curiosity는 compute_drives 내부에서 계산됐지만 외부로 반환하지 않았으므로 debug에서 다시 계산 X.
    # 대신 boredom/energy/drives로 1차 관측을 제공한다.

    # Preserve existing self_expansion section if present
    merged = dict(prev)
    merged["last_drive_update_utc"] = _utc_now()
    merged["energy"] = float(round(energy, 3))
    # boredom/curiosity는 0~1 스케일로 저장(태그는 human_summary에서 문자열화)
    merged["boredom"] = float(round(boredom, 3))
    # curiosity는 explore 이벤트 age 기반으로 간접 생성(동일 로직 재계산)
    explore_age = debug.get("exploration_event_age_s")
    if isinstance(explore_age, (int, float)):
        curiosity = _clamp01(1.0 - (float(explore_age) / (3 * 3600.0)))
    else:
        curiosity = 0.45
    merged["curiosity"] = float(round(curiosity, 3))
    merged["drives"] = drives.as_dict()
    merged.setdefault("meta", {})
    if isinstance(merged["meta"], dict):
        merged["meta"]["drive_debug"] = debug

    _write_json(INTERNAL_STATE, merged)
    print(json.dumps({"ok": True, "out": str(INTERNAL_STATE)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

