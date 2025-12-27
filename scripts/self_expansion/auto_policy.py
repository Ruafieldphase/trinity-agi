"""
Automatic trigger policy evaluator.
Reads current signals/logs/state to decide which trigger to emit.

Rules (initial defaults, can be extended):
- thought_stream staleness > THRESH_STALENESS_SEC -> self_acquire
- heartbeat file staleness > THRESH_STALENESS_SEC -> heartbeat_check
- last history entries with status failed >= 2 -> sync_clean
- fallback/default -> full_cycle

Outputs trigger JSON to signals/lua_trigger.json (Linux path preferred).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, List


THRESH_STALENESS_SEC = 15 * 60  # 15 minutes
THRESH_HEARTBEAT_STALE_SEC = 10 * 60  # 10 minutes
THRESH_HEARTBEAT_STALL_SEC = 5 * 60  # 5 minutes without count increase
THRESH_FAILURES = 2
THRESH_ERROR_RATIO = 0.5
THRESH_REPORT_STALE_SEC = 20 * 60  # 20 minutes
# "고정 인터벌"이 시스템의 리듬을 막지 않도록, 기본 쿨다운은 짧게 둔다.
# 리듬 신호는 관찰 대상으로만 유지하며 결정 기준에는 반영하지 않는다.
THRESH_DECISION_COOLDOWN_SEC = 60  # 60s base
THRESH_WAVE_PARTICLE_STALE_SEC = 2 * 3600  # 2 hours
THRESH_AUTOPOIETIC_STALE_SEC = 20 * 60  # 20 minutes
THRESH_SELFCARE_STALE_SEC = 30 * 60  # 30 minutes
THRESH_ANOMALIES_HIGH = 120
THRESH_LOOP_COMPLETE_RATE_LOW = 97.0
THRESH_FORCE_FULL_CYCLE_SEC = 45 * 60  # 45 minutes (ensure periodic learning loop)
THRESH_COMPRESS_STREAK = 3  # consecutive self_compress before forcing a full_cycle (if not critical)
THRESH_QFLOW_INTERVENTION_COOLDOWN_SEC = 30 * 60  # 30 minutes (avoid "compress loop" on persistent chaotic)
LEDGER_PATHS = [
    Path("/home/bino/agi/fdo_agi_repo/memory/resonance_ledger_v2.jsonl"),
    Path("/home/bino/agi/fdo_agi_repo/memory/resonance_ledger.jsonl"),
]
LEDGER_TAIL = 200
HISTORY_TAIL = 20
STATE_CACHE_LINUX = Path("/home/bino/agi/outputs/sync_cache/auto_policy_state.json")


def get_state_cache_path(root: Path) -> Path:
    """
    Linux VM에서는 고정 경로를 쓰고, 로컬 개발(Windows 등)에서는 워크스페이스 경로로 폴백한다.
    """
    try:
        # Windows에서 Path("/home/...")는 "C:\\home\\..."로 해석될 수 있고,
        # 실수로 생성된 C:\\home\\bino\\...가 존재하면 split-brain(상태 분기)을 유발한다.
        # Linux(=posix)에서만 고정 경로를 사용한다.
        if os.name == "posix" and STATE_CACHE_LINUX.parent.exists():
            return STATE_CACHE_LINUX
    except Exception:
        pass
    return root / "outputs" / "sync_cache" / "auto_policy_state.json"


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        # Windows/PowerShell 도구가 UTF-8 BOM을 붙이는 경우가 있어 utf-8-sig로 읽는다.
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def load_state_cache(state_cache: Path) -> Dict[str, Any]:
    if not state_cache.exists():
        return {}
    try:
        return json.loads(state_cache.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state_cache(state_cache: Path, data: Dict[str, Any]):
    try:
        state_cache.parent.mkdir(parents=True, exist_ok=True)
        state_cache.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def file_mtime(path: Path) -> Optional[float]:
    try:
        return path.stat().st_mtime
    except Exception:
        return None


def compute_experience_signatures(outputs: Path) -> Dict[str, str]:
    """
    Stable experience signatures (NOT file mtime).

    Why:
    - intake scripts rewrite their latest.json on every run (mtime always changes),
      which can create a self-triggering full_cycle loop.
    - signatures use "raw-derived stable fields" (newest file mtime/hash, latest session timestamp, etc.)
      so they only change when real inputs change.
    """
    sigs: Dict[str, str] = {}

    def _sig_obs_recode(p: Path) -> str | None:
        obj = load_json(p) or {}
        if not isinstance(obj, dict):
            return None
        newest = obj.get("newest") if isinstance(obj.get("newest"), dict) else {}
        m = newest.get("mtime")
        total = obj.get("total")
        try:
            m_f = float(m) if m is not None else None
        except Exception:
            m_f = None
        m_i = int(m_f) if m_f is not None else None
        try:
            total_i = int(total or 0)
        except Exception:
            total_i = 0
        if m_i is None and total_i == 0:
            return "empty"
        return f"newest_mtime={m_i};total={total_i}"

    def _sig_rua_conv(p: Path) -> str | None:
        obj = load_json(p) or {}
        if not isinstance(obj, dict):
            return None
        newest = obj.get("newest") if isinstance(obj.get("newest"), dict) else {}
        sha = str(newest.get("sha256_head") or "")
        m = newest.get("mtime")
        try:
            m_f = float(m) if m is not None else None
        except Exception:
            m_f = None
        # FS mtime은 소수점 정밀도가 환경/직렬화에 따라 흔들릴 수 있으므로 초 단위로 정규화한다.
        m_i = int(m_f) if m_f is not None else None
        try:
            total_i = int(obj.get("total_docs") or 0)
        except Exception:
            total_i = 0
        if not sha and m_i is None and total_i == 0:
            return "empty"
        return f"sha={sha};mtime={m_i};total={total_i}"

    def _sig_exploration_intake(p: Path) -> str | None:
        obj = load_json(p) or {}
        if not isinstance(obj, dict):
            return None
        latest = obj.get("latest_session") if isinstance(obj.get("latest_session"), dict) else {}
        ts = latest.get("timestamp")
        m_iso = str(latest.get("mtime_iso") or "")
        try:
            ts_f = float(ts) if ts is not None else None
        except Exception:
            ts_f = None
        try:
            sc = int(obj.get("session_count") or 0)
        except Exception:
            sc = 0
        try:
            mc = int(obj.get("media_count") or 0)
        except Exception:
            mc = 0
        if ts_f is None and sc == 0 and mc == 0:
            return "empty"
        return f"latest_ts={ts_f};mtime_iso={m_iso};sessions={sc};media={mc}"

    def _sig_exploration_event(p: Path) -> str | None:
        obj = load_json(p) or {}
        if not isinstance(obj, dict):
            return None
        ts = str(obj.get("timestamp_utc") or obj.get("timestamp") or "")
        sf = str(obj.get("session_file") or "")
        if not ts and not sf:
            return None
        return f"ts={ts};session_file={sf}"

    def _sig_feeling(p: Path) -> str | None:
        obj = load_json(p) or {}
        if not isinstance(obj, dict):
            return None
        ts = str(obj.get("timestamp") or "")
        if not ts:
            ari = obj.get("ari_new_experience") if isinstance(obj.get("ari_new_experience"), dict) else {}
            ts = str(ari.get("timestamp") or "")
        return ts or None

    sources = {
        "obs_recode": (outputs / "obs_recode_intake_latest.json", _sig_obs_recode),
        "rua_conversation": (outputs / "rua_conversation_intake_latest.json", _sig_rua_conv),
        "exploration_intake": (outputs / "exploration_intake_latest.json", _sig_exploration_intake),
        "exploration_event": (outputs / "exploration_session_event_latest.json", _sig_exploration_event),
        "feeling": (outputs / "feeling_latest.json", _sig_feeling),
    }
    for name, (path, fn) in sources.items():
        sig = fn(path)
        if sig:
            sigs[name] = sig
    return sigs


def read_history_tail(path: Path, n: int = HISTORY_TAIL) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        return [json.loads(l) for l in lines[-n:]]
    except Exception:
        return []


def read_ledger_tail(paths: List[Path], n: int = LEDGER_TAIL) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    for p in paths:
        if not p.exists():
            continue
        try:
            lines = p.read_text(encoding="utf-8").splitlines()[-n:]
            for l in lines:
                try:
                    events.append(json.loads(l))
                except Exception:
                    continue
        except Exception:
            continue
    return events


def choose_action(root: Path) -> Dict[str, Any]:
    now = time.time()
    cache_path = get_state_cache_path(root)
    cache = load_state_cache(cache_path)
    # Windows에서는 "/home/..."가 "C:\\home\\..."로 매핑될 수 있어 split-brain을 유발한다.
    if os.name == "posix":
        signals_dir = Path("/home/bino/agi/signals")
        if not signals_dir.exists():
            signals_dir = root / "signals"
    else:
        signals_dir = root / "signals"

    outputs = root / "outputs"
    memory = root / "memory"

    # --- Homeostasis upkeep (best-effort) ---
    # auto_policy는 '결정' 레이어이지만, 에너지/리듬 신호가 stale이면
    # 판단 자체가 자연 리듬에서 벗어날 수 있어 먼저 갱신을 시도한다.
    def _run_script_best_effort(rel: str, timeout_s: int = 8) -> None:
        try:
            p = root / rel
            if not p.exists():
                return
            creationflags = 0
            if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW"):
                creationflags = subprocess.CREATE_NO_WINDOW
            subprocess.run(
                [sys.executable, str(p)],
                cwd=root,
                check=False,
                capture_output=True,
                timeout=timeout_s,
                creationflags=creationflags,
            )
        except Exception:
            return

    def _is_stale(path: Path, stale_s: float) -> bool:
        m = file_mtime(path)
        return (m is None) or ((now - float(m)) > stale_s)

    try:
        clock = outputs / "natural_rhythm_clock_latest.json"
        if _is_stale(clock, 10 * 60):
            _run_script_best_effort("scripts/natural_rhythm_clock.py", timeout_s=6)
    except Exception:
        pass

    try:
        mito = outputs / "mitochondria_state.json"
        if _is_stale(mito, 5 * 60):
            _run_script_best_effort("scripts/atp_update.py", timeout_s=8)
    except Exception:
        pass

    try:
        rest_gate = outputs / "safety" / "rest_gate_latest.json"
        if _is_stale(rest_gate, 5 * 60):
            _run_script_best_effort("scripts/rest_gate.py", timeout_s=8)
    except Exception:
        pass

    # Safety review can be refreshed out-of-band; keep it reasonably fresh before gating decisions.
    try:
        constitution = outputs / "bridge" / "constitution_review_latest.json"
        # 60s 이상 stale이면 best-effort로 최신화(네트워크 없음; 로컬 리포트 생성).
        if _is_stale(constitution, 60):
            _run_script_best_effort("scripts/auto_constitution_review.py", timeout_s=8)
    except Exception:
        pass

    # --- Homeostasis: rest gate ---
    rest_gate = outputs / "safety" / "rest_gate_latest.json"
    rg = load_json(rest_gate) or {}
    try:
        if isinstance(rg, dict) and str(rg.get("status") or "").upper() == "REST":
            until = rg.get("rest_until_epoch")
            if isinstance(until, (int, float)) and float(until) > now:
                return {"action": "heartbeat_check", "reason": "rest_gate=REST (homeostasis)"}
    except Exception:
        pass

    bridge = outputs / "bridge"
    constitution_review = bridge / "constitution_review_latest.json"

    # A) Last safety decision gate: if the system is in REVIEW/BLOCK, do not advance into heavy cycles automatically.
    try:
        cobj = load_json(constitution_review) or {}
        cstat = str(cobj.get("status") or "").strip().upper()
    except Exception:
        cstat = ""
    if cstat == "BLOCK":
        return {"action": "heartbeat_check", "reason": "constitution BLOCK: hold (no autonomous actions)"}
    if cstat == "REVIEW":
        return {"action": "heartbeat_check", "reason": "constitution REVIEW: hold (await human check)"}
    if cstat == "CAUTION":
        # CAUTION에서는 정리/안정화만 자동으로 허용
        return {"action": "self_compress", "reason": "constitution CAUTION: stabilize (compress only)"}

    decision_cooldown_sec = THRESH_DECISION_COOLDOWN_SEC
    force_full_cycle_sec = THRESH_FORCE_FULL_CYCLE_SEC
    compress_streak_threshold = THRESH_COMPRESS_STREAK

    thought = outputs / "thought_stream_latest.json"
    heartbeat = outputs / "unconscious_heartbeat.json"
    state = memory / "agi_internal_state.json"
    history = bridge / "trigger_report_history.jsonl"
    latest_report = bridge / "trigger_report_latest.json"
    wave_particle_unified = outputs / "wave_particle_unified_latest.json"
    wave_particle_state = outputs / "sync_cache" / "wave_particle_state.json"
    autopoietic_report = outputs / "autopoietic_loop_report_latest.json"
    autopoietic_state = outputs / "sync_cache" / "autopoietic_report_state.json"
    sys_diag = outputs / "system_integration_diagnostic_latest.json"
    observer = outputs / "stream_observer_summary_latest.json"
    selfcare = outputs / "selfcare_summary_latest.json"
    rit_registry = outputs / "rit_registry_latest.json"
    obs_recode_intake = outputs / "obs_recode_intake_latest.json"
    rua_conversation_intake = outputs / "rua_conversation_intake_latest.json"
    exploration_intake = outputs / "exploration_intake_latest.json"
    feeling_latest = outputs / "feeling_latest.json"

    hb_m = file_mtime(heartbeat)
    hb_data = load_json(heartbeat) or {}
    hb_count = hb_data.get("heartbeat_count") or hb_data.get("state", {}).get("heartbeat_count")
    hb_state = hb_data.get("state") if isinstance(hb_data.get("state"), dict) else {}
    hb_curiosity = hb_state.get("curiosity")
    hb_drives = hb_state.get("drives") if isinstance(hb_state.get("drives"), dict) else {}
    hb_explore = hb_drives.get("explore")

    # --- Experience gate (highest priority among "growth" rules) ---
    # NOTE: intake 최신 JSON은 매 실행마다 rewrite되므로 파일 mtime 기반은 무한 루프를 만들 수 있다.
    # 따라서 "내부 안정 시그니처"로만 새 경험을 감지한다.
    exp_cache = cache.get("experience_signatures") if isinstance(cache.get("experience_signatures"), dict) else {}
    current_sigs = compute_experience_signatures(outputs)
    new_hits = [k for k, v in current_sigs.items() if exp_cache.get(k) != v]
    if new_hits:
        return {"action": "full_cycle", "reason": f"new experience detected: {', '.join(new_hits)}"}

    # 0) If the last report indicates a stuck cycle (missing symmetry), compress first.
    rep = load_json(latest_report) or {}
    rep_m = file_mtime(latest_report)
    rep_status = str(rep.get("status") or "")
    rep_result = rep.get("result_summary") if isinstance(rep.get("result_summary"), dict) else {}
    wave = rep_result.get("wave_tail") if isinstance(rep_result, dict) else {}
    autopoietic = wave.get("autopoietic") if isinstance(wave, dict) else {}
    last_rhythm_state = wave.get("last_rhythm_state") if isinstance(wave, dict) else {}
    last_wave_event = wave.get("last_event") if isinstance(wave, dict) else None

    def parse_ts(value) -> Optional[float]:
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if not isinstance(value, str) or not value:
                return None
            # ISO string
            from datetime import datetime

            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.timestamp()
        except Exception:
            return None

    last_wave_event_ts = None
    if isinstance(last_wave_event, dict):
        last_wave_event_ts = parse_ts(last_wave_event.get("timestamp") or last_wave_event.get("ts"))

    if (
        isinstance(autopoietic, dict)
        and autopoietic.get("exists") is True
        and isinstance(autopoietic.get("phases_missing"), list)
        and "symmetry" in autopoietic.get("phases_missing")
    ):
        # Avoid overreacting to an in-flight cycle; only act if it looks stuck for >2 minutes.
        if last_wave_event_ts and (now - last_wave_event_ts) < 120:
            pass
        else:
            return {"action": "self_compress", "reason": "autopoietic cycle missing symmetry"}

    # If recent cycle failed, prefer sync_clean.
    if rep_status == "failed" and rep_m and (now - rep_m) < THRESH_REPORT_STALE_SEC:
        return {"action": "sync_clean", "reason": "last trigger execution failed"}

    # 0.5) Rhythm state is observation-only; no branching decisions here.

    # 0.8) Output-driven policy: autopoietic + wave/particle + diagnostics (workspace-native signals)
    # Self-care / quantum_flow
    sc_m = file_mtime(selfcare)
    sc_obj = load_json(selfcare) or {}
    qflow = sc_obj.get("quantum_flow") if isinstance(sc_obj.get("quantum_flow"), dict) else {}
    q_state = str(qflow.get("state") or "").lower()
    try:
        q_coh = float(qflow.get("phase_coherence") or 0.0)
    except Exception:
        q_coh = 0.0
    if sc_m and (now - sc_m) > THRESH_SELFCARE_STALE_SEC:
        return {"action": "full_cycle", "reason": "selfcare summary stale"}
    if qflow and not qflow.get("error"):
        if q_state in ("resistive", "chaotic"):
            # "아무것도 안 해도 되는 상태"를 정상 생존으로 취급한다.
            # chaotic/resistive가 지속될 때 self_compress를 연속 실행하면 압축 루프가 되므로,
            # 일정 시간 동안은 개입을 멈추고 settle(idle)로 둔다.
            #
            # 단, settle이 "고정 인터벌"이 되면 리듬을 막을 수 있으므로:
            # - pain(라우팅 신호)이 낮고
            # - 자연 리듬이 EXPANSION이고
            # - 호기심/지루함이 높을 때는
            #   "정리(압축)" 대신 "관측/습득(self_acquire)"로 완만하게 우회할 수 있다.
            try:
                last_qflow_ts = float(cache.get("qflow_last_intervention_ts") or 0)
            except Exception:
                last_qflow_ts = 0.0

            settle_sec = int(THRESH_QFLOW_INTERVENTION_COOLDOWN_SEC)

            if last_qflow_ts and (now - last_qflow_ts) < settle_sec:
                return {"action": "idle", "reason": f"quantum_flow={q_state}: settle (idle)"}
            return {"action": "self_compress", "reason": f"quantum_flow={q_state}"}
        if q_state in ("superconducting", "coherent") and q_coh >= 0.7:
            return {"action": "self_acquire", "reason": f"quantum_flow={q_state}, coherence={q_coh:.2f}"}

    # Autopoietic report staleness / degradation
    auto_m = file_mtime(autopoietic_report)
    auto_obj = load_json(autopoietic_report) or {}
    rates = auto_obj.get("rates_pct") if isinstance(auto_obj.get("rates_pct"), dict) else {}
    counts = auto_obj.get("counts") if isinstance(auto_obj.get("counts"), dict) else {}
    try:
        loop_complete_rate = float(rates.get("loop_complete_rate") or 0.0)
    except Exception:
        loop_complete_rate = 0.0
    incomplete_loops = int(counts.get("incomplete_loops") or 0) if isinstance(counts, dict) else 0
    if auto_m and (now - auto_m) > THRESH_AUTOPOIETIC_STALE_SEC:
        return {"action": "full_cycle", "reason": "autopoietic report stale"}
    # Treat tiny incompleteness as noise; act only when it persists or completion rate drops.
    if incomplete_loops >= 3 or (loop_complete_rate and loop_complete_rate < THRESH_LOOP_COMPLETE_RATE_LOW):
        return {
            "action": "self_compress",
            "reason": f"autopoietic degraded: complete_rate={loop_complete_rate:.1f}, incomplete={incomplete_loops}",
        }

    # Wave/particle unified report freshness and anomaly pressure
    wp_m = file_mtime(wave_particle_unified)
    wp_obj = load_json(wave_particle_unified) or {}
    wp_meta = wp_obj.get("meta") if isinstance(wp_obj.get("meta"), dict) else {}
    wp_particle = wp_obj.get("particle_analysis") if isinstance(wp_obj.get("particle_analysis"), dict) else {}
    wp_particle_summary = wp_particle.get("summary") if isinstance(wp_particle.get("summary"), dict) else {}
    particles_detected = wp_particle_summary.get("particles_detected") if isinstance(wp_particle_summary.get("particles_detected"), dict) else {}
    anomalies = int(particles_detected.get("anomalies") or 0) if isinstance(particles_detected, dict) else 0
    sig_events = int(particles_detected.get("significant_events") or 0) if isinstance(particles_detected, dict) else 0
    most_sig = str(wp_particle_summary.get("most_significant") or "").lower()
    try:
        completeness = float(wp_meta.get("completeness_score") or 0.0)
    except Exception:
        completeness = 0.0
    # If unified output is stale and its own min-interval likely passed, request full_cycle.
    if wp_m and (now - wp_m) > THRESH_WAVE_PARTICLE_STALE_SEC:
        return {"action": "full_cycle", "reason": "wave_particle unified stale"}
    if sig_events > 0 and ("failed" in most_sig or "error" in most_sig):
        return {"action": "sync_clean", "reason": "wave_particle sees failed significant event"}
    if anomalies >= THRESH_ANOMALIES_HIGH:
        return {"action": "self_compress", "reason": f"high anomalies={anomalies}"}
    if completeness and completeness < 0.5:
        return {"action": "self_acquire", "reason": f"low completeness={completeness:.2f}"}

    # Diagnostics: if high-priority recommendations exist, bias toward compress (stabilize) then full_cycle.
    sys_obj = load_json(sys_diag) or {}
    recs = sys_obj.get("recommendations") if isinstance(sys_obj.get("recommendations"), list) else []
    high_recs = [r for r in recs if str(r.get("priority") or "").upper() == "HIGH"] if recs else []
    if high_recs:
        return {"action": "self_compress", "reason": f"system diag HIGH: {high_recs[0].get('issue') or 'unknown'}"}

    # Observer: if it has no data persistently, treat it as low-signal and run acquisition occasionally.
    obs_obj = load_json(observer) or {}
    obs_summary = obs_obj.get("summary") if isinstance(obs_obj.get("summary"), dict) else {}
    total_records = int(obs_summary.get("total_records") or 0) if isinstance(obs_summary, dict) else 0
    if total_records == 0 and (now % 1800) < 300:
        return {"action": "self_acquire", "reason": "observer has no records (periodic nudge)"}

    # 1) Staleness checks
    thought_m = file_mtime(thought)
    if thought_m and (now - thought_m) > THRESH_STALENESS_SEC:
        return {"action": "self_acquire", "reason": "thought_stream stale"}

    if hb_m and (now - hb_m) > THRESH_HEARTBEAT_STALE_SEC:
        return {"action": "heartbeat_check", "reason": "heartbeat stale"}

    # 1.5) Heartbeat stall detection (mtime advanced but count not advancing)
    last_count = cache.get("heartbeat_count")
    last_mtime = cache.get("heartbeat_mtime")
    if (
        hb_m
        and hb_count is not None
        and last_count is not None
        and last_mtime is not None
        and hb_m > last_mtime
        and hb_count <= last_count
        and (now - hb_m) > THRESH_HEARTBEAT_STALL_SEC
    ):
        return {"action": "heartbeat_check", "reason": "heartbeat stalled (count not increasing)"}

    # Update cache with latest heartbeat observation before further rules
    # (decision cache is saved in main(), so here we only keep heartbeat observation in-memory)

    # 2) Consecutive failures in history
    hist = read_history_tail(history, HISTORY_TAIL)
    fails = [h for h in hist if h.get("status") == "failed"]
    if len(fails) >= THRESH_FAILURES:
        return {"action": "sync_clean", "reason": "recent failures"}
    if hist:
        err_ratio = len(fails) / max(1, len(hist))
        if err_ratio >= THRESH_ERROR_RATIO:
            return {"action": "sync_clean", "reason": "high failure ratio"}

    # 2.5) RIT/경험 기반 분기 (관점→정책으로 연결)
    # - RIT: 위상 흔들림/회피(두려움 proxy)가 높으면 먼저 안정화(압축)로 간다.
    rit_obj = load_json(rit_registry) or {}
    rit_vals = rit_obj.get("current_values") if isinstance(rit_obj.get("current_values"), dict) else {}
    try:
        phase_jitter = float(rit_vals.get("phase_jitter_0_1")) if "phase_jitter_0_1" in rit_vals else None
    except Exception:
        phase_jitter = None
    try:
        fear_proxy = float(rit_vals.get("fear_proxy_avoid_0_1")) if "fear_proxy_avoid_0_1" in rit_vals else None
    except Exception:
        fear_proxy = None

    # --- Soft guard: avoid getting stuck in "compress only" forever ---
    # 최근 결정 히스토리를 보고, 과도한 self_compress 반복이면 주기적으로 full_cycle을 섞는다.
    # (단, 리듬 노이즈가 극단적으로 높을 때는 안정화가 우선)
    recent = cache.get("recent_decisions")
    recent_actions: List[str] = []
    if isinstance(recent, list):
        for item in recent[-10:]:
            if isinstance(item, dict):
                a = item.get("action")
                if isinstance(a, str) and a:
                    recent_actions.append(a)
            elif isinstance(item, str):
                recent_actions.append(item)

    compress_streak = 0
    for a in reversed(recent_actions):
        if a == "self_compress":
            compress_streak += 1
        else:
            break

    # Last full_cycle time (decision-level, not execution-level)
    last_full_cycle_ts = None
    if isinstance(recent, list):
        for item in reversed(recent):
            if isinstance(item, dict) and item.get("action") == "full_cycle":
                try:
                    last_full_cycle_ts = float(item.get("ts"))
                except Exception:
                    last_full_cycle_ts = None
                break
    force_full_cycle = (
        last_full_cycle_ts is None
        or (now - float(last_full_cycle_ts or 0)) > force_full_cycle_sec
    )
    if phase_jitter is not None and phase_jitter >= 0.75:
        if force_full_cycle and compress_streak >= compress_streak_threshold and phase_jitter < 0.92:
            return {"action": "full_cycle", "reason": f"compress_streak={compress_streak}, rit phase_jitter={phase_jitter:.2f} (periodic learning)"}
        return {"action": "self_compress", "reason": f"rit phase_jitter={phase_jitter:.2f} (stabilize)"}
    if fear_proxy is not None and fear_proxy >= 0.65:
        if force_full_cycle and compress_streak >= compress_streak_threshold and fear_proxy < 0.88:
            return {"action": "full_cycle", "reason": f"compress_streak={compress_streak}, rit fear_proxy={fear_proxy:.2f} (periodic learning)"}
        return {"action": "self_compress", "reason": f"rit fear_proxy={fear_proxy:.2f} (stabilize)"}

    # 3) 루아 신호 로그 파싱 (파서 추가 가능)
    lua_signals = bridge / "lua_signals.log"
    if lua_signals.exists():
        try:
            txt = lua_signals.read_text(encoding="utf-8")[-2000:]
            # 아주 단순한 키워드 트리거 예시
            if "sync" in txt.lower():
                return {"action": "sync_clean", "reason": "lua signal keyword: sync"}
            if "heartbeat" in txt.lower():
                return {"action": "heartbeat_check", "reason": "lua signal keyword: heartbeat"}
        except Exception:
            pass

    # 4) 레저 이벤트 기반: warn/error 감지
    ledger_events = read_ledger_tail(LEDGER_PATHS, LEDGER_TAIL)
    warns = [e for e in ledger_events if e.get("event") in ("warn", "error")]
    if warns:
        last = warns[-1]
        evt = last.get("event")
        reason = last.get("reason") or last.get("message") or "ledger warning"
        return {"action": "sync_clean", "reason": f"ledger {evt}: {reason}"}

    # 5) 자연 리듬은 관찰 대상이며 결정을 변경하지 않는다.

    # Default: "아무것도 안 해도 정상"인 생존 상태
    # - 새 경험은 이미 상단에서 full_cycle로 연결됨
    # - 그 외에는 굳이 '더 똑똑해지기' 위해 억지로 돌리지 않는다.
    return {"action": "idle", "reason": "idle is normal (no action required)"}


def write_trigger(trigger_path: Path, action: str, params: dict | None = None, origin: str = "lua-auto-policy"):
    trigger = {
        "action": action,
        "params": params or {},
        "timestamp": time.time(),
        "origin": origin,
    }
    trigger_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(trigger, ensure_ascii=False, indent=2)
    # Never overwrite an existing trigger: use exclusive create to avoid race with manual/Lua triggers.
    try:
        fd = os.open(str(trigger_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    except FileExistsError:
        return None
    except Exception:
        # Fallback: if exclusive create fails, still avoid overwrite.
        if trigger_path.exists():
            return None
        trigger_path.write_text(payload, encoding="utf-8")
        return trigger
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
    finally:
        pass
    return trigger


def main():
    root = Path(__file__).resolve().parents[2]  # c:/workspace/agi or /home/bino/agi
    # On Windows, always write to workspace-local trigger path to avoid split-brain triggers.
    if os.name != "posix":
        trigger_path = root / "signals" / "lua_trigger.json"
    else:
        trigger_path = Path("/home/bino/agi/signals/lua_trigger.json")
        if not trigger_path.parent.exists():
            trigger_path = root / "signals" / "lua_trigger.json"

    # Capture heartbeat observation for cache
    hb_path = root / "outputs" / "unconscious_heartbeat.json"
    hb_m = file_mtime(hb_path)
    hb_data = load_json(hb_path) or {}
    hb_count = hb_data.get("heartbeat_count") or hb_data.get("state", {}).get("heartbeat_count")

    decision = choose_action(root)
    rhythm_mode_value = ""
    rhythm_mode = None
    try:
        from agi_core.rhythm_boundaries import RhythmBoundaryManager  # type: ignore

        boundary_manager = RhythmBoundaryManager(root)
        rhythm_mode = boundary_manager.detect_rhythm_mode()
        rhythm_mode_value = rhythm_mode.value if rhythm_mode else ""
    except Exception:
        rhythm_mode = None
        rhythm_mode_value = ""
    rhythm_snapshot = {}
    try:
        clock = load_json(root / "outputs" / "natural_rhythm_clock_latest.json") or {}
        if isinstance(clock, dict):
            rhythm_snapshot = {
                "timestamp": clock.get("timestamp"),
                "time_phase": clock.get("time_phase"),
                "recommended_phase": clock.get("recommended_phase"),
                "bio_rhythm": clock.get("bio_rhythm"),
            }
    except Exception:
        rhythm_snapshot = {}

    decision_cooldown_sec = THRESH_DECISION_COOLDOWN_SEC

    # Decision thrash guard: if we chose the same action too recently, fall back to a lightweight alternative.
    cache_path = get_state_cache_path(root)
    cache = load_state_cache(cache_path)
    last_action = cache.get("last_decision_action")
    last_ts = float(cache.get("last_decision_ts") or 0)
    # Global throttle: auto_policy가 (버그/중복 데몬 등으로) 너무 자주 호출되더라도,
    # "트리거를 쓰는 행위"는 최소 주기 이하로 반복하지 않는다.
    # - full_cycle은 새 경험을 처리해야 하므로 예외로 둔다.
    now_ts = time.time()
    if last_ts and (now_ts - last_ts) < decision_cooldown_sec and decision.get("action") != "full_cycle":
        decision = {"action": "idle", "reason": "cooldown: global throttle"}
    elif last_action == decision.get("action") and last_ts and (now_ts - last_ts) < decision_cooldown_sec:
        # Prefer a stable low-cost action that still progresses.
        # NOTE: idle은 반복되어도 정상이다(=생존 상태). 쿨다운으로 다른 액션으로 바꾸지 않는다.
        if decision.get("action") == "idle":
            pass
        elif decision["action"] == "self_compress":
            decision = {"action": "idle", "reason": "cooldown: avoid repeated self_compress"}
        elif decision["action"] == "self_acquire":
            decision = {"action": "idle", "reason": "cooldown: avoid repeated self_acquire"}
        else:
            decision = {"action": "idle", "reason": "cooldown: avoid repeated action"}

    # Idle은 "정상 생존 상태"이므로 트리거를 만들지 않는다(=아무 일도 안 일어나는 것이 정상).
    # 관측 가능한 생존 신호는 run_trigger_once.py의 idle_tick이 담당한다.
    if decision.get("action") == "idle":
        created = None
    else:
        created = write_trigger(trigger_path, decision["action"], {"reason": decision.get("reason")})
    # Capture experience mtimes.
    exp_sources = {
        "obs_recode_intake_latest.json": root / "outputs" / "obs_recode_intake_latest.json",
        "rua_conversation_intake_latest.json": root / "outputs" / "rua_conversation_intake_latest.json",
        "exploration_intake_latest.json": root / "outputs" / "exploration_intake_latest.json",
        "exploration_session_event_latest.json": root / "outputs" / "exploration_session_event_latest.json",
        "feeling_latest.json": root / "outputs" / "feeling_latest.json",
    }
    exp_mtimes = {}
    for name, path in exp_sources.items():
        exp_mtimes[name] = file_mtime(path)

    # Stable experience signatures (not mtime) — used to prevent self-generated output loops.
    exp_sigs = compute_experience_signatures(root / "outputs")

    # 경험 입력 캐시 갱신 규칙:
    # - 경험 시그니처는 "이번에 full_cycle을 선택했다"는 사실만으로도 갱신한다.
    #   (트리거 파일이 이미 존재해 created=None이 되더라도, 동일 경험을 '새 경험'으로 계속 오인하지 않도록)
    # - mtime 기반 캐시는 legacy로 유지하되, 새 구현은 experience_signatures를 사용한다.
    if decision.get("action") == "full_cycle":
        next_exp_cache = exp_mtimes
        next_sig_cache = exp_sigs if isinstance(exp_sigs, dict) else {}
    else:
        next_exp_cache = cache.get("experience_mtimes") if isinstance(cache.get("experience_mtimes"), dict) else exp_mtimes
        next_sig_cache = cache.get("experience_signatures") if isinstance(cache.get("experience_signatures"), dict) else {}

    qflow_last_intervention_ts = cache.get("qflow_last_intervention_ts")
    try:
        if decision.get("action") == "self_compress" and str(decision.get("reason") or "").startswith("quantum_flow="):
            qflow_last_intervention_ts = time.time()
    except Exception:
        pass
    save_state_cache(
        cache_path,
        {
            **cache,
            "last_decision_action": decision.get("action"),
            "last_decision_ts": time.time(),
            "last_decision_reason": decision.get("reason"),
            "heartbeat_count": hb_count,
            "heartbeat_mtime": hb_m,
            "experience_mtimes": next_exp_cache,
            "experience_signatures": next_sig_cache,
            "qflow_last_intervention_ts": qflow_last_intervention_ts,
            "rhythm_mode": rhythm_mode_value,
            "rhythm_snapshot": rhythm_snapshot,
            "recent_decisions": (
                (cache.get("recent_decisions") if isinstance(cache.get("recent_decisions"), list) else [])
                + [{"ts": time.time(), "action": decision.get("action"), "reason": decision.get("reason")}]
            )[-50:],
        }
    )
    if decision.get("action") == "idle":
        print(json.dumps({**decision, "skipped_trigger": True}, ensure_ascii=False))
    elif created is None:
        print(json.dumps({"skipped": True, "reason": "trigger_exists", "decision": decision}, ensure_ascii=False))
    else:
        print(json.dumps(decision, ensure_ascii=False))


if __name__ == "__main__":
    main()
