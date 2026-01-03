"""
Resonance Simulator - Autopoietic Energy Dynamics

원본: C:\\workspace\\original_data\\core_flow_sim.py
목적: 7일 위상 루프 기반 공명/에너지/엔트로피 동역학 시뮬레이션
통합: 실시간 메트릭 입력 → 시뮬레이션 → 예측/피드백

핵심 개념:
- info_density: 정보 밀도 (공명과 엔트로피의 균형)
- resonance: 공명도 (sin 함수 기반, 위상과 연동)
- entropy: 엔트로피 (무질서도, 공명과 반비례)
- temporal_phase: 시간 위상 (7일 주기)
- horizon_crossing: 임계점 초과 시 위상 반전

Exit Code:
  0 = Success
  1 = Failure
"""
import sys
import logging
import math
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path


# 7일 주기 위상 정의 (원본에서 추출)
WEEKLY_PHASES = [
    {
        "day": "Monday",
        "axis": "Who",
        "emotion": "Love",
        "alpha": 1.25,
        "beta": 0.64,
        "coherence": 1.10,
        "tempo_shift": 0.18,
    },
    {
        "day": "Tuesday",
        "axis": "What",
        "emotion": "Respect",
        "alpha": 1.18,
        "beta": 0.66,
        "coherence": 1.05,
        "tempo_shift": 0.12,
    },
    {
        "day": "Wednesday",
        "axis": "Why",
        "emotion": "Understanding",
        "alpha": 1.22,
        "beta": 0.63,
        "coherence": 1.20,
        "tempo_shift": 0.15,
    },
    {
        "day": "Thursday",
        "axis": "Where",
        "emotion": "Responsibility",
        "alpha": 1.28,
        "beta": 0.68,
        "coherence": 1.08,
        "tempo_shift": 0.10,
    },
    {
        "day": "Friday",
        "axis": "How",
        "emotion": "Forgiveness",
        "alpha": 1.15,
        "beta": 0.60,
        "coherence": 0.98,
        "tempo_shift": 0.20,
    },
    {
        "day": "Saturday",
        "axis": "When",
        "emotion": "Compassion",
        "alpha": 1.12,
        "beta": 0.58,
        "coherence": 0.92,
        "tempo_shift": 0.22,
    },
    {
        "day": "Sunday",
        "axis": "Integration",
        "emotion": "Peace",
        "alpha": 1.20,
        "beta": 0.62,
        "coherence": 1.00,
        "tempo_shift": 0.25,
    },
]


EMOTION_GAINS = {
    "Love": 0.15,
    "Respect": 0.12,
    "Understanding": 0.16,
    "Responsibility": 0.18,
    "Forgiveness": 0.11,
    "Compassion": 0.14,
    "Peace": 0.13,
}


@dataclass
class ResonanceState:
    """공명 시스템 상태"""
    info_density: float = 0.25  # 정보 밀도
    resonance: float = 0.42  # 공명도
    entropy: float = 0.55  # 엔트로피
    logical_coherence: float = 0.52  # 논리적 일관성
    ethical_alignment: float = 0.58  # 윤리적 정렬
    temporal_phase: float = 0.0  # 시간 위상
    meta_bias: float = 0.0  # 메타 편향
    horizon_crossings: int = 0  # 지평선 교차 횟수
    history: List[Dict[str, float]] = field(default_factory=list)

    def step(
        self,
        phase: Dict[str, object],
        t: int,
        noise: float = 0.02
    ) -> Dict[str, float]:
        """
        1 스텝 시뮬레이션 (원본 로직 보존)
        
        Args:
            phase: 현재 위상 (WEEKLY_PHASES 중 하나)
            t: 시간 스텝
            noise: 노이즈 강도 (기본 0.02로 감소)
        
        Returns:
            현재 스텝의 메트릭 딕셔너리
        """
        # 감정 게인 가져오기
        emotion = str(phase["emotion"])
        emotion_gain = EMOTION_GAINS.get(emotion, 0.10)
        
        # 동역학 파라미터
        alpha = float(phase["alpha"]) + emotion_gain * 0.35
        beta = float(phase["beta"]) - emotion_gain * 0.15
        
        # 정보 밀도 업데이트 (공명 - 엔트로피 균형)
        dI = alpha * self.resonance - beta * self.entropy
        self.info_density += dI
        
        # 메타 편향 업데이트
        self.meta_bias += 0.05 * (emotion_gain - self.meta_bias)
        
        # 시간 위상 진행
        tempo_shift = float(phase["tempo_shift"])
        self.temporal_phase += tempo_shift * (1.0 + self.meta_bias)
        
        # 논리적 일관성 (사인 기반)
        coherence = float(phase["coherence"])
        coherence_drive = self.info_density * coherence + self.meta_bias
        self.logical_coherence = 0.5 * (1.0 + math.sin(coherence_drive))
        self.logical_coherence = max(0.1, min(0.9, self.logical_coherence))
        
        # 공명도 업데이트 (위상과 정보 밀도 연동)
        self.resonance = abs(math.sin(self.info_density + self.temporal_phase))
        
        # 엔트로피 업데이트 (공명과 반비례)
        entropy_target = 1.0 - self.resonance * self.logical_coherence
        self.entropy += 0.25 * (entropy_target - self.entropy)
        self.entropy = max(0.05, min(0.95, self.entropy))
        
        # 윤리적 정렬 업데이트
        self.ethical_alignment += 0.20 * (emotion_gain - self.ethical_alignment)
        self.ethical_alignment = max(0.05, min(0.95, self.ethical_alignment))
        
        # 지평선 교차 체크 (임계점 초과 시 위상 반전)
        threshold = 1.00 + 0.18 * (0.7 - self.ethical_alignment)
        horizon_flag = 0.0
        
        if self.info_density > threshold:
            self.info_density *= -0.55  # 위상 반전
            self.horizon_crossings += 1
            horizon_flag = 1.0
        
        # 정보 밀도 클램핑
        self.info_density = max(-1.5, min(1.8, self.info_density))
        
        # 기록
        record = {
            "t": float(t),
            "day": phase["day"],
            "info_density": self.info_density,
            "resonance": self.resonance,
            "entropy": self.entropy,
            "coherence": self.logical_coherence,
            "ethics": self.ethical_alignment,
            "phase": self.temporal_phase,
            "threshold": threshold,
            "horizon_crossing": horizon_flag,
        }
        self.history.append(record)
        return record

    def get_current_metrics(self) -> Dict[str, float]:
        """현재 상태 메트릭 반환"""
        return {
            "info_density": self.info_density,
            "resonance": self.resonance,
            "entropy": self.entropy,
            "coherence": self.logical_coherence,
            "ethics": self.ethical_alignment,
            "phase": self.temporal_phase,
            "horizon_crossings": self.horizon_crossings,
        }


