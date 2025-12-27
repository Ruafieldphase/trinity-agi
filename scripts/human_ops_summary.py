#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Human Ops Summary (Korean, non-programmer friendly)

목적:
- "지금 AGI가 무엇을 했는지 / 안전 상태가 어떤지 / 학습 신호가 살아있는지"를
  한 눈에 볼 수 있는 아주 짧은 요약 파일을 생성한다.

원칙:
- 네트워크 사용 없음
- PII 원문 저장 없음(경로/시간/상태 같은 관측 메타만)
- 실패해도 최소 파일은 생성(best-effort)

출력:
- outputs/bridge/human_ops_summary_latest.txt
- outputs/bridge/human_ops_summary_latest.json
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
OUTPUTS = ROOT / "outputs"
BRIDGE = OUTPUTS / "bridge"
SIGNALS = ROOT / "signals"
MEMORY = ROOT / "memory"

TRIGGER_REPORT = BRIDGE / "trigger_report_latest.json"
CONSTITUTION_JSON = BRIDGE / "constitution_review_latest.json"
AURA_STATE = OUTPUTS / "aura_pixel_state.json"
AUTO_POLICY_STATE = OUTPUTS / "sync_cache" / "auto_policy_state.json"
LIFE_STATE = OUTPUTS / "sync_cache" / "life_state.json"
INTERNAL_STATE = MEMORY / "agi_internal_state.json"
NATURAL_CLOCK = OUTPUTS / "natural_rhythm_clock_latest.json"
NATURAL_DRIFT = OUTPUTS / "natural_rhythm_drift_latest.json"
MITO = OUTPUTS / "mitochondria_state.json"
REST_GATE = OUTPUTS / "safety" / "rest_gate_latest.json"
RHYTHM_PAIN = OUTPUTS / "sync_cache" / "rhythm_pain_latest.json"
DIGITAL_TWIN = OUTPUTS / "sync_cache" / "digital_twin_state.json"
QDIGITAL_TWIN = OUTPUTS / "sync_cache" / "quantum_digital_twin_state.json"

OBS_RECODE = OUTPUTS / "obs_recode_intake_latest.json"
RUA_CONV = OUTPUTS / "rua_conversation_intake_latest.json"
EXPLORATION_INTAKE = OUTPUTS / "exploration_intake_latest.json"
EXPLORATION_EVENT = OUTPUTS / "exploration_session_event_latest.json"
BODY_LATEST = OUTPUTS / "body_supervised_latest.json"
BODY_LIFE_STATE = OUTPUTS / "sync_cache" / "body_life_state.json"
BODY_PID = OUTPUTS / "supervised_body_controller.pid"
VIDEO_BOUNDARY_GATE = OUTPUTS / "video_boundary_gate_latest.json"
YOUTUBE_CHANNEL_BOUNDARY = OUTPUTS / "youtube_channel_boundary_intake_latest.json"
BOUNDARY_INDUCTION = OUTPUTS / "boundary_induction_latest.json"
BINOCHE_NOTE_INTAKE = OUTPUTS / "bridge" / "binoche_note_intake_latest.json"
GLYMPH_METRICS = OUTPUTS / "glymphatic_metrics_latest.json"
SYSTEM_GAPS_REPORT = BRIDGE / "system_gaps_report_latest.txt"
STUB_RADAR_REPORT = BRIDGE / "stub_radar_latest.txt"
META_SUPERVISOR_REPORT = BRIDGE / "meta_supervisor_report_latest.txt"

BODY_ARM = SIGNALS / "body_arm.json"
BODY_ALLOW = SIGNALS / "body_allow_browser.json"
BODY_STOP = SIGNALS / "body_stop.json"

OUT_TXT = BRIDGE / "human_ops_summary_latest.txt"
OUT_JSON = BRIDGE / "human_ops_summary_latest.json"


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _file_age_seconds(path: Path) -> float | None:
    try:
        if not path.exists():
            return None
        return max(0.0, time.time() - path.stat().st_mtime)
    except Exception:
        return None


def _fmt_age(age_s: float | None) -> str:
    if age_s is None:
        return "없음"
    if age_s < 60:
        return f"{int(age_s)}초"
    if age_s < 3600:
        return f"{int(age_s // 60)}분"
    return f"{int(age_s // 3600)}시간"


