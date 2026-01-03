"""
Self-Trigger Module
외부 입력 없이 내부 정보만으로 AGI가 스스로 깨어나는 계기(trigger)를 생성합니다.

트리거 유형:
- UNRESOLVED_PATTERN: 미해결 패턴/이슈가 남았을 때
- BOREDOM: 최근 맥락 변화가 거의 없을 때
- CURIOSITY_CONFLICT: 상반된 패턴/정보가 감지될 때
- MODEL_DRIFT: 내부 모델과 실제 데이터의 불일치가 커질 때
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from agi_core.rhythm_boundaries import RhythmBoundaryManager


class TriggerType(str, Enum):
    """자기-트리거 유형"""
    UNRESOLVED_PATTERN = "UNRESOLVED_PATTERN"
    BOREDOM = "BOREDOM"
    CURIOSITY_CONFLICT = "CURIOSITY_CONFLICT"
    MODEL_DRIFT = "MODEL_DRIFT"
    EMOTIONAL_RESONANCE = "EMOTIONAL_RESONANCE"  # 외부 감정 신호 공명
    ACOUSTIC_ANOMALY = "ACOUSTIC_ANOMALY"        # 소리 신호 이상 탐지
    MIMESIS_STALL = "MIMESIS_STALL"              # 리듬 정체 (미메시스 실패)


@dataclass
class TriggerEvent:
    """트리거 이벤트 데이터"""
    type: TriggerType
    score: float              # 0.0 ~ 1.0 (강도)
    reason: str               # 사람이 읽을 수 있는 설명
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "score": self.score,
            "reason": self.reason,
            "payload": self.payload
        }


def _load_jsonl(path: str, max_lines: int = 500) -> List[Dict[str, Any]]:
    """JSONL 파일에서 최신 N개 항목을 로드"""
    if not os.path.exists(path):
        return []
    
    entries = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except Exception:
        return []
    
    # 최신 항목만 반환
    return entries[-max_lines:] if len(entries) > max_lines else entries


def _load_json(path: str) -> Dict[str, Any]:
    """JSON 파일 로드"""
    if not os.path.exists(path):
        return {}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def compute_unresolved_pattern_trigger(
    resonance_ledger_path: str,
    threshold: float = 0.6,
) -> Optional[TriggerEvent]:
    """
    resonance_ledger.jsonl에서 미해결/실패 상태의 비율을 분석하여
    UNRESOLVED_PATTERN 트리거 생성 여부를 결정합니다.
    """
    entries = _load_jsonl(resonance_ledger_path, max_lines=100)
    
    if not entries:
        return None
    
    # 상태별 카운트
    failed_count = 0
    pending_count = 0
    total_count = 0
    
    for entry in entries:
        status = entry.get("status", "")
        event = entry.get("event", "")
        
        if "failed" in status or "failed" in event:
            failed_count += 1
        elif "pending" in status:
            pending_count += 1
        total_count += 1
    
    if total_count == 0:
        return None
    
    # 미해결 비율 계산
    unresolved_ratio = (failed_count + pending_count) / total_count
    
    if unresolved_ratio >= threshold:
        return TriggerEvent(
            type=TriggerType.UNRESOLVED_PATTERN,
            score=min(unresolved_ratio, 1.0),
            reason=f"미해결 패턴 비율이 높음: {unresolved_ratio:.1%} (failed={failed_count}, pending={pending_count})",
            payload={
                "failed_count": failed_count,
                "pending_count": pending_count,
                "total_count": total_count,
                "ratio": unresolved_ratio
            }
        )
    
    return None


def compute_boredom_trigger(
    learning_log_path: str,
    min_idle_seconds: int = 60 * 30,  # 30분
) -> Optional[TriggerEvent]:
    """
    learning_log.jsonl의 마지막 이벤트 시간 기준으로
    일정 시간 이상 활동이 없으면 BOREDOM 트리거를 생성합니다.
    """
    entries = _load_jsonl(learning_log_path, max_lines=50)
    
    if not entries:
        # 로그가 없으면 매우 지루한 상태
        return TriggerEvent(
            type=TriggerType.BOREDOM,
            score=1.0,
            reason="학습 로그가 비어 있음 - 완전한 휴면 상태",
            payload={"last_activity": None, "idle_seconds": float("inf")}
        )
    
    # 마지막 항목의 타임스탬프 파싱
    last_entry = entries[-1]
    timestamp_str = last_entry.get("timestamp", "")
    
    if not timestamp_str:
        return None
    
    try:
        # ISO 형식 파싱
        if "T" in timestamp_str:
            last_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        else:
            return None
    except ValueError:
        return None
    
    # 현재 시간과 비교 (UTC 기준)
    now = datetime.now(timezone.utc)
    if last_time.tzinfo is None:
        last_time = last_time.replace(tzinfo=timezone.utc)
    
    idle_seconds = (now - last_time).total_seconds()
    
    if idle_seconds >= min_idle_seconds:
        # 점수: idle_seconds가 길수록 높음 (최대 1.0)
        max_idle_for_max_score = 60 * 60 * 2  # 2시간이면 최대 점수
        score = min(idle_seconds / max_idle_for_max_score, 1.0)
        
        idle_minutes = idle_seconds / 60
        return TriggerEvent(
            type=TriggerType.BOREDOM,
            score=score,
            reason=f"마지막 활동으로부터 {idle_minutes:.0f}분 경과 - 새로운 자극 필요",
            payload={
                "last_activity": timestamp_str,
                "idle_seconds": idle_seconds,
                "idle_minutes": idle_minutes
            }
        )
    
    return None


def compute_curiosity_conflict_trigger(
    learned_patterns_path: str,
    threshold: float = 0.5,
) -> Optional[TriggerEvent]:
    """
    learned_patterns.json에서 상반된 결과를 가진 패턴을 탐지하여
    CURIOSITY_CONFLICT 트리거를 생성합니다.
    """
    patterns = _load_json(learned_patterns_path)
    
    if not patterns:
        return None
    
    conflicts = []
    
    for pattern_key, pattern_data in patterns.items():
        count = pattern_data.get("count", 0)
        success_count = pattern_data.get("success_count", 0)
        success_rate = pattern_data.get("success_rate", 1.0)
        
        # 성공률이 중간(0.3~0.7) 범위이면 충돌로 간주
        if count >= 2 and 0.3 <= success_rate <= 0.7:
            conflict_score = 1.0 - abs(success_rate - 0.5) * 2  # 0.5에서 최대
            conflicts.append({
                "pattern": pattern_key,
                "success_rate": success_rate,
                "count": count,
                "conflict_score": conflict_score
            })
    
    if not conflicts:
        return None
    
    # 가장 높은 충돌 점수
    max_conflict = max(conflicts, key=lambda x: x["conflict_score"])
    
    if max_conflict["conflict_score"] >= threshold:
        return TriggerEvent(
            type=TriggerType.CURIOSITY_CONFLICT,
            score=max_conflict["conflict_score"],
            reason=f"패턴 '{max_conflict['pattern']}'에서 상반된 결과 감지 (성공률: {max_conflict['success_rate']:.1%})",
            payload={
                "conflicting_patterns": conflicts,
                "primary_conflict": max_conflict
            }
        )
    
    return None


def compute_model_drift_trigger(
    digital_twin_state_path: Optional[str] = None,
    recent_observations_path: Optional[str] = None,
    threshold: float = 0.7,
) -> Optional[TriggerEvent]:
    """
    디지털 트윈 상태와 실제 관측값의 차이를 측정하여
    MODEL_DRIFT 트리거를 생성합니다.
    """
    # 디지털 트윈 파일 확인
    if not digital_twin_state_path:
        base_dir = Path(__file__).parent.parent / "outputs" / "sync_cache"
        digital_twin_state_path = str(base_dir / "digital_twin_state.json")

    if os.path.exists(digital_twin_state_path):
        twin_state = _load_json(digital_twin_state_path)
    else:
        twin_state = {}
    
    # 디지털 트윈이 아직 준비되지 않은 경우
    if not twin_state:
        return None
    
    # 디지털 트윈의 mismatch 값을 직접 사용
    mismatch = twin_state.get("mismatch_0_1", 0.0)
    
    if mismatch >= threshold:
        return TriggerEvent(
            type=TriggerType.MODEL_DRIFT,
            score=min(mismatch, 1.0),
            reason=f"디지털 트윈 불일치(Mismatch) 감지: {mismatch:.2f} (Threshold: {threshold:.2f})",
            payload={
                "mismatch": mismatch,
                "route_hint": twin_state.get("route_hint"),
                "timestamp": twin_state.get("generated_at_utc"),
                "observed_action": twin_state.get("observed", {}).get("last_action")
            }
        )
    
    return None
    
    return None


def compute_emotional_resonance_trigger(
    resonance_ledger_path: str,
    threshold: float = 0.6,
) -> Optional[TriggerEvent]:
    """
    Core(Core)의 감정 상태를 분석하여 EMOTIONAL_RESONANCE 트리거를 생성합니다.
    """
    entries = _load_jsonl(resonance_ledger_path, max_lines=50)
    
    if not entries:
        return None
    
    # Core의 최신 감정 이벤트 필터링
    Core_events = [e for e in entries if e.get("who") == "Core"]
    if not Core_events:
        return None
    
    latest_event = Core_events[-1]
    fear = latest_event.get("fear", 0.0)
    anxiety = latest_event.get("anxiety", 0.0)
    resonance_score = latest_event.get("resonance_score", 0.7)
    
    # 불안이나 공포가 높으면 공명 트리거 발생
    emotional_intensity = max(fear, anxiety)
    
    if emotional_intensity >= threshold:
        return TriggerEvent(
            type=TriggerType.EMOTIONAL_RESONANCE,
            score=emotional_intensity,
            reason=f"Core의 정서적 불안 감지 (Intensity: {emotional_intensity:.2f})",
            payload={
                "fear": fear,
                "anxiety": anxiety,
                "note": latest_event.get("emotion_note", ""),
                "resonance_score": resonance_score
            }
        )
    
    return None


def compute_acoustic_anomaly_trigger(
    output_dir: str,
    threshold: float = 0.75,
) -> Optional[TriggerEvent]:
    """
    최신 소리 탐사 결과를 분석하여 ACOUSTIC_ANOMALY 트리거를 생성합니다.
    """
    # outputs 디렉토리에서 최신 acoustic_probe_*.json 찾기
    p = Path(output_dir)
    json_files = sorted(list(p.glob("acoustic_probe_*.json")), key=os.path.getmtime)
    
    if not json_files:
        return None
    
    latest_probe = _load_json(str(json_files[-1]))
    if not latest_probe:
        return None
    
    # 주파수 응답의 피크 개수나 강도를 분석
    fr_peaks = latest_probe.get("frequency_response_peaks", [])
    
    # 예: 피크가 너무 많거나(노이즈), 특정 주파수 대역의 에너지가 너무 높을 때
    if len(fr_peaks) > 15:
        score = min(len(fr_peaks) / 25, 1.0)
        if score >= threshold:
            return TriggerEvent(
                type=TriggerType.ACOUSTIC_ANOMALY,
                score=score,
                reason=f"소리 환경의 복잡도/노이즈 급증 탐지 (Peaks: {len(fr_peaks)})",
                payload={"peak_count": len(fr_peaks), "source": json_files[-1].name}
            )
            
    return None


def compute_mimesis_stall_trigger(
    thought_history_path: str,
    threshold_consecutive_neutral: int = 5,
) -> Optional[TriggerEvent]:
    """
    thought_stream_history.jsonl을 분석하여 리듬 점수가 50점 근처에서
    장기간 정체되거나 공명이 'Void' 상태인 경우 트리거를 발생시킵니다.
    """
    entries = _load_jsonl(thought_history_path, max_lines=20)
    if len(entries) < threshold_consecutive_neutral:
        return None

    consecutive_stalls = 0
    for entry in reversed(entries):
        score = entry.get("state", {}).get("score", 0)
        resonance_summary = entry.get("resonance", {}).get("summary", "")
        
        # 50점 근처이거나 알 수 없는 메모리 상태인 경우 정체로 간주
        if (48 <= score <= 52) or ("Unknown Memory" in resonance_summary) or ("Void" in resonance_summary):
            consecutive_stalls += 1
        else:
            break

    if consecutive_stalls >= threshold_consecutive_neutral:
        return TriggerEvent(
            type=TriggerType.MIMESIS_STALL,
            score=min(consecutive_stalls / 10.0, 1.0),
            reason=f"리듬 정체 감지: {consecutive_stalls}회 연속 중립 상태 (미메시스적 도약 필요)",
            payload={"consecutive_stalls": consecutive_stalls}
        )

    return None


def compute_self_trigger(
    config: Dict[str, Any],
) -> Optional[TriggerEvent]:
    """
    모든 트리거 후보를 계산하고,
    score가 가장 높은 TriggerEvent를 선택하여 반환합니다.
    
    config 예시:
    {
        "paths": {
            "resonance_ledger": "memory/resonance_ledger.jsonl",
            "learning_log": "memory/learning_log.jsonl",
            "learned_patterns": "memory/learned_patterns.json",
            "digital_twin_state": "memory/digital_twin_state.json",
            "recent_observations": "memory/recent_obs.jsonl",
            "outputs": "outputs",
        },
        "thresholds": {
            "unresolved_pattern": 0.6,
            "boredom_idle_seconds": 1800,
            "curiosity_conflict": 0.5,
            "model_drift": 0.7,
            "emotional_resonance": 0.6,
            "acoustic_anomaly": 0.75,
        }
    }
    """
    paths = config.get("paths", {})
    thresholds = config.get("thresholds", {})
    
    # 🧬 Rhythm-Aware Adjustment
    workspace_root = Path(__file__).parent.parent
    boundary_manager = RhythmBoundaryManager(workspace_root)
    rhythm_state = boundary_manager.get_rhythm_state()
    
    # 리듬에 따른 동적 임계값 적용
    adjusted_thresholds = {
        "unresolved_pattern": boundary_manager.adjust_threshold("unresolved_pattern", thresholds.get("unresolved_pattern", 0.6), rhythm_state),
        "boredom_idle_seconds": boundary_manager.adjust_threshold("boredom_idle_seconds", thresholds.get("boredom_idle_seconds", 1800), rhythm_state),
        "curiosity_conflict": boundary_manager.adjust_threshold("curiosity_conflict", thresholds.get("curiosity_conflict", 0.5), rhythm_state),
        "model_drift": boundary_manager.adjust_threshold("model_drift", thresholds.get("model_drift", 0.7), rhythm_state),
        "emotional_resonance": boundary_manager.adjust_threshold("emotional_resonance", thresholds.get("emotional_resonance", 0.6), rhythm_state),
        "acoustic_anomaly": boundary_manager.adjust_threshold("acoustic_anomaly", thresholds.get("acoustic_anomaly", 0.75), rhythm_state),
    }
    
    # 로깅 (필요 시)
    # print(f"🌊 Rhythm Adjusted Thresholds: {adjusted_thresholds} (Phase: {rhythm_state['phase']})")
    
    # 기본 경로 설정
    base_dir = Path(__file__).parent.parent / "memory"
    
    resonance_path = paths.get("resonance_ledger", str(base_dir / "resonance_ledger.jsonl"))
    learning_log_path = paths.get("learning_log", str(base_dir / "learning_log.jsonl"))
    patterns_path = paths.get("learned_patterns", str(base_dir / "learned_patterns.json"))
    twin_path = paths.get("digital_twin_state")
    obs_path = paths.get("recent_observations")
    
    # 모든 트리거 계산
    triggers: List[TriggerEvent] = []
    
    # 1. 미해결 패턴 트리거
    unresolved_trigger = compute_unresolved_pattern_trigger(
        resonance_path,
        threshold=adjusted_thresholds["unresolved_pattern"]
    )
    if unresolved_trigger:
        triggers.append(unresolved_trigger)
    
    # 2. 지루함 트리거
    boredom_trigger = compute_boredom_trigger(
        learning_log_path,
        min_idle_seconds=adjusted_thresholds["boredom_idle_seconds"]
    )
    if boredom_trigger:
        triggers.append(boredom_trigger)
    
    # 3. 호기심 충돌 트리거
    conflict_trigger = compute_curiosity_conflict_trigger(
        patterns_path,
        threshold=adjusted_thresholds["curiosity_conflict"]
    )
    if conflict_trigger:
        triggers.append(conflict_trigger)
    
    # 4. 모델 드리프트 트리거
    drift_trigger = compute_model_drift_trigger(
        twin_path,
        obs_path,
        threshold=adjusted_thresholds["model_drift"]
    )
    if drift_trigger:
        triggers.append(drift_trigger)
    
    # 5. 감정 공명 트리거
    emotion_trigger = compute_emotional_resonance_trigger(
        resonance_path,
        threshold=adjusted_thresholds["emotional_resonance"]
    )
    if emotion_trigger:
        triggers.append(emotion_trigger)
    
    # 6. 소리 이상 트리거
    acoustic_trigger = compute_acoustic_anomaly_trigger(
        paths.get("outputs", "outputs"),
        threshold=adjusted_thresholds["acoustic_anomaly"]
    )
    if acoustic_trigger:
        triggers.append(acoustic_trigger)
    
    # 7. 미메시스 정체 트리거
    thought_history = paths.get("thought_history", str(base_dir.parent / "outputs" / "thought_stream_history.jsonl"))
    stall_trigger = compute_mimesis_stall_trigger(thought_history)
    if stall_trigger:
        triggers.append(stall_trigger)
    
    # 가장 높은 점수의 트리거 반환
    if not triggers:
        return None
    
    return max(triggers, key=lambda t: t.score)


# 편의를 위한 기본 설정
def get_default_trigger_config() -> Dict[str, Any]:
    """기본 트리거 설정 반환"""
    base_dir = Path(__file__).parent.parent / "memory"
    
    return {
        "paths": {
            "resonance_ledger": str(base_dir / "resonance_ledger.jsonl"),
            "learning_log": str(base_dir / "learning_log.jsonl"),
            "learned_patterns": str(base_dir / "learned_patterns.json"),
            "digital_twin_state": str(base_dir / "digital_twin_state.json"),
            "recent_observations": str(base_dir / "recent_obs.jsonl"),
        },
        "thresholds": {
            "unresolved_pattern": 0.6,
            "boredom_idle_seconds": 1800,  # 30분
            "curiosity_conflict": 0.5,
            "model_drift": 0.7,
            "emotional_resonance": 0.6,
            "acoustic_anomaly": 0.75,
        }
    }


if __name__ == "__main__":
    # 테스트 실행
    config = get_default_trigger_config()
    trigger = compute_self_trigger(config)
    
    if trigger:
        print(f"🎯 Self-Trigger 감지!")
        print(f"   Type: {trigger.type.value}")
        print(f"   Score: {trigger.score:.2f}")
        print(f"   Reason: {trigger.reason}")
    else:
        print("😴 트리거 없음 - 시스템이 안정 상태")


def generate_triggers_from_state(state: Dict[str, float]) -> List[TriggerEvent]:
    """
    AGI 내부 상태(의식/무의식/배경자아 등)를 기반으로
    트리거를 자동 생성합니다.
    
    이 함수는 heartbeat 루프에서 호출되어
    AGI가 "심심함/호기심/갈등"을 스스로 느끼게 합니다.
    
    Args:
        state: AGI 내부 상태 딕셔너리
            - consciousness: 의식 레벨 (0.0~1.0)
            - unconscious: 무의식 레벨
            - background_self: 배경자아 레벨
            - boredom: 지루함 레벨
            - curiosity: 호기심 레벨
            - energy: 에너지 레벨
    
    Returns:
        생성된 트리거 리스트
    """
    triggers: List[TriggerEvent] = []
    
    boredom = state.get("boredom", 0.0)
    curiosity = state.get("curiosity", 0.0)
    energy = state.get("energy", 1.0)
    consciousness = state.get("consciousness", 0.5)
    unconscious = state.get("unconscious", 0.5)
    
    # 1) 지루함 트리거 (BOREDOM)
    # boredom이 0.5 이상이고 energy가 충분하면
    if boredom > 0.5 and energy > 0.3:
        triggers.append(TriggerEvent(
            type=TriggerType.BOREDOM,
            score=min(1.0, boredom + 0.1),
            reason=f"지루함 레벨 {boredom:.2f} - 새로운 자극이 필요함",
            payload={"source": "state_based", "boredom": boredom, "energy": energy}
        ))
    
    # 2) 호기심 갈등 트리거 (CURIOSITY_CONFLICT)
    # curiosity가 높거나 의식-무의식 차이가 크면
    consciousness_diff = abs(consciousness - unconscious)
    if curiosity > 0.6 or consciousness_diff > 0.3:
        conflict_score = max(curiosity * 0.7, consciousness_diff * 0.8)
        triggers.append(TriggerEvent(
            type=TriggerType.CURIOSITY_CONFLICT,
            score=min(1.0, conflict_score),
            reason=f"호기심 {curiosity:.2f}, 의식-무의식 차이 {consciousness_diff:.2f}",
            payload={"source": "state_based", "curiosity": curiosity, "diff": consciousness_diff}
        ))
    
    # 3) Soft Curiosity 트리거 (약한 탐색 욕구)
    # 강한 트리거가 없고, 약간 지루하고, 피곤하지 않을 때
    if not triggers and 0.2 < boredom <= 0.5 and energy > 0.5:
        triggers.append(TriggerEvent(
            type=TriggerType.BOREDOM,  # Soft exploration도 BOREDOM 타입 사용
            score=0.4 + boredom * 0.3,
            reason=f"조용한 지루함 - 가벼운 탐색 시도",
            payload={"source": "soft_curiosity", "mode": "light_exploration"}
        ))
    
    # 4) 존재적 정체 트리거 (MIMESIS_STALL - 상태 기반)
    if not triggers and boredom < 0.2 and abs(consciousness - unconscious) < 0.1 and energy > 0.6:
        triggers.append(TriggerEvent(
            type=TriggerType.MIMESIS_STALL,
            score=0.5,
            reason="내적 변화가 극도로 적은 정체 상태 감지",
            payload={"source": "state_based_stall"}
        ))

    return triggers


def detect_trigger(state: Dict[str, float]) -> Optional[TriggerEvent]:
    """
    AGI 상태에서 가장 점수가 높은 트리거 하나를 반환합니다.
    
    Heartbeat 루프에서 사용됩니다.
    """
    triggers = generate_triggers_from_state(state)
    
    if not triggers:
        return None
    
    return max(triggers, key=lambda t: t.score)

