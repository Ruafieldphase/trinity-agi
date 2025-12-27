#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suggest Browser Exploration Task (Supervised Body)

목표:
- AGI가 "직접 경험"을 만들 수 있도록, 감독 모드(supervised_body)가 무장(arm)된 경우에만
  `signals/body_task.json`에 안전한 탐색 작업을 1회 제안/생성한다.

안전:
- arm 파일이 없거나 만료되면 아무것도 하지 않는다.
- 기존 body_task.json이 있으면 덮어쓰지 않는다.
- 액션은 URL 기반(open_url/google_search/youtube_search)만 사용한다(클릭/타이핑 없음).
"""

from __future__ import annotations

import json
import os
import time
import ctypes
from pathlib import Path
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[2]
SIGNALS = WORKSPACE / "signals"
OUTPUTS = WORKSPACE / "outputs"
STATE = OUTPUTS / "sync_cache" / "browser_exploration_suggest_state.json"

ARM_FILE = SIGNALS / "body_arm.json"
ALLOW_FILE = SIGNALS / "body_allow_browser.json"
TASK_FILE = SIGNALS / "body_task.json"
STOP_FILE = SIGNALS / "body_stop.json"
CONSTITUTION_JSON = OUTPUTS / "bridge" / "constitution_review_latest.json"
HUMAN_SUMMARY = OUTPUTS / "self_compression_human_summary_latest.json"
REST_GATE = OUTPUTS / "safety" / "rest_gate_latest.json"


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _atomic_create_json(path: Path, payload: dict[str, Any]) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, indent=2)
    try:
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    except FileExistsError:
        return False
    except Exception:
        if path.exists():
            return False
        path.write_text(data, encoding="utf-8")
        return True
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(data)
    return True


def _is_armed(now: float) -> bool:
    # 1) Persistent allow mode (explicit opt-in file)
    allow = _load_json(ALLOW_FILE) or {}
    try:
        if isinstance(allow, dict) and bool(allow.get("allow")):
            exp = allow.get("expires_at")
            if exp is None:
                return True
            if isinstance(exp, (int, float)) and now < float(exp):
                return True
            # expired allow → cleanup
            try:
                if ALLOW_FILE.exists():
                    ALLOW_FILE.unlink()
            except Exception:
                pass
    except Exception:
        pass

    # 2) Arm TTL mode
    arm = _load_json(ARM_FILE) or {}
    try:
        exp = float(arm.get("expires_at") or 0.0)
    except Exception:
        exp = 0.0
    if not (exp and now < exp):
        # Remove expired/stale arm file so "armed" doesn't look stuck.
        try:
            if ARM_FILE.exists():
                ARM_FILE.unlink()
        except Exception:
            pass
        return False
    return True


def _within_allowed_hours(now_ts: float) -> bool:
    """
    Optional time window (local time) from allow file.
    If not configured, allow anytime (still respects idle + cooldown).
    """
    allow = _load_json(ALLOW_FILE) or {}
    if not isinstance(allow, dict):
        return True
    hours = allow.get("allowed_hours_local")
    if not (isinstance(hours, list) and len(hours) == 2):
        return True
    try:
        start_h = int(hours[0])
        end_h = int(hours[1])
    except Exception:
        return True
    if start_h == end_h:
        return True
    lt = time.localtime(now_ts)
    h = int(lt.tm_hour)
    if start_h < end_h:
        return start_h <= h < end_h
    # overnight window
    return h >= start_h or h < end_h


def _idle_seconds() -> float | None:
    """
    사용자가 PC를 쓰지 않는 동안에만 브라우저 탐색을 제안하기 위한 idle 추정.
    """
    try:
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if not user32.GetLastInputInfo(ctypes.byref(lii)):
            return None
        tick = kernel32.GetTickCount()
        return float((tick - lii.dwTime) / 1000.0)
    except Exception:
        return None


def _min_idle_seconds() -> float:
    """
    allow 파일에 설정된 최소 idle 시간(초).
    - 기본값: 120초
    - 0 이하: idle 조건 비활성화
    """
    allow = _load_json(ALLOW_FILE) or {}
    try:
        raw = allow.get("min_idle_seconds")
        if raw is None:
            raw = allow.get("min_idle_sec")
        if raw is None:
            return 120.0
        return max(0.0, float(raw))
    except Exception:
        return 120.0


def _safety_allows_autonomy() -> bool:
    """
    브라우저 탐색은 네트워크가 개입되므로,
    안전 판정이 불안정할 때는 자동 실행을 억제한다.
    """
    c = _load_json(CONSTITUTION_JSON) or {}
    if not isinstance(c, dict):
        return True
    st = str(c.get("status") or "").upper().strip()
    # REVIEW/BLOCK이면 인간 확인(또는 시스템 안정화) 우선.
    if st in {"BLOCK", "REVIEW"}:
        return False
    return True


def _rest_gate_blocks() -> bool:
    rg = _load_json(REST_GATE) or {}
    try:
        if isinstance(rg, dict) and str(rg.get("status") or "").upper() == "REST":
            until = rg.get("rest_until_epoch")
            if until is None:
                return True
            if isinstance(until, (int, float)) and time.time() < float(until):
                return True
    except Exception:
        return False
    return False


def _time_phase_label(now: float) -> str:
    """
    자연 리듬의 가장 단순한 근사: 낮/밤.
    - 가능하면 human_summary의 time_phase를 사용
    - 없으면 로컬 시간으로 추정
    """
    hs = _load_json(HUMAN_SUMMARY) or {}
    tags = hs.get("tags") if isinstance(hs.get("tags"), dict) else {}
    v = str(tags.get("time_phase") or "").strip()
    if v in {"낮", "밤"}:
        return v
    h = int(time.localtime(now).tm_hour)
    return "낮" if 7 <= h < 21 else "밤"


def _rhythm_intensity(now: float) -> dict[str, Any]:
    """
    리듬 강도(0..1) + 주요 드라이브를 추정.
    """
    hs = _load_json(HUMAN_SUMMARY) or {}
    tags = hs.get("tags") if isinstance(hs.get("tags"), dict) else {}
    ist = hs.get("internal_state") if isinstance(hs.get("internal_state"), dict) else {}
    drives = ist.get("drives") if isinstance(ist.get("drives"), dict) else {}

    def fnum(v: Any) -> float:
        try:
            return float(v)
        except Exception:
            return 0.0

    explore = fnum(drives.get("explore"))
    avoid = fnum(drives.get("avoid"))
    rest = fnum(drives.get("rest"))
    boredom = fnum(ist.get("boredom"))
    curiosity = fnum(ist.get("curiosity"))

    dominant = str(tags.get("dominant_drive") or "")
    intensity = (0.55 * explore) + (0.25 * curiosity) + (0.20 * boredom) - (0.40 * rest) - (0.25 * avoid)
    intensity = max(0.0, min(1.0, intensity))

    return {
        "intensity": intensity,
        "dominant_drive": dominant,
        "explore": explore,
        "rest": rest,
        "avoid": avoid,
        "boredom": boredom,
        "curiosity": curiosity,
    }


def _pick_fractal_phase(now: float, prev_phase: str | None) -> tuple[str, str]:
    """
    정반합(프랙탈) 리듬으로 브라우저 탐색을 '확장/통합/수축'으로 순환시킨다.

    - EXPANSION: 외부 탐색(지도가/어스/검색)
    - INTEGRATION: 내부 통합(로컬 outputs 열기 등)
    - CONTRACTION: 안정화(짧은 앰비언스/휴식)
    """
    time_phase = _time_phase_label(now)
    c = _load_json(CONSTITUTION_JSON) or {}
    cst = str((c.get("status") if isinstance(c, dict) else "") or "").upper().strip()
    r = _rhythm_intensity(now)
    intensity = float(r["intensity"])

    # 안전이 흔들리면 수축이 먼저다.
    if cst == "CAUTION":
        return "CONTRACTION", "constitution=CAUTION"

    # 밤에는 기본적으로 통합/수축이 우세(자연스러운 회수/정리 리듬)
    if time_phase == "밤":
        # 정체(Stall) 중이면 밤이라도 가벼운 확장을 시도할 수 있다.
        if "STALL" in str(c.get("last_resonance") or "").upper():
            return "EXPANSION", "night_stall_recovery"
        if intensity >= 0.75:
            return "EXPANSION", "night_intense_explore"
        if prev_phase == "CONTRACTION":
            return "INTEGRATION", "night_cycle"
        return "CONTRACTION", "night_cycle"

    # 낮에는 기본적으로 확장/통합이 우세
    if intensity >= 0.55:
        if prev_phase == "EXPANSION":
            return "INTEGRATION", "day_cycle_after_expansion"
        return "EXPANSION", "day_cycle"
    return "INTEGRATION", "day_low_intensity_integrate"


def _rhythm_rate(now: float) -> tuple[float, int, str]:
    """
    리듬(상태)은 기록용이며 속도/상한에는 반영하지 않는다.
    반환: (cooldown_sec, max_per_hour, reason)
    """
    # 리듬 입력
    r = _rhythm_intensity(now)
    intensity = float(r["intensity"])
    time_phase = _time_phase_label(now)
    dominant = str(r["dominant_drive"])

    # 이전 phase를 읽어 순환에 사용(없으면 None)
    st = _load_json(STATE) or {}
    prev_phase = str(st.get("phase") or "") if isinstance(st, dict) else ""
    prev_phase = prev_phase if prev_phase else None

    phase, phase_reason = _pick_fractal_phase(now, prev_phase)

    # 리듬 정보는 기록용이며 결정 변수로 사용하지 않는다.
    cooldown = 20 * 60.0
    max_per_hour = 4

    # 안전 CAUTION이면 강제 수축으로 더 완만하게
    c = _load_json(CONSTITUTION_JSON) or {}
    cst = str((c.get("status") if isinstance(c, dict) else "") or "").upper().strip()
    if cst == "CAUTION":
        cooldown = max(cooldown, 60 * 60.0)
        max_per_hour = min(max_per_hour, 1)

    max_per_hour = max(1, int(max_per_hour))

    # Optional overrides from allow file
    allow = _load_json(ALLOW_FILE) or {}
    reason_bits: list[str] = [
        f"time_phase={time_phase}",
        f"phase={phase}({phase_reason})",
        f"dominant={dominant or 'unknown'}",
        f"intensity={intensity:.2f}",
    ]
    if isinstance(allow, dict):
        try:
            # Semantics:
            # - allow 파일이 `max_tasks_per_hour`를 명시하면, 그 값을 "의식적 override"로 존중한다.
            # - 0 이하: 무제한(=rate limit 해제)
            # - 양수: 해당 상한 적용
            if "max_tasks_per_hour" in allow:
                ov = int(allow.get("max_tasks_per_hour") or 0)
                if ov <= 0:
                    max_per_hour = 0
                    reason_bits.append("override=max_tasks_per_hour=unlimited")
                else:
                    max_per_hour = ov
                    reason_bits.append("override=max_tasks_per_hour")
        except Exception:
            pass
        try:
            # `min_cooldown_sec` is treated as a *cap* on the computed cooldown.
            # - 0: no cooldown (allow frequent exploration)
            # - >0: cap to this value
            if "min_cooldown_sec" in allow:
                ov = float(allow.get("min_cooldown_sec") or 0.0)
                if ov >= 0.0:
                    cooldown = min(cooldown, ov)
                    reason_bits.append("override=cooldown_cap")
        except Exception:
            pass

    # Persist chosen phase so next run can continue the fractal cycle
    try:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        snap = _load_json(STATE) or {}
        if not isinstance(snap, dict):
            snap = {}
        snap["phase"] = phase
        snap["phase_reason"] = phase_reason
        STATE.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    return cooldown, max_per_hour, ", ".join(reason_bits)


def main() -> int:
    now = time.time()
    # 명시적 STOP은 최우선 경계(boundary)다: 작업을 만들지도 않는다.
    if STOP_FILE.exists():
        return 0
    if not _is_armed(now):
        return 0
    if TASK_FILE.exists():
        return 0
    if not _within_allowed_hours(now):
        return 0
    if not _safety_allows_autonomy():
        return 0
    rest_gate_active = _rest_gate_blocks()

    # 사용자가 활동 중이면 제안하지 않는다.
    idle_s = _idle_seconds()
    min_idle = _min_idle_seconds()
    # 사용자가 실제로 PC를 "쓰지 않는 동안"만 탐색을 건다.
    # allow 파일에서 min_idle_seconds <= 0 이면 idle 조건을 비활성화한다.
    if min_idle > 0 and idle_s is not None and idle_s < min_idle:
        return 0

    cooldown_sec, max_per_hour, rate_reason = _rhythm_rate(now)
    today = time.strftime("%Y-%m-%d", time.localtime(now))
    hour_key = time.strftime("%Y-%m-%d %H", time.localtime(now))
    try:
        st = _load_json(STATE) or {}
        if isinstance(st, dict):
            if st.get("hour_key") == hour_key:
                cnt = int(st.get("count_in_hour") or 0)
                if max_per_hour > 0 and cnt >= max_per_hour:
                    return 0
            last = float(st.get("last_suggest_ts") or 0.0)
            if last and (now - last) < float(cooldown_sec):
                return 0
    except Exception:
        pass

    # 가벼운 휴리스틱: 기본 탐색 루트(google/youtube allowlist 내부)
    queries = [
        "구글어스",
        "구글 지도 로드뷰",
        "도시 야경 자전거",
        "자연 소리 ambience",
    ]

    # human_summary 태그를 참고(있으면)
    hs = _load_json(OUTPUTS / "self_compression_human_summary_latest.json") or {}
    tags = hs.get("tags") if isinstance(hs.get("tags"), dict) else {}
    if str(tags.get("dominant_drive") or "") == "explore":
        queries.insert(0, "새로운 장소 탐색")

    # 프랙탈 위상에 따라 액션을 고른다.
    # (정: EXPANSION, 반: CONTRACTION, 합: INTEGRATION)
    st = _load_json(STATE) or {}
    phase = str(st.get("phase") or "") if isinstance(st, dict) else ""
    if phase not in {"EXPANSION", "CONTRACTION", "INTEGRATION"}:
        phase = "EXPANSION"

    variant = int(now) % 3
    if phase == "EXPANSION":
        if variant == 0:
            actions = [
                {"type": "open_url", "url": "https://earth.google.com/web/"},
                {"type": "sleep", "seconds": 2},
                {"type": "google_search", "query": queries[0]},
                {"type": "sleep", "seconds": 2},
            ]
        else:
            actions = [
                {"type": "open_url", "url": "https://www.google.com/maps"},
                {"type": "sleep", "seconds": 2},
                {"type": "google_search", "query": queries[1]},
                {"type": "sleep", "seconds": 2},
            ]
    elif phase == "INTEGRATION":
        # 통합(정렬) 구간에서도 "경험을 1회라도 물질화"하기 위한 가벼운 탐색을 허용한다.
        # (allow 파일이 없으면 이 스크립트 자체가 실행되지 않으므로 안전함)
        if variant == 0:
            actions = [
                {"type": "open_url", "url": "https://www.google.com/maps"},
                {"type": "sleep", "seconds": 2},
                {"type": "google_search", "query": queries[1]},
                {"type": "sleep", "seconds": 2},
            ]
        elif variant == 1:
            actions = [
                {"type": "open_url", "url": "https://earth.google.com/web/"},
                {"type": "sleep", "seconds": 2},
                {"type": "google_search", "query": queries[0]},
                {"type": "sleep", "seconds": 2},
            ]
        else:
            actions = [
                {"type": "youtube_search", "query": "자연 소리 ambience"},
                {"type": "sleep", "seconds": 2},
            ]
    else:  # CONTRACTION
        # 수축(회수)에서는 외부 창/탭을 열지 않는다.
        actions = [{"type": "sleep", "seconds": 2}]

    task = {
        "goal": "browser_exploration",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        "actions": actions,
        "policy": {
            "cooldown_sec": cooldown_sec,
            "max_per_hour": max_per_hour,
            "min_idle_seconds": min_idle,
            "rest_gate_active": rest_gate_active,
            "reason": rate_reason,
        },
    }

    created = _atomic_create_json(TASK_FILE, task)
    try:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        prev = _load_json(STATE) or {}
        prev_hour = str(prev.get("hour_key") or "")
        prev_cnt = int(prev.get("count_in_hour") or 0) if isinstance(prev, dict) else 0
        if prev_hour != hour_key:
            prev_cnt = 0
        if created:
            prev_cnt += 1
        STATE.write_text(
            json.dumps(
                {
                    "day": today,
                    "hour_key": hour_key,
                    "count_in_hour": prev_cnt,
                    "last_suggest_ts": now,
                    "created": bool(created),
                    "rate": {
                        "cooldown_sec": cooldown_sec,
                        "max_per_hour": max_per_hour,
                        "reason": rate_reason,
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
