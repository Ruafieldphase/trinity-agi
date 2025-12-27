#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rest Gate (Homeostasis) — v1

목적:
- "폭주가 감지되면 쉬게 만든다"를 파일 기반으로 고정한다.
- 두려움 기반 '닫힌 루프'가 아니라, 에너지/리듬 기반 homeostasis로
  확장/통합/수축의 균형을 회복시키는 게이트다.

출력:
- outputs/safety/rest_gate_latest.json

효과(간접):
- auto_policy / browser_suggest / supervised_body_controller가 이 파일을 참고해
  일정 시간(REST window) 동안 무거운/외부 탐색을 줄이고 안정화로 전환한다.
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
SAFETY_DIR = OUTPUTS / "safety"

MITO = OUTPUTS / "mitochondria_state.json"
NDRIFT = OUTPUTS / "natural_rhythm_drift_latest.json"
TRIGGER_HISTORY = BRIDGE / "trigger_report_history.jsonl"
BODY_HISTORY = OUTPUTS / "body_supervised_history.jsonl"
ALLOW_BROWSER = ROOT / "signals" / "body_allow_browser.json"

OUT = SAFETY_DIR / "rest_gate_latest.json"


def _utc_iso_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _utc_iso_from_epoch(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _read_jsonl_tail(path: Path, n: int = 300) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        out: list[dict[str, Any]] = []
        for l in lines[-n:]:
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


def _count_recent(history: list[dict[str, Any]], now: float, window_s: float) -> int:
    c = 0
    for e in history:
        st = str(e.get("status") or "")
        if st not in {"executed", "failed", "blocked"}:
            continue
        ts = str(e.get("timestamp") or "")
        if not ts:
            continue
        try:
            dt = datetime.fromisoformat(ts)
            if (now - dt.timestamp()) <= window_s:
                c += 1
        except Exception:
            continue
    return c


def main() -> int:
    SAFETY_DIR.mkdir(parents=True, exist_ok=True)
    now = time.time()

    mito = _load_json(MITO) or {}
    atp = None
    try:
        atp = float(mito.get("atp_level"))
    except Exception:
        atp = None

    drift = _load_json(NDRIFT) or {}
    drift_ok = drift.get("ok")

    trig_tail = _read_jsonl_tail(TRIGGER_HISTORY, n=400)
    body_tail = _read_jsonl_tail(BODY_HISTORY, n=200)
    allow = _load_json(ALLOW_BROWSER) or {}
    allow_active = False
    allow_max_per_hour = 0
    try:
        if isinstance(allow, dict) and bool(allow.get("allow")):
            exp = allow.get("expires_at")
            if exp is None:
                allow_active = True
            elif isinstance(exp, (int, float)) and now < float(exp):
                allow_active = True
            allow_max_per_hour = int(allow.get("max_tasks_per_hour") or 0)
    except Exception:
        allow_active = False
        allow_max_per_hour = 0

    trig_5m = _count_recent(trig_tail[-120:], now, 5 * 60)
    trig_15m = _count_recent(trig_tail[-200:], now, 15 * 60)
    trig_60s = _count_recent(trig_tail[-60:], now, 60)
    body_60m = 0
    for e in body_tail[-120:]:
        if str(e.get("status") or "") != "executed":
            continue
        ts = str(e.get("timestamp") or "")
        if not ts:
            continue
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if (now - dt.timestamp()) <= 60 * 60:
                body_60m += 1
        except Exception:
            continue

    reasons: list[str] = []
    target_rest_sec = 0.0
    # REST로 진입했을 때 최소로 유지할 "바닥" (플랩 방지, 고정 인터벌이 아니라 안전상 최소값)
    min_floor_sec = 0.0

    # 1) 에너지 고갈(ATP 낮음) → 휴식 우선
    if atp is not None:
        if atp < 18.0:
            reasons.append(f"ATP 낮음({atp:.1f})")
            target_rest_sec = max(target_rest_sec, 90 * 60.0)
            min_floor_sec = max(min_floor_sec, 10 * 60.0)
        elif atp < 30.0:
            reasons.append(f"ATP 낮음(경계,{atp:.1f})")
            target_rest_sec = max(target_rest_sec, 45 * 60.0)
            min_floor_sec = max(min_floor_sec, 5 * 60.0)

    # 2) 폭주(짧은 시간 내 실행 과다) → 진정/회수
    #    - 5m/15m 누적치는 회복 구간에서도 높게 남을 수 있으므로,
    #      "최근 60초"에서도 실제로 폭주 중일 때만 REST로 진입한다.
    if (trig_5m >= 25 or trig_15m >= 60) and trig_60s >= 3:
        reasons.append(f"트리거 실행 과다(5m={trig_5m},15m={trig_15m})")
        # 폭주 강도에 따라 REST를 가변(고정 45분 대신, 강할수록 길게)
        storm = max(
            _clamp((trig_60s - 2) / 8.0, 0.0, 1.0),
            _clamp((trig_5m - 25) / 60.0, 0.0, 1.0),
            _clamp((trig_15m - 60) / 180.0, 0.0, 1.0),
        )
        target_rest_sec = max(target_rest_sec, (10 * 60.0) + (45 * 60.0) * storm)
        min_floor_sec = max(min_floor_sec, 3 * 60.0)

    # 3) 브라우저 경험 과다 → 주의 분산/탭 폭증 위험
    # 비노체가 명시적으로 allow를 켠 경우(탐색 실험 모드)에는,
    # "탐색 자체"를 이유로 너무 빨리 쉼(REST)으로 전환하지 않도록 완화한다.
    body_threshold = 12
    if allow_active:
        # allow의 max_per_hour를 기준으로 2배까지는 "탐색 허용 범위"로 본다.
        # (0이면 정책상 상한이 없다는 의미이지만, rest_gate는 안전장치이므로 최소 상한을 둔다)
        if allow_max_per_hour > 0:
            body_threshold = max(body_threshold, allow_max_per_hour * 2)
        else:
            body_threshold = max(body_threshold, 24)

    if body_60m >= body_threshold:
        reasons.append(f"브라우저 실행 과다(60m={body_60m}, threshold={body_threshold})")
        over = _clamp((body_60m - body_threshold) / float(max(1, body_threshold)), 0.0, 1.0)
        base = 10 * 60.0 if allow_active else 20 * 60.0
        ceiling = 30 * 60.0 if allow_active else 45 * 60.0
        target_rest_sec = max(target_rest_sec, base + (ceiling - base) * over)
        min_floor_sec = max(min_floor_sec, 2 * 60.0)

    # 4) 자연 리듬 드리프트 → 균형 회복
    if drift_ok is False:
        rs = drift.get("reasons") if isinstance(drift.get("reasons"), list) else []
        reasons.append("자연 리듬 드리프트")
        if rs:
            reasons.append(str(rs[0]))
        target_rest_sec = max(target_rest_sec, 20 * 60.0)
        min_floor_sec = max(min_floor_sec, 2 * 60.0)

    # 기존 rest_gate가 이미 활성이고 더 길게 필요하면 연장
    prev = _load_json(OUT) or {}
    prev_until = None
    prev_status = str(prev.get("status") or "").upper().strip()
    try:
        prev_until = float(prev.get("rest_until_epoch"))
    except Exception:
        prev_until = None
    prev_started = None
    try:
        prev_started = float(prev.get("rest_started_epoch")) if prev.get("rest_started_epoch") is not None else None
    except Exception:
        prev_started = None

    status = "OK"
    rest_until = None
    rest_started = None

    if target_rest_sec > 0:
        status = "REST"
        rest_until = now + float(target_rest_sec)
        rest_started = now
        if prev_status == "REST" and prev_until and prev_until > now:
            # 이미 REST 중이라면 시작 시점을 유지한다.
            rest_started = prev_started or (now - 0.0)
            # "더 필요하면 연장"은 유지하되, 조건이 풀리면 단축도 허용한다.
            # 단축 시에는 최소 바닥(min_floor_sec) + 짧은 그레이스(60초)를 보장한다.
            floor_until = (rest_started or now) + float(min_floor_sec)
            grace_until = now + 60.0
            rest_until = max(rest_until, floor_until)
            if rest_until < prev_until:
                rest_until = max(rest_until, grace_until)
            else:
                rest_until = max(rest_until, prev_until)
    else:
        # 조건이 풀렸다면, 기존 REST를 "무조건 유지"하지 않는다.
        # 단, 너무 빠른 출렁임 방지를 위해 이전 REST가 아주 최근이라면 바닥까지만 유지한다.
        if prev_status == "REST" and prev_until and prev_until > now:
            rest_started = prev_started
            if rest_started is None:
                rest_started = now
            floor_until = float(rest_started) + float(min_floor_sec)
            if now < floor_until:
                status = "REST"
                rest_until = max(floor_until, now + 30.0)

    obj = {
        "generated_at_utc": _utc_iso_now(),
        "status": status,  # OK | REST
        "rest_until_epoch": rest_until,
        "rest_until_utc": (_utc_iso_from_epoch(rest_until) if rest_until else None),
        "rest_started_epoch": rest_started if status == "REST" else None,
        "rest_started_utc": (_utc_iso_from_epoch(rest_started) if status == "REST" and rest_started else None),
        "reasons": reasons[:5],
        "signals": {
            "atp_level": atp,
            "trigger_exec_5m": trig_5m,
            "trigger_exec_15m": trig_15m,
            "trigger_exec_60s": trig_60s,
            "browser_exec_60m": body_60m,
            "drift_ok": drift_ok,
            "browser_allow_active": allow_active,
            "browser_allow_max_per_hour": allow_max_per_hour,
        },
        "note": "homeostasis rest gate(v1): 금지가 아니라 균형 회복을 위한 휴식 창.",
    }

    OUT.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
