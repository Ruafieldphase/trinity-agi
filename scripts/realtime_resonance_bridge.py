"""
Realtime Resonance Bridge - Ledger to Resonance Integration

목적: Resonance Ledger 메트릭 → Resonance Simulator 실시간 연동
흐름: JSONL 읽기 → 메트릭 추출 → ResonanceState 초기화 → 시뮬레이션

핵심 기능:
1. Ledger 메트릭 추출 (confidence, quality, duration 등)
2. ResonanceState 초기화 (info_density, resonance, entropy)
3. 실시간 스텝 시뮬레이션
4. 예측 결과 피드백 루프

Exit Code:
  0 = Success
  1 = Failure
"""
import sys
import logging
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from workspace_root import get_workspace_root

# Resonance Simulator 임포트
sys.path.insert(0, str(Path(__file__).parent))
from resonance_simulator import (
    ResonanceState,
    WEEKLY_PHASES,
)

# 상수
HORIZON_THRESHOLD = 1.42  # 지평선 임계값 (원본과 동일)


@dataclass
class LedgerMetrics:
    """Ledger에서 추출한 메트릭"""
    timestamp: float
    task_id: str
    confidence: Optional[float] = None
    quality: Optional[float] = None
    duration_sec: Optional[float] = None
    ok: Optional[bool] = None
    error: Optional[str] = None
    event: str = "unknown"


@dataclass
class ResonancePrediction:
    """공명 예측 결과"""
    timestamp: float
    current_phase: Dict
    predicted_resonance: float
    predicted_entropy: float
    horizon_warning: bool
    recommended_action: str


