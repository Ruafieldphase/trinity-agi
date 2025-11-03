from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime

_PROJECT_ROOT = Path(__file__).parent.parent  # fdo_agi_repo
_PROFILE_PATH = _PROJECT_ROOT / "memory" / "user_profile.json"


def _ensure_dirs() -> None:
    _PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_user_profile() -> Dict[str, Any]:
    """Load user profile from JSON; return empty structure if missing."""
    _ensure_dirs()
    if not _PROFILE_PATH.exists():
        return {"preferences": {}, "updated_at": None}
    try:
        with open(_PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Corrupt file fallback
        return {"preferences": {}, "updated_at": None}


def save_user_profile(profile: Dict[str, Any]) -> None:
    """Persist user profile to JSON (UTF-8)."""
    _ensure_dirs()
    profile = dict(profile or {})
    profile.setdefault("updated_at", datetime.now().isoformat())
    with open(_PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)


def get_user_profile_context() -> str:
    """Return a compact, human-readable prompt snippet for all personas.

    Example output:
    [사용자 프로필]
    - 일일 자동 실행: 10:00
    - 새벽 전원 상태: OFF (야간엔 PC 꺼짐)
    """
    prof = load_user_profile()
    prefs = prof.get("preferences", {})

    auto_time = prefs.get("daily_auto_run_time")
    power = prefs.get("overnight_computer_power")  # "off" | "on" | None
    offline_window = prefs.get("offline_window")  # e.g., "02:00-07:00"

    lines = ["[사용자 프로필]"]
    if auto_time:
        lines.append(f"- 일일 자동 실행: {auto_time}")
    if power:
        state = "OFF" if str(power).lower() == "off" else "ON"
        lines.append(f"- 새벽 전원 상태: {state}")
    if offline_window:
        lines.append(f"- 야간 오프라인 구간: {offline_window}")

    # 최소 한 줄은 제공 (없으면 빈 컨텍스트 반환 방지)
    if len(lines) == 1:
        lines.append("- 선호 설정: (아직 등록되지 않음)")

    return "\n".join(lines)
