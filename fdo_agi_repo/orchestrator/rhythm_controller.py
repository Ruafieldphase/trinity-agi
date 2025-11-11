"""
RhythmController
 - neuromodulator_state(D,S,O) → (alpha, beta, theta_overlap)
 - Map to tool/LLM params: temperature, top_k, synth_max_tokens, verify_rounds, tone, safety

Design goals
 - Be resilient: works even when no ledger exists
 - Cheap: O(lines) scan of tail if available, else defaults
 - Deterministic: small jitter only from recent signals
"""
from __future__ import annotations
from typing import Dict, Any, Tuple
import os
import json
from pathlib import Path

LEDGER_PATH = Path(__file__).resolve().parents[1] / "memory" / "resonance_ledger.jsonl"


def _safe_read_trend(window: int = 2000) -> Dict[str, float]:
    """Read last N lines from ledger and compute coarse D/S/O proxies.
    Heuristics:
      - dopamine (D): recent success/ok ratio
      - serotonin (S): recent stability (low error density)
      - oxytocin (O): recent collaboration/merge/assist events density
    Returns values in [0,1].
    """
    if not LEDGER_PATH.exists():
        return {"D": 0.5, "S": 0.5, "O": 0.5}

    try:
        lines = LEDGER_PATH.read_text(encoding="utf-8").splitlines()[-window:]
        total = 0
        ok = 0
        errors = 0
        social = 0
        for ln in lines:
            if not ln.strip():
                continue
            try:
                ev = json.loads(ln)
            except Exception:
                continue
            total += 1
            evn = (ev.get("event") or "").lower()
            if "error" in evn or ev.get("level") == "error":
                errors += 1
            if any(k in evn for k in ("complete","end","ok","success","pass")):
                ok += 1
            if any(k in evn for k in ("assist","merge","handoff","collab","cooperate","ally")):
                social += 1
        if total <= 0:
            return {"D": 0.5, "S": 0.5, "O": 0.5}
        d = max(0.0, min(1.0, ok / total))
        s = max(0.0, min(1.0, 1.0 - (errors / total)))
        o = max(0.0, min(1.0, social / max(1, total//10)))  # smoother
        return {"D": d, "S": s, "O": o}
    except Exception:
        return {"D": 0.5, "S": 0.5, "O": 0.5}


def estimate_signals() -> Dict[str, float]:
    """Public entry: combine env overrides with observed trend.
    Env override: RHYTHM_OVERRIDE_JSON='{"D":0.7,"S":0.6,"O":0.4}'
    """
    trend = _safe_read_trend()
    override = os.environ.get("RHYTHM_OVERRIDE_JSON")
    if override:
        try:
            ov = json.loads(override)
            for k in ("D","S","O"):
                if k in ov and isinstance(ov[k], (int,float)):
                    trend[k] = float(ov[k])
        except Exception:
            pass
    return trend


def map_to_params(
    signals: Dict[str, float],
    fear_level: float | None = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Map neuromodulator signals to alpha/beta/theta and practical hints.
    
    Args:
        signals: D/S/O neuromodulator signals
        fear_level: 편도체 신호 (0.0~1.0, optional)
            - 높은 두려움 → beta 증가 (대립), alpha 감소 (깊이)
            - 낮은 두려움 → alpha 증가, beta 감소
    
    Returns (rhythm_params, optimization_hint)
    """
    D = float(signals.get("D", 0.5))
    S = float(signals.get("S", 0.5))
    O = float(signals.get("O", 0.5))
    F = fear_level if fear_level is not None else 0.35  # 기본 경계심

    # Core parameters with fear integration
    # 높은 두려움 → 깊이 감소(alpha↓), 대립 증가(beta↑)
    alpha = round(0.5 + 0.5 * S * (1.0 - 0.3 * F), 3)  # fear dampens depth
    beta = round(0.3 + 0.7 * (1.0 - D) + 0.2 * F, 3)  # fear boosts opposition
    theta_overlap = round(0.2 + 0.5 * O * (1.0 - 0.2 * F), 3)  # fear reduces overlap

    # LLM/tool mappings with fear consideration
    # 높은 두려움 → temperature 감소 (더 안전), verify_rounds 증가
    base_temp = 0.3 + 0.4 * (1.0 - S) + 0.3 * (1.0 - D)
    temperature = round(base_temp * (1.0 - 0.25 * F), 2)  # fear reduces temperature
    top_k = int(20 + 40 * S * (1.0 - 0.15 * F))  # fear narrows top_k
    synth_max_tokens = int(400 + 600 * alpha)
    
    # 두려움 높을 때 검증 라운드 증가
    if F >= 0.7:
        verify_rounds = 3
    elif F >= 0.5:
        verify_rounds = 2
    else:
        verify_rounds = 1 if S > 0.6 else 2 if S > 0.35 else 3

    # Routing and throttling hints
    preferred_channels = ["primary"] if D >= 0.5 and F < 0.6 else ["primary","fallback"]
    should_throttle_offpeak = (D < 0.35) or (F >= 0.6)  # fear triggers throttling
    batch_compression_level = 0 if O < 0.4 else (1 if O < 0.7 else 2)

    rhythm_params = {
        "alpha": alpha,
        "beta": beta,
        "theta_overlap": theta_overlap,
        "temperature": temperature,
        "top_k": top_k,
        "synth_max_tokens": synth_max_tokens,
        "verify_rounds": verify_rounds,
        "fear_level": F,  # 추가: fear 레벨 전파
    }

    optimization_hint = {
        "preferred_channels": preferred_channels,
        "should_throttle_offpeak": should_throttle_offpeak,
        "batch_compression_level": batch_compression_level,
        "theta_overlap": theta_overlap,
        # Additional knobs future personas/tooling may read
        "llm_temperature": temperature,
        "llm_top_k": top_k,
        "verify_rounds": verify_rounds,
    }
    return rhythm_params, optimization_hint


__all__ = ["estimate_signals", "map_to_params"]
"""
RhythmController: 리듬적 S→D 결합을 기반으로 합(統合) 파라미터 산출

안전한 기본값을 제공하며, 레저가 비어있거나 입력이 부족해도 동작합니다.
출력: alpha(합 깊이), beta(대립 폭), theta_overlap(오버랩 임계) 및 LLM 매개변수 힌트
"""
from typing import Dict, Any, Tuple
import os
import json
import time

LEDGER_PATH_DEFAULT = os.path.join(os.path.dirname(__file__), "..", "memory", "resonance_ledger.jsonl")


def _sigmoid(x: float) -> float:
    try:
        import math
        return 1.0 / (1.0 + math.exp(-x))
    except Exception:
        return 0.5


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return hi if v > hi else (lo if v < lo else v)


def _ema(prev: float, new: float, alpha: float) -> float:
    return (1 - alpha) * prev + alpha * new


def _read_recent_ledger_stats(path: str, max_lines: int = 500) -> Dict[str, Any]:
    """최근 레저 통계를 간단히 집계(진입 비용 최소화). 실패 시 안전한 기본값 반환."""
    stats = {
        "ok_ratio": 0.8,
        "error_ratio": 0.0,
        "avg_duration": 1.0,
        "events": 0,
    }
    try:
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        if not os.path.exists(path):
            return stats
        ok = err = 0
        durations = []
        cnt = 0
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-max_lines:]
        for line in lines:
            cnt += 1
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                if obj.get("ok") is True:
                    ok += 1
                if obj.get("ok") is False or obj.get("error"):
                    err += 1
                d = obj.get("duration_sec")
                if isinstance(d, (int, float)):
                    durations.append(float(d))
        stats["events"] = cnt
        total = max(1, ok + err)
        stats["ok_ratio"] = ok / total
        stats["error_ratio"] = err / total
        if durations:
            stats["avg_duration"] = sum(durations) / len(durations)
        return stats
    except Exception:
        return stats


def estimate_signals(ledger_path: str = LEDGER_PATH_DEFAULT) -> Dict[str, float]:
    """
    뉴로모듈레이터 신호 추정(D,S,O in [0,1]).
    - 매우 경량: 최근 레저 성공률/에러율/지속시간만 사용.
    - 레저가 없으면 안전한 기본값(0.5/0.6/0.6)을 반환.
    """
    stats = _read_recent_ledger_stats(ledger_path)
    okr = float(stats.get("ok_ratio", 0.8))
    err = float(stats.get("error_ratio", 0.0))
    dur = float(stats.get("avg_duration", 1.0))

    # 도파민: 성과 상승 시↑, 에러 시↓, 지나치게 오래 걸리면 소폭↓
    d_base = _clamp(0.5 + 0.4 * (okr - 0.5) - 0.1 * err - 0.05 * (max(0.0, dur - 2.0) / 4.0))
    # 세로토닌: 안정·인내 — 에러↑면 오히려 안정화 필요로 해석해 약간↑, 너무 길면 피로로 약간↑
    s_base = _clamp(0.6 + 0.1 * err + 0.05 * (max(0.0, dur - 2.0) / 4.0))
    # 옥시토신: 신뢰/협력 — 성공률↑면↑, 에러↑면↓
    o_base = _clamp(0.6 + 0.3 * (okr - 0.5) - 0.2 * err)

    # 간단한 리듬 위상: 일중 리듬을 약하게 섞어 비대칭성 부여(옵셔널)
    try:
        import math
        t = time.time()
        circ = math.cos((t % 86400) / 86400.0 * 2 * math.pi)
        s_base = _clamp(_ema(s_base, _sigmoid(0.5 * circ), 0.15))
    except Exception:
        pass

    # S가 D를 밀어주는 결합항: D_eff = D_raw + λ1*S (변화율 항은 경량 버전에서 생략)
    lam1 = 0.2
    d_eff = _clamp(d_base + lam1 * s_base)

    return {"D": d_eff, "S": s_base, "O": o_base}


def map_to_params(signals: Dict[str, float], fear_level: float = 0.35) -> Tuple[Dict[str, float], Dict[str, Any]]:
    """
    신호(D,S,O)→ (rhythm_params, optimization_hint)
    rhythm_params: alpha, beta, theta_overlap ∈ [0,1]
    optimization_hint: persona에 전달할 가벼운 힌트(채널·스로틀·배치)
    fear_level: 편도체 신호 (0=안전, 1=극심한 위협)
    """
    D = float(signals.get("D", 0.5))
    S = float(signals.get("S", 0.6))
    O = float(signals.get("O", 0.6))
    
    # 두려움 통합: 높은 fear → alpha↓(탐색↓), beta↑(경계↑)
    fear_clamped = _clamp(fear_level)
    fear_impact = fear_clamped - 0.35  # 중심점

    # 분산/충돌이 없으므로 경량 상수 기반
    alpha = _clamp(0.5 + 0.3 * S - 0.1 * abs(D - 0.5) - 0.2 * fear_impact)
    beta  = _clamp(0.4 + 0.4 * abs(D - 0.5) - 0.2 * O + 0.25 * fear_impact)
    theta = _clamp(0.5 - 0.3 * D + 0.2 * S)

    rhythm_params = {
        "alpha": alpha,
        "beta": beta,
        "theta_overlap": theta,
        "fear_level": fear_clamped,  # 추적용
        "temperature": _clamp(0.7 - 0.3 * fear_impact),
        "verify_rounds": int(1 + fear_clamped * 2),  # fear↑ → 검증↑
    }

    # Optimization hints for personas (respected by antithesis persona already)
    preferred = []
    if beta > 0.6:
        preferred.append("gateway")  # 탐색 폭↑일 때 게이트웨이 우선
    if O > 0.6:
        preferred.append("cloud_ai")  # 신뢰↑일 때 클라우드 채널 허용
    if not preferred:
        preferred = ["local_llm"]  # 기본 로컬 선호 (테스트 친화)

    hint: Dict[str, Any] = {
        "preferred_channels": preferred,
        "should_throttle_offpeak": bool(S > 0.65 and D < 0.55),
        "batch_compression": bool(alpha > 0.65),
        "batch_compression_level": "high" if alpha > 0.75 else ("low" if alpha > 0.6 else "off"),
        "theta_overlap": theta,
        "alpha": alpha,
        "beta": beta,
        "oxytocin": O,
    }
    return rhythm_params, hint
