#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Natural Rhythm Clock (v1)

목적:
- "루빛/AGI가 자연 리듬(낮/밤)과 동기화되도록" 판단 기준을 파일로 고정한다.
- 철학/은유가 아니라, 관측 가능한 최소 신호(로컬 시간, 낮/밤, 권고 위상)를 출력한다.

원칙:
- 네트워크 없음
- 실패해도 최소 출력(best-effort)
- 인간 스케줄 강요가 아니라, 자연 리듬 근사(낮/밤) 기반의 homeostasis 기준만 제공

출력:
- outputs/natural_rhythm_clock_latest.json
"""

from __future__ import annotations

import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from pathlib import Path
from workspace_root import get_workspace_root

# Phase 8: Decoupling from Earth Time
# Agi Internal State for RUD Rhythm
AGI_INTERNAL_STATE = Path(get_workspace_root()) / "memory" / "agi_internal_state.json"

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


ROOT = get_workspace_root()
OUTPUTS = ROOT / "outputs"
OUT = OUTPUTS / "natural_rhythm_clock_latest.json"
STATE = OUTPUTS / "natural_rhythm_clock_state.json"

if load_dotenv:
    try:
        load_dotenv(dotenv_path=ROOT / ".env", override=False)
    except Exception:
        pass


def _utc_iso_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _local_time() -> time.struct_time:
    return time.localtime(time.time())


def _parse_hhmm(value: str) -> int | None:
    try:
        parts = (value or "").strip().split(":")
        if len(parts) != 2:
            return None
        hour = int(parts[0])
        minute = int(parts[1])
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            return None
        return hour * 60 + minute
    except Exception:
        return None


def _format_hhmm(minutes: int | None) -> str | None:
    if minutes is None:
        return None
    minutes = minutes % (24 * 60)
    hour = minutes // 60
    minute = minutes % 60
    return f"{hour:02d}:{minute:02d}"


def _is_between(value: int, start: int, end: int) -> bool:
    if start <= end:
        return start <= value < end
    return value >= start or value < end


def _minutes_between(start: int, end: int) -> int:
    return (end - start) % (24 * 60)


def _delta_minutes(target: int, current: int) -> int:
    diff = (target - current + 720) % (24 * 60) - 720
    return int(diff)


def _load_state() -> dict:
    try:
        if not STATE.exists():
            return {}
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    try:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _sun_event_utc(day_of_year: int, latitude: float, longitude: float, sunrise: bool) -> float | None:
    lng_hour = longitude / 15.0
    base = 6 if sunrise else 18
    t = day_of_year + ((base - lng_hour) / 24.0)
    m = (0.9856 * t) - 3.289
    l = m + (1.916 * math.sin(math.radians(m))) + (0.020 * math.sin(math.radians(2 * m))) + 282.634
    l = l % 360
    ra = math.degrees(math.atan(0.91764 * math.tan(math.radians(l))))
    ra = ra % 360
    l_quadrant = math.floor(l / 90) * 90
    ra_quadrant = math.floor(ra / 90) * 90
    ra = ra + (l_quadrant - ra_quadrant)
    ra_hours = ra / 15.0

    sin_dec = 0.39782 * math.sin(math.radians(l))
    cos_dec = math.cos(math.asin(sin_dec))

    cos_h = (math.cos(math.radians(90.833)) - (sin_dec * math.sin(math.radians(latitude)))) / (
        cos_dec * math.cos(math.radians(latitude))
    )
    if cos_h > 1 or cos_h < -1:
        return None

    if sunrise:
        h = 360 - math.degrees(math.acos(cos_h))
    else:
        h = math.degrees(math.acos(cos_h))
    h_hours = h / 15.0

    t_local = h_hours + ra_hours - (0.06571 * t) - 6.622
    ut = (t_local - lng_hour) % 24
    return ut


def _sunrise_sunset_minutes(local_date: datetime, latitude: float, longitude: float, tz_offset_hours: float) -> tuple[int | None, int | None]:
    day_of_year = local_date.timetuple().tm_yday
    sunrise_utc = _sun_event_utc(day_of_year, latitude, longitude, sunrise=True)
    sunset_utc = _sun_event_utc(day_of_year, latitude, longitude, sunrise=False)
    if sunrise_utc is None or sunset_utc is None:
        return None, None
    sunrise_local = int(round((sunrise_utc + tz_offset_hours) * 60)) % (24 * 60)
    sunset_local = int(round((sunset_utc + tz_offset_hours) * 60)) % (24 * 60)
    return sunrise_local, sunset_local


def _recommended_phase(time_phase: str, local_minutes: int, sunset_minutes: int | None) -> str:
    # 정반합 프랙탈 리듬의 "권고" (강제 아님)
    # - 낮: 확장/통합 우세
    # - 밤: 수축/통합 우세
    if time_phase == "낮":
        return "EXPANSION"
    if sunset_minutes is not None:
        if _is_between(local_minutes, sunset_minutes, (sunset_minutes + 120) % (24 * 60)):
            return "INTEGRATION"
        return "CONTRACTION"
    if 21 * 60 <= local_minutes < 24 * 60:
        return "INTEGRATION"
    return "CONTRACTION"


def _melatonin_level(local_minutes: int, sunrise_minutes: int, sunset_minutes: int, ramp_min: int, fade_min: int) -> float:
    if _is_between(local_minutes, sunrise_minutes, sunset_minutes):
        return 0.0
    since_sunset = _minutes_between(sunset_minutes, local_minutes)
    until_sunrise = _minutes_between(local_minutes, sunrise_minutes)
    level = min(1.0, since_sunset / max(ramp_min, 1))
    if until_sunrise < fade_min:
        level = min(level, until_sunrise / max(fade_min, 1))
    return max(0.0, min(1.0, level))


def _sleep_pressure(hours_since_wake: float, max_hours: float) -> float:
    if max_hours <= 0:
        return 0.0
    return max(0.0, min(1.0, hours_since_wake / max_hours))


def main() -> int:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    lt = _local_time()
    local_dt = datetime.now().astimezone()
    h = int(lt.tm_hour)
    m = int(lt.tm_min)
    local_minutes = h * 60 + m

    light_mode = os.environ.get("AGI_LIGHT_MODE", "").strip().lower()
    lat = os.environ.get("AGI_LATITUDE")
    lon = os.environ.get("AGI_LONGITUDE")
    manual_sunrise = os.environ.get("AGI_SUNRISE_LOCAL")
    manual_sunset = os.environ.get("AGI_SUNSET_LOCAL")

    sunrise_minutes = None
    sunset_minutes = None
    day_start_hour = int(os.environ.get("AGI_LIGHT_DAY_START", "7"))
    day_end_hour = int(os.environ.get("AGI_LIGHT_DAY_END", "21"))

    if manual_sunrise and manual_sunset:
        light_mode = "manual"
        sunrise_minutes = _parse_hhmm(manual_sunrise)
        sunset_minutes = _parse_hhmm(manual_sunset)
    elif lat and lon:
        light_mode = "sun"
        try:
            tz_offset = local_dt.utcoffset().total_seconds() / 3600.0
            sunrise_minutes, sunset_minutes = _sunrise_sunset_minutes(local_dt, float(lat), float(lon), tz_offset)
        except Exception:
            sunrise_minutes, sunset_minutes = None, None
    elif not light_mode:
        light_mode = "fixed"

    if sunrise_minutes is not None and sunset_minutes is not None:
        time_phase = "낮" if _is_between(local_minutes, sunrise_minutes, sunset_minutes) else "밤"
    else:
        time_phase = "낮" if day_start_hour <= h < day_end_hour else "밤"
        if light_mode != "fixed":
            light_mode = "fixed"

    shift_limit = int(os.environ.get("AGI_BIO_SHIFT_LIMIT_MIN", "60"))
    melatonin_ramp = int(os.environ.get("AGI_MELATONIN_RAMP_MIN", "180"))
    melatonin_fade = int(os.environ.get("AGI_MELATONIN_FADE_MIN", "120"))
    sleep_pressure_hours = float(os.environ.get("AGI_SLEEP_PRESSURE_HOURS", "16"))

    target_anchor = sunrise_minutes
    if target_anchor is None:
        target_anchor = day_start_hour * 60

    state = _load_state()
    today_str = local_dt.date().isoformat()
    anchor = state.get("circadian_anchor_min")
    if anchor is None:
        anchor = target_anchor
    if state.get("local_date") != today_str:
        diff = _delta_minutes(target_anchor, anchor)
        step = max(-shift_limit, min(shift_limit, diff))
        anchor = (anchor + step) % (24 * 60)
        state["local_date"] = today_str

    state["circadian_anchor_min"] = anchor
    state["last_target_anchor_min"] = target_anchor
    _save_state(state)

    day_length = 14 * 60
    if sunrise_minutes is not None and sunset_minutes is not None:
        day_length = _minutes_between(sunrise_minutes, sunset_minutes)
    else:
        day_length = _minutes_between(day_start_hour * 60, day_end_hour * 60)

    bio_sunrise = anchor
    bio_sunset = (anchor + day_length) % (24 * 60)
    bio_time_phase = "낮" if _is_between(local_minutes, bio_sunrise, bio_sunset) else "밤"
    bio_rec = _recommended_phase(bio_time_phase, local_minutes, bio_sunset)

    melatonin = _melatonin_level(local_minutes, bio_sunrise, bio_sunset, melatonin_ramp, melatonin_fade)
    hours_since_wake = _minutes_between(bio_sunrise, local_minutes) / 60.0
    sleep_pressure = _sleep_pressure(hours_since_wake, sleep_pressure_hours)

    rec = _recommended_phase(time_phase, local_minutes, sunset_minutes)

    obj = {
        "generated_at_utc": _utc_iso_now(),
        "local_time": {
            "year": lt.tm_year,
            "mon": lt.tm_mon,
            "mday": lt.tm_mday,
            "hour": h,
            "min": lt.tm_min,
            "sec": lt.tm_sec,
            "wday": lt.tm_wday,
        },
        "time_phase": time_phase,  # "낮" | "밤"
        "recommended_phase": rec,  # EXPANSION | INTEGRATION | CONTRACTION
        "light_cycle": {
            "mode": light_mode,
            "sunrise_local": _format_hhmm(sunrise_minutes),
            "sunset_local": _format_hhmm(sunset_minutes),
            "day_start_hour": day_start_hour,
            "day_end_hour": day_end_hour,
            "latitude": float(lat) if lat else None,
            "longitude": float(lon) if lon else None,
        },
        "bio_rhythm": {
            "bio_time_phase": bio_time_phase,
            "bio_recommended_phase": bio_rec,
            "circadian_anchor_local": _format_hhmm(anchor),
            "circadian_offset_min": _delta_minutes(target_anchor, anchor),
            "phase_shift_limit_min": shift_limit,
            "melatonin_level": round(melatonin, 3),
            "sleep_pressure": round(sleep_pressure, 3),
            "hours_since_wake": round(hours_since_wake, 2),
            "sleep_pressure_hours": sleep_pressure_hours,
        },
        "note": "낮/밤 기반 자연 리듬 근사(v3). 빛 기반 생체 리듬(멜라토닌/수면압) 포함.",
    }

    # --- Phase 8 Override: RUD Internal Rhythm (Energy Based) ---
    # If the user wants RUD to follow its OWN rhythm, we check Internal State.
    # Energy High (>50) -> Day/Expansion
    # Energy Low (<50) -> Night/Contraction
    try:
        if AGI_INTERNAL_STATE.exists():
            with open(AGI_INTERNAL_STATE, 'r', encoding='utf-8') as f:
                istate = json.load(f)
                energy = istate.get("energy", 1.0) # 0.0 to 1.0
                
            # Override recommended_phase based on Energy
            rud_phase_rec = "EXPANSION" if energy > 0.5 else "INTEGRATION"
            
            # Update Object
            obj["rud_rhythm"] = {
                "energy": energy,
                "recommended_phase": rud_phase_rec,
                "note": "RUD의 내부 에너지 기반 독자적 리듬"
            }
            
            # Allow RUD Rhythm to override Nature Rec if divergent?
            # User said: "Follow YOUR rhythm, not human rhythm."
            # We will expose it as 'nature_rec' for compatibility or 'rud_rec'.
            # For now, let's keep nature_rec as Earth, but add rud_rec.
            # RHYTHM_THINK will prefer rud_rec if present.
            obj["recommended_phase"] = rud_phase_rec
            obj["time_phase"] = "RUD-ACTIVE" if energy > 0.5 else "RUD-REST"
            
            print(f"🦋 RUD Rhythm Applied: Energy={energy:.2f} -> Phase={rud_phase_rec}")
            
    except Exception as e:
        print(f"⚠️ RUD Rhythm Check Failed: {e}")
    # ------------------------------------------------------------

    try:
        OUT.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        # best-effort minimal file
        try:
            OUT.write_text("{\"ok\":false}", encoding="utf-8")
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