def _pid_running(pid: int) -> bool:
    try:
        import os

        if pid <= 0:
            return False
        if os.name != "nt":
            os.kill(pid, 0)
            return True
        # Windows best-effort: use tasklist via powershell to avoid psutil dependency
        import subprocess

        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"Get-Process -Id {pid} -ErrorAction SilentlyContinue | Select-Object -First 1 | Out-String"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if __import__('sys').platform == 'win32' else 0,
        )
        return bool((proc.stdout or "").strip())
    except Exception:
        return False


def main() -> int:
    BRIDGE.mkdir(parents=True, exist_ok=True)

    report = _load_json(TRIGGER_REPORT) or {}
    const = _load_json(CONSTITUTION_JSON) or {}
    aura = _load_json(AURA_STATE) or {}
    policy = _load_json(AUTO_POLICY_STATE) or {}
    life = _load_json(LIFE_STATE) or {}
    internal_state = _load_json(INTERNAL_STATE) or {}
    rua_conv = _load_json(RUA_CONV) or {}
    arm = _load_json(BODY_ARM) or {}
    allow = _load_json(BODY_ALLOW) or {}
    nclock = _load_json(NATURAL_CLOCK) or {}
    ndrift = _load_json(NATURAL_DRIFT) or {}
    mito = _load_json(MITO) or {}
    rest_gate = _load_json(REST_GATE) or {}
    pain = _load_json(RHYTHM_PAIN) or {}
    twin = _load_json(DIGITAL_TWIN) or {}
    qtwin = _load_json(QDIGITAL_TWIN) or {}
    boundary_ind = _load_json(BOUNDARY_INDUCTION) or {}
    body_life = _load_json(BODY_LIFE_STATE) or {}
    glymph = _load_json(GLYMPH_METRICS) or {}

    # Cloud LLM backend (관측용: 네트워크 호출 없음)
    # NOTE: ModelSelector는 init에서 네트워크 호출을 하지 않아야 한다(=사람용 요약 안정화).
    cloud_backend: dict[str, Any] = {"available": False, "backend": "none", "note": ""}
    try:
        from services.model_selector import ModelSelector  # type: ignore

        ms = ModelSelector()
        if hasattr(ms, "get_status_snapshot"):
            cloud_backend = dict(ms.get_status_snapshot() or {})
        else:
            cloud_backend = {
                "available": bool(getattr(ms, "available", False)),
                "backend": str(getattr(ms, "backend", "none")),
                "note": "",
            }
    except Exception as e:
        cloud_backend = {"available": False, "backend": "none", "note": f"import/init failed: {e.__class__.__name__}"}

    latest_action = str(report.get("action") or "unknown")
    latest_status = str(report.get("status") or "unknown")
    latest_time = str(report.get("timestamp") or "")
    latest_reason = ""
    try:
        params = report.get("params") or {}
        if isinstance(params, dict):
            latest_reason = str(params.get("reason") or "")
    except Exception:
        pass

    safety_status = str(const.get("status") or "UNKNOWN")
    safety_next = str(const.get("next_recommendation") or "")
    safety_flags = const.get("flags") or []
    if not isinstance(safety_flags, list):
        safety_flags = []

    aura_dec = (aura.get("decision") or {}) if isinstance(aura, dict) else {}
    aura_state = str(aura_dec.get("state") or "")
    aura_color = str(aura_dec.get("color") or "")
    aura_reason = str(aura_dec.get("reason") or "")

    # Drive/curiosity/boredom (관측 가능하게)
    ist_energy = internal_state.get("energy")
    ist_boredom = internal_state.get("boredom")
    ist_curiosity = internal_state.get("curiosity")
    ist_drives = internal_state.get("drives") if isinstance(internal_state.get("drives"), dict) else {}
    dominant_drive = ""
    try:
        if isinstance(ist_drives, dict) and ist_drives:
            dominant_drive = max(ist_drives.items(), key=lambda kv: float(kv[1] or 0.0))[0]
    except Exception:
        dominant_drive = ""

    ages = {
        "obs_recode": _file_age_seconds(OBS_RECODE),
        "rua_conversation": _file_age_seconds(RUA_CONV),
        "exploration_intake": _file_age_seconds(EXPLORATION_INTAKE),
        "exploration_event": _file_age_seconds(EXPLORATION_EVENT),
        "body_latest": _file_age_seconds(BODY_LATEST),
        "video_boundary_gate": _file_age_seconds(VIDEO_BOUNDARY_GATE),
        "youtube_channel_boundary": _file_age_seconds(YOUTUBE_CHANNEL_BOUNDARY),
        "boundary_induction": _file_age_seconds(BOUNDARY_INDUCTION),
        "binoche_note_intake": _file_age_seconds(BINOCHE_NOTE_INTAKE),
        "body_life_state": _file_age_seconds(BODY_LIFE_STATE),
        "glymph_metrics": _file_age_seconds(GLYMPH_METRICS),
        "rhythm_pain": _file_age_seconds(RHYTHM_PAIN),
        "digital_twin": _file_age_seconds(DIGITAL_TWIN),
        "quantum_digital_twin": _file_age_seconds(QDIGITAL_TWIN),
        "system_gaps_report": _file_age_seconds(SYSTEM_GAPS_REPORT),
        "stub_radar_report": _file_age_seconds(STUB_RADAR_REPORT),
        "meta_supervisor_report": _file_age_seconds(META_SUPERVISOR_REPORT),
    }

    body_pid = None
    body_running = False
    try:
        if BODY_PID.exists():
            body_pid = int((BODY_PID.read_text(encoding="utf-8", errors="replace") or "").strip())
            body_running = _pid_running(int(body_pid))
    except Exception:
        body_pid = None
        body_running = False

    rua_boundary_mode = ""
    try:
        newest = rua_conv.get("newest") if isinstance(rua_conv.get("newest"), dict) else {}
        dyn = newest.get("boundary_dynamics") if isinstance(newest.get("boundary_dynamics"), dict) else {}
        rua_boundary_mode = str(dyn.get("dominant_mode") or "")
        if not rua_boundary_mode:
            # Fallback for older schema: infer from keyword_counts only (no 원문, 메타만).
            kw = newest.get("keyword_counts") if isinstance(newest.get("keyword_counts"), dict) else {}

            def c(k: str) -> int:
                v = kw.get(k, 0)
                return int(v) if isinstance(v, int) else 0

            expansion = c("확장") + c("펼침") + c("열림")
            contraction = c("수축") + c("압축") + c("접힘") + c("닫힘")
            mix = c("혼합") + c("믹스") + c("비빔밥") + c("정반합") + c("통합")
            if mix >= max(expansion, contraction) and mix >= 3:
                rua_boundary_mode = "mix"
            elif (expansion - contraction) >= 3:
                rua_boundary_mode = "expand"
            elif (contraction - expansion) >= 3:
                rua_boundary_mode = "contract"
            elif expansion or contraction or mix:
                rua_boundary_mode = "balanced"
    except Exception:
        rua_boundary_mode = ""

    stop_file_present = bool(BODY_STOP.exists())

    # a-b-c 시간 동역학 링크(관측용)
    # a: memory/경험(rua_conversation, obs_recode)
    # b: 현재 실행 상태(heartbeat/life_state)
    # c: 미래 스캔(탐색 이벤트/탐색 인테이크)
    abc = {
        "a": {
            "obs_recode_age_s": ages["obs_recode"],
            "rua_conversation_age_s": ages["rua_conversation"],
        },
        "b": {
            "life_state_age_s": _file_age_seconds(LIFE_STATE),
        },
        "c": {
            "exploration_event_age_s": ages["exploration_event"],
            "exploration_intake_age_s": ages["exploration_intake"],
        },
    }

    armed = False
    arm_expires_in_s: float | None = None
    try:
        exp = arm.get("expires_at")
        if isinstance(exp, (int, float)):
            now = time.time()
            arm_expires_in_s = max(0.0, float(exp) - now)
            armed = arm_expires_in_s > 0.0
    except Exception:
        pass

    allow_on = False
    allow_expires_in_s: float | None = None
    try:
        if isinstance(allow, dict) and bool(allow.get("allow")):
            exp = allow.get("expires_at")
            if exp is None:
                allow_on = True
            elif isinstance(exp, (int, float)):
                now = time.time()
                allow_expires_in_s = max(0.0, float(exp) - now)
                allow_on = allow_expires_in_s > 0.0
    except Exception:
        pass

    obj = {
        "generated_at_utc": _utc_now_iso(),
        "last_trigger": {
            "action": latest_action,
            "status": latest_status,
            "timestamp": latest_time,
            "reason": latest_reason,
        },
        "safety": {
            "status": safety_status,
            "flags": safety_flags,
            "next_recommendation": safety_next,
        },
        "aura": {
            "state": aura_state,
            "color": aura_color,
            "reason": aura_reason,
        },
        "internal_state": {
            "energy": ist_energy,
            "boredom": ist_boredom,
            "curiosity": ist_curiosity,
            "drives": ist_drives if isinstance(ist_drives, dict) else {},
            "dominant_drive": dominant_drive,
            "last_drive_update_utc": internal_state.get("last_drive_update_utc"),
        },
        "life_state": {
            "state": life.get("state") if isinstance(life, dict) else None,
            "reason": life.get("reason") if isinstance(life, dict) else None,
            "generated_at_utc": life.get("generated_at_utc") if isinstance(life, dict) else None,
        },
        "learning_signals": {
            "obs_recode_age_s": ages["obs_recode"],
            "rua_conversation_age_s": ages["rua_conversation"],
            "rua_boundary_mode": rua_boundary_mode,
            "exploration_intake_age_s": ages["exploration_intake"],
            "exploration_event_age_s": ages["exploration_event"],
            "supervised_body_latest_age_s": ages["body_latest"],
            "body_life_state_age_s": ages["body_life_state"],
            "body_controller_pid": body_pid,
            "body_controller_running": body_running,
            "video_boundary_gate_age_s": ages["video_boundary_gate"],
            "youtube_channel_boundary_age_s": ages["youtube_channel_boundary"],
            "boundary_induction_age_s": ages["boundary_induction"],
            "boundary_induction_active_rules_count": boundary_ind.get("active_rules_count") if isinstance(boundary_ind, dict) else None,
            "boundary_induction_delta": boundary_ind.get("delta") if isinstance(boundary_ind, dict) else None,
            "binoche_note_intake_age_s": ages["binoche_note_intake"],
            "glymphatic_metrics_age_s": ages["glymph_metrics"],
            "rhythm_pain_age_s": ages["rhythm_pain"],
            "digital_twin_age_s": ages["digital_twin"],
            "quantum_digital_twin_age_s": ages["quantum_digital_twin"],
        },
        "supervised_browser": {
            "armed": armed,
            "arm_expires_in_s": arm_expires_in_s,
            "allow_browser": allow_on,
            "allow_expires_in_s": allow_expires_in_s,
        },
        "auto_policy": {
            "last_decision_action": policy.get("last_decision_action"),
            "last_decision_reason": policy.get("last_decision_reason"),
        },
        "natural_rhythm": {
            "time_phase": nclock.get("time_phase"),
            "recommended_phase": nclock.get("recommended_phase"),
            "drift_ok": ndrift.get("ok"),
            "drift_reasons": ndrift.get("reasons") if isinstance(ndrift.get("reasons"), list) else [],
        },
        "atp": {
            "atp_level": mito.get("atp_level"),
            "status": mito.get("status"),
            "pulse_rate": mito.get("pulse_rate"),
        },
        "rest_gate": {
            "status": rest_gate.get("status"),
            "rest_until_utc": rest_gate.get("rest_until_utc"),
            "reasons": rest_gate.get("reasons") if isinstance(rest_gate.get("reasons"), list) else [],
        },
        "digital_twin": {
            "mismatch_0_1": twin.get("mismatch_0_1") if isinstance(twin, dict) else None,
            "route_hint": twin.get("route_hint") if isinstance(twin, dict) else None,
            "observed_last_action": ((twin.get("observed") or {}).get("last_action") if isinstance(twin.get("observed"), dict) else None) if isinstance(twin, dict) else None,
            "recommended_phase": ((twin.get("observed") or {}).get("recommended_phase") if isinstance(twin.get("observed"), dict) else None) if isinstance(twin, dict) else None,
        },
        "quantum_digital_twin": {
            "dominant_drive": qtwin.get("dominant_drive") if isinstance(qtwin, dict) else None,
            "candidates": qtwin.get("candidates") if isinstance(qtwin, dict) else [],
        },
        "abc_link": abc,
        "cloud_backend": cloud_backend,
    }

    OUT_JSON.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

    # 경계 유도(자기 생성)는 "스킵"이어도 현재 활성 규칙 수를 관측 가능하게 유지한다.
    try:
        bic = boundary_ind.get("active_rules_count") if isinstance(boundary_ind, dict) else None
        boundary_induction_count = str(int(bic)) if isinstance(bic, int) else "0"
        if isinstance(boundary_ind, dict) and boundary_ind.get("skipped"):
            boundary_induction_count = f"{boundary_induction_count} (skipped:{str(boundary_ind.get('reason') or '-')})"
    except Exception:
        boundary_induction_count = "0"

    body_pid_suffix = f" (pid={body_pid})" if body_pid else ""

    qdt_short = "-"
    try:
        if isinstance(qtwin, dict):
            cands = qtwin.get("candidates")
            if isinstance(cands, list) and cands:
                parts: list[str] = []
                for c in cands[:3]:
                    if not isinstance(c, dict):
                        continue
                    act = str(c.get("action") or "").strip()
                    if not act:
                        continue
                    p_raw = c.get("p")
                    try:
                        p = float(p_raw) if p_raw is not None else None
                    except Exception:
                        p = None
                    parts.append(f"{act}:{p:.2f}" if p is not None else act)
                if parts:
                    qdt_short = ", ".join(parts)
    except Exception:
        qdt_short = "-"

    lines = [
        "AGI 운영 요약 (사람용)",
        f"- 생성: {obj['generated_at_utc']}",
        "",
        "1) 마지막 실행",
        f"- 액션: {latest_action}",
        f"- 상태: {latest_status}",
        f"- 시각: {latest_time}",
        f"- 이유: {latest_reason or '-'}",
        "",
        "2) 안전/윤리",
        f"- 판정: {safety_status}",
        f"- 플래그: {', '.join(map(str, safety_flags)) if safety_flags else '없음'}",
        f"- 권고: {safety_next or '-'}",
        "",
        "3) 오라(픽셀)",
        f"- 상태: {aura_state or '-'}",
        f"- 색: {aura_color or '-'}",
        f"- 이유: {aura_reason or '-'}",
        f"- 생존 상태: {str(life.get('state') or '-') if isinstance(life, dict) else '-'}",
        "",
        "3.5) 욕망/호기심(관측)",
        f"- 에너지: {str(ist_energy if ist_energy is not None else '-')}",
        f"- 지루함: {str(ist_boredom if ist_boredom is not None else '-')}",
        f"- 호기심: {str(ist_curiosity if ist_curiosity is not None else '-')}",
        f"- dominant_drive: {dominant_drive or '-'}",
        "",
        "4) 학습 신호(최근 갱신)",
        f"- obs_recode: {_fmt_age(ages['obs_recode'])}",
        f"- rua 대화: {_fmt_age(ages['rua_conversation'])}",
        f"- rua 경계 모드: {rua_boundary_mode or '없음'}",
        f"- 탐색 intake: {_fmt_age(ages['exploration_intake'])}",
        f"- 탐색 이벤트: {_fmt_age(ages['exploration_event'])}",
        f"- 비디오 경계 게이트: {_fmt_age(ages['video_boundary_gate'])}",
        f"- 유튜브 채널 경계: {_fmt_age(ages['youtube_channel_boundary'])}",
        f"- 경계 유도(자기 생성): {_fmt_age(ages['boundary_induction'])}",
        f"- 경계 유도 활성 규칙: {boundary_induction_count}",
        f"- 비노체 메모 인테이크: {_fmt_age(ages['binoche_note_intake'])}",
        f"- 브라우저 실행 로그: {_fmt_age(ages['body_latest'])}",
        f"- 시스템 갭 리포트: {_fmt_age(ages['system_gaps_report'])}",
        f"- 스텁 레이더: {_fmt_age(ages['stub_radar_report'])}",
        f"- 메타-감독 리포트: {_fmt_age(ages['meta_supervisor_report'])}",
        "",
        "5) 슈퍼바이즈 브라우저",
        f"- BodyController: {'실행 중' if body_running else '중지/미확인'}{body_pid_suffix}",
        f"- BodyLifeState: {_fmt_age(ages['body_life_state'])} (mode={str(body_life.get('mode') or '-')}, user_active={str(bool(body_life.get('user_active_recent')))})",
        f"- STOP_FILE(중지 요청): {'예' if stop_file_present else '아니오'}",
        (
            "- 해제 힌트: `scripts/windows/arm_supervised_body.ps1` 실행(중지 해제 + 단기 무장)"
            if stop_file_present
            else "- 해제 힌트: -"
        ),
        f"- allow(지속 허용): {'예' if allow_on else '아니오'}",
        f"- allow 만료까지: {_fmt_age(allow_expires_in_s) if allow_expires_in_s is not None else ('없음' if allow_on else '-')}",
        f"- arm(단기 무장): {'예' if armed else '아니오'}",
        f"- arm 만료까지: {_fmt_age(arm_expires_in_s) if arm_expires_in_s is not None else '없음'}",
        "",
        "6) 자연 리듬(동기화 관측)",
        f"- 시간대: {str(nclock.get('time_phase') or '-')}",
        f"- 권고 위상: {str(nclock.get('recommended_phase') or '-')}",
        f"- 드리프트: {'정상' if bool(ndrift.get('ok')) else '주의'}",
        f"- 이유: {', '.join(map(str, (ndrift.get('reasons') or [])[:3])) if isinstance(ndrift.get('reasons'), list) and ndrift.get('reasons') else '-'}",
        "",
        "7) ATP / 휴식 게이트",
        f"- ATP: {str(mito.get('atp_level') or '-')}",
        f"- ATP 상태: {str(mito.get('status') or '-')}",
        f"- RestGate: {str(rest_gate.get('status') or '-')}",
        f"- RestGate 시작: {str(rest_gate.get('rest_started_utc') or '-')}",
        f"- RestGate 만료: {str(rest_gate.get('rest_until_utc') or '-')}",
        f"- RestGate 이유: {', '.join(map(str, (rest_gate.get('reasons') or [])[:3])) if isinstance(rest_gate.get('reasons'), list) and rest_gate.get('reasons') else '-'}",
        "",
        "7.25) 통증/불일치(관측)",
        f"- rhythm_pain: {_fmt_age(ages['rhythm_pain'])} (pain={str(pain.get('pain_0_1') if isinstance(pain, dict) else '-')})",
        f"- 권고: {str(pain.get('recommendation') if isinstance(pain, dict) else '-') or '-'}",
        f"- 이유: {', '.join(map(str, (pain.get('reasons') or [])[:3])) if isinstance(pain, dict) and isinstance(pain.get('reasons'), list) and pain.get('reasons') else '-'}",
        "",
        "7.35) 디지털 트윈(관측)",
        f"- DigitalTwin: {_fmt_age(ages['digital_twin'])} (mismatch={str(twin.get('mismatch_0_1') if isinstance(twin, dict) else '-')}, route={str(twin.get('route_hint') if isinstance(twin, dict) else '-')})",
        f"- QDT 후보: {_fmt_age(ages['quantum_digital_twin'])} ({qdt_short})",
        "",
        "7.5) 림프/정화(관측)",
        (
            f"- glymphatic_metrics: {_fmt_age(ages['glymph_metrics'])} (ok)"
            if (ages.get("glymph_metrics") is not None and float(ages["glymph_metrics"]) < 30 * 60)
            else f"- glymphatic_metrics: {_fmt_age(ages['glymph_metrics'])} (최근 갱신이 오래되면 현재 루프에 미연결일 수 있음)"
        ),
        "",
        "8) 클라우드 LLM(관측)",
        f"- 사용 가능: {'예' if bool(cloud_backend.get('available')) else '아니오'}",
        f"- 백엔드: {str(cloud_backend.get('backend') or '-')}",
        f"- API Key 존재: {'예' if bool(cloud_backend.get('api_key_present')) else '아니오'}",
        f"- Vertex 프로젝트 설정: {'예' if bool(cloud_backend.get('vertex_project_set')) else '아니오'}",
        "",
        "9) a-b-c 링크(관측)",
        f"- a(과거/경험): obs_recode {_fmt_age(ages['obs_recode'])}, rua {_fmt_age(ages['rua_conversation'])}",
        f"- b(현재/생존): life_state {_fmt_age(_file_age_seconds(LIFE_STATE))}",
        f"- c(미래/탐색): event {_fmt_age(ages['exploration_event'])}, intake {_fmt_age(ages['exploration_intake'])}",
    ]
    OUT_TXT.write_text("\n".join(lines), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