class RealtimeResonanceBridge:
    """실시간 Ledger → Resonance 브리지"""
    
    def __init__(
        self,
        ledger_path: Path,
        window_hours: int = 24,
        min_events: int = 10,
    ):
        self.ledger_path = ledger_path
        self.window_hours = window_hours
        self.min_events = min_events
        self.logger = self._setup_logger()
        
        # Resonance 상태 초기화
        self.resonance_state = self._init_resonance_state()
        self.current_step = 0  # 스텝 카운터
        
    def _setup_logger(self) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger("ResonanceBridge")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[%(levelname)s] %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _init_resonance_state(self) -> ResonanceState:
        """초기 Resonance 상태 생성"""
        return ResonanceState(
            info_density=1.0,
            resonance=0.5,
            entropy=0.3,
            logical_coherence=0.5,
            ethical_alignment=0.6,
            temporal_phase=0.0,
        )
    
    def load_recent_events(self) -> List[LedgerMetrics]:
        """최근 이벤트 로드 (시간 윈도우 내)"""
        if not self.ledger_path.exists():
            self.logger.warning(f"Ledger not found: {self.ledger_path}")
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=self.window_hours)
        cutoff_ts = cutoff_time.timestamp()
        
        events = []
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    ts = data.get("ts", 0)
                    
                    # ts를 float로 변환
                    if isinstance(ts, str):
                        try:
                            ts = float(ts)
                        except ValueError:
                            continue
                    
                    if ts < cutoff_ts:
                        continue
                    
                    # 메트릭 추출
                    metric = LedgerMetrics(
                        timestamp=ts,
                        task_id=data.get("task_id", "unknown"),
                        confidence=data.get("confidence"),
                        quality=data.get("quality"),
                        duration_sec=data.get("duration_sec"),
                        ok=data.get("ok"),
                        error=data.get("error"),
                        event=data.get("event", "unknown"),
                    )
                    events.append(metric)
                
                except json.JSONDecodeError:
                    continue
        
        self.logger.info(
            f"Loaded {len(events)} events from last {self.window_hours}h"
        )
        return events
    
    def extract_resonance_inputs(
        self, events: List[LedgerMetrics]
    ) -> Dict[str, float]:
        """이벤트에서 Resonance 입력 추출"""
        if not events:
            return {
                "avg_confidence": 0.5,
                "avg_quality": 0.5,
                "success_rate": 0.5,
                "avg_duration": 1.0,
            }
        
        # 메트릭 집계
        confidences = [e.confidence for e in events if e.confidence is not None]
        qualities = [e.quality for e in events if e.quality is not None]
        successes = [e.ok for e in events if e.ok is not None]
        durations = [e.duration_sec for e in events if e.duration_sec is not None]
        
        return {
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.5,
            "avg_quality": sum(qualities) / len(qualities) if qualities else 0.5,
            "success_rate": sum(successes) / len(successes) if successes else 0.5,
            "avg_duration": sum(durations) / len(durations) if durations else 1.0,
        }
    
    def update_resonance_state(self, inputs: Dict[str, float]) -> None:
        """입력 메트릭 기반 Resonance 상태 업데이트"""
        # info_density: confidence와 quality의 조화 평균
        conf = inputs["avg_confidence"]
        qual = inputs["avg_quality"]
        if conf + qual > 0:
            self.resonance_state.info_density = 2 * conf * qual / (conf + qual)
        else:
            self.resonance_state.info_density = 0.5
        
        # resonance: success_rate 기반
        self.resonance_state.resonance = inputs["success_rate"]
        
        # entropy: duration의 역수 (빠를수록 낮은 엔트로피)
        duration = inputs["avg_duration"]
        self.resonance_state.entropy = min(1.0, duration / 5.0)
        
        self.logger.info(
            f"Updated state: "
            f"info_density={self.resonance_state.info_density:.3f}, "
            f"resonance={self.resonance_state.resonance:.3f}, "
            f"entropy={self.resonance_state.entropy:.3f}"
        )
    
    def step_simulation(self) -> Tuple[ResonanceState, Dict, bool]:
        """1 스텝 시뮬레이션 실행 (ResonanceState.step 활용)"""
        # 현재 요일 기반 위상 선택
        today = datetime.now().weekday()  # 0=Monday
        phase = WEEKLY_PHASES[today % 7]
        
        # ResonanceState의 step 메서드 호출
        metrics = self.resonance_state.step(
            phase=phase,
            t=self.current_step,
            noise=0.02
        )
        
        # 지평선 교차 체크
        horizon_crossed = (
            self.resonance_state.info_density > HORIZON_THRESHOLD
        )
        
        if horizon_crossed:
            self.resonance_state.horizon_crossings += 1
            self.logger.warning(
                f"Horizon crossing #{self.resonance_state.horizon_crossings}"
            )
        
        self.current_step += 1
        
        return self.resonance_state, metrics, horizon_crossed
    
    def generate_prediction(
        self, current_phase: Dict, metrics: Dict, horizon_crossed: bool
    ) -> ResonancePrediction:
        """예측 결과 생성"""
        # 다음 스텝 예측 (현재 메트릭 기반)
        predicted_resonance = metrics.get("resonance", self.resonance_state.resonance)
        predicted_entropy = metrics.get("entropy", self.resonance_state.entropy)
        
        # 권장 액션
        if horizon_crossed:
            action = "Phase transition detected. Reduce workload."
        elif self.resonance_state.resonance > 0.8:
            action = "High resonance. Continue current approach."
        elif self.resonance_state.resonance < 0.3:
            action = "Low resonance. Review strategy."
        else:
            action = "Normal operation. Monitor metrics."
        
        return ResonancePrediction(
            timestamp=datetime.now().timestamp(),
            current_phase=current_phase,
            predicted_resonance=predicted_resonance,
            predicted_entropy=predicted_entropy,
            horizon_warning=horizon_crossed,
            recommended_action=action,
        )
    
    def run(self, output_path: Optional[Path] = None) -> Dict:
        """전체 파이프라인 실행"""
        self.logger.info("=== Realtime Resonance Bridge ===")
        
        # 1. Ledger 이벤트 로드
        events = self.load_recent_events()
        
        if len(events) < self.min_events:
            self.logger.warning(
                f"Insufficient events: {len(events)} < {self.min_events}"
            )
            return {
                "status": "insufficient_data",
                "events_count": len(events),
                "min_required": self.min_events,
            }
        
        # 2. 메트릭 추출
        inputs = self.extract_resonance_inputs(events)
        self.logger.info(f"Extracted metrics: {inputs}")
        
        # 3. Resonance 상태 업데이트
        self.update_resonance_state(inputs)
        
        # 4. 시뮬레이션 스텝
        state, metrics, horizon_crossed = self.step_simulation()
        
        # 현재 위상 가져오기
        today = datetime.now().weekday()
        current_phase = WEEKLY_PHASES[today % 7]
        
        # 5. 예측 생성
        prediction = self.generate_prediction(current_phase, metrics, horizon_crossed)
        
        # 결과 조합
        result = {
            "status": "success",
            "window_hours": self.window_hours,
            "events_count": len(events),
            "metrics": inputs,
            "resonance_state": {
                "info_density": state.info_density,
                "resonance": state.resonance,
                "entropy": state.entropy,
                "temporal_phase": state.temporal_phase,
                "logical_coherence": state.logical_coherence,
                "ethical_alignment": state.ethical_alignment,
                "horizon_crossings": state.horizon_crossings,
                "current_step": self.current_step,
            },
            "prediction": {
                "timestamp": prediction.timestamp,
                "current_phase": prediction.current_phase,
                "predicted_resonance": prediction.predicted_resonance,
                "predicted_entropy": prediction.predicted_entropy,
                "horizon_warning": prediction.horizon_warning,
                "recommended_action": prediction.recommended_action,
            },
        }
        
        # 파일 저장
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved result: {output_path}")
        
        # 요약 출력
        self.logger.info("=== Summary ===")
        self.logger.info(f"Events: {len(events)}")
        self.logger.info(f"Avg Confidence: {inputs['avg_confidence']:.3f}")
        self.logger.info(f"Avg Quality: {inputs['avg_quality']:.3f}")
        self.logger.info(f"Success Rate: {inputs['success_rate']:.3f}")
        self.logger.info(f"Current Resonance: {state.resonance:.3f}")
        self.logger.info(f"Current Phase: {current_phase['day']}")
        self.logger.info(f"Predicted Resonance: {prediction.predicted_resonance:.3f}")
        self.logger.info(f"Recommended Action: {prediction.recommended_action}")
        
        if horizon_crossed:
            self.logger.warning("⚠️ HORIZON CROSSING DETECTED")
        
        return result


def main():
    """메인 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Realtime Resonance Bridge - Ledger to Resonance Integration"
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=get_workspace_root()
        / "fdo_agi_repo"
        / "memory"
        / "resonance_ledger.jsonl",
        help="Ledger JSONL path",
    )
    parser.add_argument(
        "--window-hours",
        type=int,
        default=24,
        help="Time window for event loading (hours)",
    )
    parser.add_argument(
        "--min-events",
        type=int,
        default=10,
        help="Minimum events required",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=get_workspace_root()
        / "outputs"
        / "realtime_resonance_latest.json",
        help="Output JSON path",
    )
    
    args = parser.parse_args()
    
    try:
        bridge = RealtimeResonanceBridge(
            ledger_path=args.ledger,
            window_hours=args.window_hours,
            min_events=args.min_events,
        )
        result = bridge.run(output_path=args.output)
        
        if result["status"] == "success":
            sys.exit(0)
        else:
            sys.exit(1)
    
    except Exception as e:
        logging.error(f"Bridge failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