class ResonanceSimulator:
    """
    Resonance Simulator (공명 시뮬레이터)
    
    7일 주기 위상 루프를 기반으로 정보 밀도/공명/엔트로피 동역학 시뮬레이션.
    원본 core_flow_sim.py의 핵심 로직을 추출하여 현재 AGI 시스템에 통합.
    """

    def __init__(self):
        """시뮬레이터 초기화"""
        self.state = ResonanceState()
        self.logger = logging.getLogger("ResonanceSimulator")
        self.logger.info("Simulator initialized")

    def run_simulation(
        self,
        cycles: int = 2,
        steps_per_phase: int = 24
    ) -> List[Dict[str, float]]:
        """
        시뮬레이션 실행
        
        Args:
            cycles: 주기 횟수 (1 주기 = 7일)
            steps_per_phase: 각 위상당 스텝 수 (24 = 1시간 단위)
        
        Returns:
            전체 히스토리 (리스트)
        """
        total_steps = cycles * len(WEEKLY_PHASES) * steps_per_phase
        self.logger.info(f"Running simulation: {cycles} cycles, {total_steps} steps")
        
        for step in range(total_steps):
            phase_index = (step // steps_per_phase) % len(WEEKLY_PHASES)
            phase = WEEKLY_PHASES[phase_index]
            self.state.step(phase, step)
        
        self.logger.info(f"Simulation complete: {len(self.state.history)} records")
        return self.state.history

    def get_phase_summary(self) -> Dict[str, Dict[str, float]]:
        """위상별 평균 메트릭 요약"""
        if not self.state.history:
            return {}
        
        summary = {}
        for phase in WEEKLY_PHASES:
            day = phase["day"]
            records = [r for r in self.state.history if r["day"] == day]
            
            if not records:
                continue
            
            summary[day] = {
                "info_density": sum(r["info_density"] for r in records) / len(records),
                "resonance": sum(r["resonance"] for r in records) / len(records),
                "entropy": sum(r["entropy"] for r in records) / len(records),
                "coherence": sum(r["coherence"] for r in records) / len(records),
                "horizon_crossings": sum(r["horizon_crossing"] for r in records),
            }
        
        return summary

    def export_results(self, output_path: str):
        """결과 내보내기 (JSON)"""
        data = {
            "final_state": self.state.get_current_metrics(),
            "phase_summary": self.get_phase_summary(),
            "history_count": len(self.state.history),
            "horizon_crossings": self.state.horizon_crossings,
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Results exported: {output_path}")


# ============================================================================
# CLI 인터페이스
# ============================================================================

def demo_simulator():
    """데모: 2주기 시뮬레이션 및 요약"""
    print("=" * 70)
    print("Resonance Simulator Demo (7-Day Phase Loop)")
    print("=" * 70)
    
    # 시뮬레이터 초기화
    simulator = ResonanceSimulator()
    
    print("\n[Info] Running 2-cycle simulation (14 days)...")
    print("-" * 70)
    
    # 시뮬레이션 실행
    history = simulator.run_simulation(cycles=2, steps_per_phase=24)
    
    print(f"\n[Result] Generated {len(history)} data points")
    
    # 위상별 요약
    summary = simulator.get_phase_summary()
    
    print("\n[Phase Summary] Average metrics by day:")
    print("-" * 70)
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
        if day not in summary:
            continue
        s = summary[day]
        print(f"{day:12s}: Info={s['info_density']:6.3f}, Resonance={s['resonance']:5.3f}, "
              f"Entropy={s['entropy']:5.3f}, Crossings={int(s['horizon_crossings'])}")
    
    # 최종 상태
    final = simulator.state.get_current_metrics()
    print("\n[Final State]")
    print("-" * 70)
    print(f"Info Density:  {final['info_density']:6.3f}")
    print(f"Resonance:     {final['resonance']:6.3f}")
    print(f"Entropy:       {final['entropy']:6.3f}")
    print(f"Coherence:     {final['coherence']:6.3f}")
    print(f"Ethics:        {final['ethics']:6.3f}")
    print(f"Phase:         {final['phase']:6.3f}")
    print(f"Crossings:     {final['horizon_crossings']}")
    
    # 결과 내보내기
    output_path = "outputs/resonance_simulation_latest.json"
    simulator.export_results(output_path)
    print(f"\n[Export] {output_path}")
    
    print("\n" + "=" * 70)
    print("PASS: Resonance simulator demo completed successfully")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        exit_code = demo_simulator()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\nFAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
