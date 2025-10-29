#!/usr/bin/env python3
"""
Cost Rhythm Loop - Lumen 철학 통합

Lumen v1.4~v1.7 설계 철학을 ION 시스템에 적용:
- v1.4: auto_remediation + approval_bridge (자동복구 + 승인 연계)
- v1.5: maturity index (성숙도 지표)
- v1.6: unified_gate (통합 게이트 = ROI × SLO × Maturity)
- v1.7: resonance memory bridge (감응 기억 브리지)

Phase 3: Cost Rhythm Loop
- Budget Resonance Mapper: 비용 리듬 감응
- Cost Adaptive Policy: 비용 적응 정책
- Rollback Approval Bridge: 롤백 승인 브리지
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# Lumen Exporters 임포트
from lumen.exporters.maturity_exporter_cloudrun import MaturityExporterCloudRun
from lumen.exporters.slo_exporter_cloudrun import SLOExporterCloudRun
from lumen.gates.roi_gate_cloudrun import ROIGateCloudRun

# GCP 설정
PROJECT_ID = os.getenv("GCP_PROJECT", "naeda-genesis")
SERVICE_NAME = os.getenv("SERVICE_NAME", "ion-api-canary")

# Cost Rhythm 임계값
MONTHLY_BUDGET_USD = 200.0
COST_RESONANCE_THRESHOLD = {
    "coherence": 0.7,  # 비용 일관성 (daily variance)
    "phase": 0.8,      # 비용 위상 (trend alignment)
    "entropy": 0.5,    # 비용 엔트로피 (predictability)
}


class RhythmStatus(Enum):
    """리듬 상태 (Lumen Resonance 개념)"""
    RESONANT = "RESONANT"      # 리듬 안정
    DISSONANT = "DISSONANT"    # 리듬 불안정
    CHAOTIC = "CHAOTIC"        # 리듬 혼란


class AdaptiveAction(Enum):
    """적응 행동 (Lumen Auto-Remediation 개념)"""
    NONE = "NONE"                    # 조치 불필요
    SCALE_DOWN = "SCALE_DOWN"        # 스케일 다운
    ROLLBACK = "ROLLBACK"            # 롤백
    EMERGENCY_STOP = "EMERGENCY_STOP"  # 긴급 중지


@dataclass
class CostRhythmState:
    """비용 리듬 상태"""
    timestamp: str
    current_spend: float
    daily_average: float
    forecasted_spend: float
    
    # Lumen Resonance 메트릭
    coherence: float  # 비용 일관성 (0-1)
    phase: float      # 비용 위상 (0-1)
    entropy: float    # 비용 엔트로피 (0-1)
    
    # 통합 게이트 점수 (Lumen Unified Gate)
    maturity_score: float
    roi_percentage: float
    slo_compliance: float
    
    # 리듬 판단
    rhythm_status: str
    adaptive_action: str
    requires_approval: bool
    confidence: float


class CostRhythmLoop:
    """
    Cost Rhythm Loop - Lumen 철학 통합
    
    감응(Resonance) → 증빙(Proof) → 적응(Feedback) 루프
    """
    
    def __init__(self, project_id: str, service_name: str):
        """
        Args:
            project_id: GCP 프로젝트 ID
            service_name: Cloud Run 서비스 이름
        """
        self.project_id = project_id
        self.service_name = service_name
        
        # Lumen Exporters 초기화
        self.maturity_exporter = MaturityExporterCloudRun(project_id, service_name)
        self.slo_exporter = SLOExporterCloudRun(project_id, service_name)
        self.roi_gate = ROIGateCloudRun(project_id, service_name)
        
        # 상태 저장 경로
        self.state_path = PROJECT_ROOT / "outputs" / "cost_rhythm_state.json"
        self.state_path.parent.mkdir(exist_ok=True)
    
    def _calculate_coherence(self, daily_costs: List[float]) -> float:
        """
        비용 일관성 계산 (Lumen Resonance: coherence)
        
        일일 비용 변동이 작을수록 coherence가 높음
        
        Args:
            daily_costs: 일일 비용 리스트
            
        Returns:
            coherence (0-1)
        """
        if len(daily_costs) < 2:
            return 1.0
        
        # 표준편차 기반 coherence
        import statistics
        mean_cost = statistics.mean(daily_costs)
        if mean_cost == 0:
            return 1.0
        
        stdev = statistics.stdev(daily_costs)
        coefficient_of_variation = stdev / mean_cost
        
        # CV가 0.2 이하면 coherence 1.0, 0.5 이상이면 0.0
        coherence = max(0, min(1, 1 - (coefficient_of_variation / 0.5)))
        
        return coherence
    
    def _calculate_phase(self, daily_costs: List[float]) -> float:
        """
        비용 위상 계산 (Lumen Resonance: phase)
        
        비용 추세가 예측 가능할수록 phase가 높음
        
        Args:
            daily_costs: 일일 비용 리스트
            
        Returns:
            phase (0-1)
        """
        if len(daily_costs) < 3:
            return 1.0
        
        # 선형 회귀 R² 기반 phase
        import numpy as np
        x = np.arange(len(daily_costs))
        y = np.array(daily_costs)
        
        # 선형 회귀
        coeffs = np.polyfit(x, y, 1)
        predicted = np.polyval(coeffs, x)
        
        # R² 계산
        ss_res = np.sum((y - predicted) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        
        if ss_tot == 0:
            return 1.0
        
        r_squared = 1 - (ss_res / ss_tot)
        phase = max(0, min(1, r_squared))
        
        return phase
    
    def _calculate_entropy(self, daily_costs: List[float]) -> float:
        """
        비용 엔트로피 계산 (Lumen Resonance: entropy)
        
        비용 패턴이 예측 가능할수록 entropy가 낮음
        
        Args:
            daily_costs: 일일 비용 리스트
            
        Returns:
            entropy (0-1, 낮을수록 좋음)
        """
        if len(daily_costs) < 2:
            return 0.0
        
        # 비용 변화율의 엔트로피
        import numpy as np
        
        changes = np.diff(daily_costs)
        
        # 변화율을 5개 구간으로 이산화
        if len(changes) == 0:
            return 0.0
        
        hist, _ = np.histogram(changes, bins=5)
        probabilities = hist / np.sum(hist)
        probabilities = probabilities[probabilities > 0]  # 0 제거
        
        # Shannon entropy
        entropy = -np.sum(probabilities * np.log2(probabilities))
        
        # 최대 엔트로피 (log2(5) ≈ 2.32)로 정규화
        normalized_entropy = entropy / 2.32
        
        return min(1.0, normalized_entropy)
    
    def get_daily_costs(self, days: int = 7) -> List[float]:
        """
        일일 비용 데이터 조회
        
        Args:
            days: 조회 일수
            
        Returns:
            일일 비용 리스트
        """
        # TODO: 실제 BigQuery 또는 Cloud Billing API 연동
        # 현재는 Redis + Cloud Run 추정치 반환
        
        redis_daily = 9.36 / 30  # Redis 월 비용 / 30일
        cloudrun_daily = 15.0 / 30  # Cloud Run 추정 월 비용 / 30일
        
        base_daily = redis_daily + cloudrun_daily
        
        # 임시: 약간의 변동성 추가
        import random
        random.seed(42)
        daily_costs = [base_daily * (1 + random.uniform(-0.1, 0.1)) for _ in range(days)]
        
        return daily_costs
    
    def calculate_rhythm_state(self) -> CostRhythmState:
        """
        현재 비용 리듬 상태 계산
        
        Returns:
            CostRhythmState 객체
        """
        # 1. 일일 비용 데이터 수집
        daily_costs = self.get_daily_costs(days=7)
        
        now = datetime.utcnow()
        current_spend = sum(daily_costs)
        daily_average = current_spend / len(daily_costs)
        
        # 월말 예측
        days_in_month = 30
        forecasted_spend = daily_average * days_in_month
        
        # 2. Resonance 메트릭 계산
        coherence = self._calculate_coherence(daily_costs)
        phase = self._calculate_phase(daily_costs)
        entropy = self._calculate_entropy(daily_costs)
        
        # 3. Unified Gate 점수 수집
        try:
            maturity_result = self.maturity_exporter.calculate_maturity_score()
            maturity_score = maturity_result['maturity_score']
        except Exception:
            maturity_score = 0.0
        
        try:
            roi_result = self.roi_gate.evaluate_gate()
            roi_percentage = roi_result['roi_percentage']
        except Exception:
            roi_percentage = 0.0
        
        try:
            slo_result = self.slo_exporter.evaluate_slo_status()
            slo_compliance = slo_result['compliance_rate']
        except Exception:
            slo_compliance = 0.0
        
        # 4. 리듬 상태 판단 (Lumen Resonance Logic)
        rhythm_status = self._evaluate_rhythm_status(coherence, phase, entropy)
        
        # 5. 적응 행동 결정 (Lumen Adaptive Policy)
        adaptive_action, requires_approval, confidence = self._decide_adaptive_action(
            rhythm_status,
            forecasted_spend,
            maturity_score,
            roi_percentage,
            slo_compliance,
        )
        
        # 6. 상태 객체 생성
        state = CostRhythmState(
            timestamp=now.isoformat(),
            current_spend=current_spend,
            daily_average=daily_average,
            forecasted_spend=forecasted_spend,
            coherence=coherence,
            phase=phase,
            entropy=entropy,
            maturity_score=maturity_score,
            roi_percentage=roi_percentage,
            slo_compliance=slo_compliance,
            rhythm_status=rhythm_status.value,
            adaptive_action=adaptive_action.value,
            requires_approval=requires_approval,
            confidence=confidence,
        )
        
        return state
    
    def _evaluate_rhythm_status(self, coherence: float, phase: float, entropy: float) -> RhythmStatus:
        """
        리듬 상태 평가 (Lumen Resonance Status)
        
        Args:
            coherence: 비용 일관성
            phase: 비용 위상
            entropy: 비용 엔트로피
            
        Returns:
            RhythmStatus
        """
        # 임계값 기반 상태 결정
        if (coherence >= COST_RESONANCE_THRESHOLD["coherence"] and
            phase >= COST_RESONANCE_THRESHOLD["phase"] and
            entropy <= COST_RESONANCE_THRESHOLD["entropy"]):
            return RhythmStatus.RESONANT
        elif (coherence < 0.5 or phase < 0.5 or entropy > 0.7):
            return RhythmStatus.CHAOTIC
        else:
            return RhythmStatus.DISSONANT
    
    def _decide_adaptive_action(
        self,
        rhythm_status: RhythmStatus,
        forecasted_spend: float,
        maturity_score: float,
        roi_percentage: float,
        slo_compliance: float,
    ) -> Tuple[AdaptiveAction, bool, float]:
        """
        적응 행동 결정 (Lumen Auto-Remediation Logic)
        
        Args:
            rhythm_status: 리듬 상태
            forecasted_spend: 예측 비용
            maturity_score: 성숙도 점수
            roi_percentage: ROI 퍼센트
            slo_compliance: SLO 준수율
            
        Returns:
            (AdaptiveAction, requires_approval, confidence)
        """
        # Unified Gate 종합 점수 (가중 평균)
        gate_score = (
            maturity_score * 0.3 +
            min(roi_percentage / 10, 100) * 0.3 +
            slo_compliance * 0.4
        )
        
        # 1. EMERGENCY_STOP: 예산 120% 초과 예상 + CHAOTIC 리듬
        if forecasted_spend > MONTHLY_BUDGET_USD * 1.2 and rhythm_status == RhythmStatus.CHAOTIC:
            return (AdaptiveAction.EMERGENCY_STOP, True, 0.95)
        
        # 2. ROLLBACK: 예산 110% 초과 예상 + Gate Score < 50
        if forecasted_spend > MONTHLY_BUDGET_USD * 1.1 and gate_score < 50:
            return (AdaptiveAction.ROLLBACK, True, 0.85)
        
        # 3. SCALE_DOWN: 예산 100% 초과 예상 + DISSONANT 리듬
        if forecasted_spend > MONTHLY_BUDGET_USD and rhythm_status == RhythmStatus.DISSONANT:
            return (AdaptiveAction.SCALE_DOWN, True, 0.75)
        
        # 4. NONE: 리듬 안정
        return (AdaptiveAction.NONE, False, 1.0)
    
    def save_state(self, state: CostRhythmState):
        """
        상태 저장 (Lumen Proof Ledger 개념)
        
        Args:
            state: CostRhythmState 객체
        """
        state_dict = asdict(state)
        
        with open(self.state_path, 'w', encoding='utf-8') as f:
            json.dump(state_dict, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 상태 저장 완료: {self.state_path}")
    
    def generate_report(self, state: CostRhythmState) -> str:
        """
        리듬 상태 리포트 생성 (Markdown)
        
        Args:
            state: CostRhythmState 객체
            
        Returns:
            Markdown 리포트
        """
        rhythm_icon = {
            "RESONANT": "🟢",
            "DISSONANT": "🟡",
            "CHAOTIC": "🔴",
        }[state.rhythm_status]
        
        action_icon = {
            "NONE": "✅",
            "SCALE_DOWN": "⚠️",
            "ROLLBACK": "🚨",
            "EMERGENCY_STOP": "❌",
        }[state.adaptive_action]
        
        report = f"""# Cost Rhythm Loop Report

**Generated**: {state.timestamp}

## Rhythm Status

{rhythm_icon} **Status**: {state.rhythm_status}

## Cost Metrics

| Metric | Value |
|--------|-------|
| Current Spend (7d) | ${state.current_spend:.2f} |
| Daily Average | ${state.daily_average:.2f}/day |
| Forecasted Monthly | ${state.forecasted_spend:.2f} |
| Budget | ${MONTHLY_BUDGET_USD:.2f} |

## Resonance Metrics (Lumen Philosophy)

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Coherence (일관성) | {state.coherence:.3f} | ≥ {COST_RESONANCE_THRESHOLD['coherence']} | {"✅" if state.coherence >= COST_RESONANCE_THRESHOLD['coherence'] else "❌"} |
| Phase (위상) | {state.phase:.3f} | ≥ {COST_RESONANCE_THRESHOLD['phase']} | {"✅" if state.phase >= COST_RESONANCE_THRESHOLD['phase'] else "❌"} |
| Entropy (엔트로피) | {state.entropy:.3f} | ≤ {COST_RESONANCE_THRESHOLD['entropy']} | {"✅" if state.entropy <= COST_RESONANCE_THRESHOLD['entropy'] else "❌"} |

## Unified Gate Score (Lumen v1.6)

| Gate | Value | Weight |
|------|-------|--------|
| Maturity Score | {state.maturity_score:.1f}/100 | 30% |
| ROI | {state.roi_percentage:.1f}% | 30% |
| SLO Compliance | {state.slo_compliance:.1f}% | 40% |

## Adaptive Action (Lumen Auto-Remediation)

{action_icon} **Action**: {state.adaptive_action}

- **Requires Approval**: {"Yes" if state.requires_approval else "No"}
- **Confidence**: {state.confidence:.0%}

## Recommendations

"""
        
        if state.adaptive_action == "NONE":
            report += "✅ Cost rhythm is stable. No action required.\n"
        elif state.adaptive_action == "SCALE_DOWN":
            report += f"""⚠️  **Scale Down Recommended**

**Reason**: Forecasted spend (${state.forecasted_spend:.2f}) exceeds budget + dissonant rhythm

**Actions**:
1. Reduce min_instances to 1
2. Optimize Redis cache TTL
3. Review expensive API calls
4. Monitor for 24 hours

**Approval Required**: Yes (5-minute window)
"""
        elif state.adaptive_action == "ROLLBACK":
            report += f"""🚨 **Rollback Recommended**

**Reason**: Forecasted spend (${state.forecasted_spend:.2f}) > 110% budget + low gate score

**Actions**:
1. Rollback to previous stable revision
2. Investigate cost spike cause
3. Disable non-critical features
4. Emergency cost review

**Approval Required**: Yes (immediate)
"""
        else:  # EMERGENCY_STOP
            report += f"""❌ **EMERGENCY STOP**

**Reason**: Forecasted spend (${state.forecasted_spend:.2f}) > 120% budget + chaotic rhythm

**Actions**:
1. **STOP all non-critical services immediately**
2. Activate incident response team
3. Rollback to last known good state
4. Full cost audit required

**Approval Required**: Yes (executive level)
"""
        
        return report


def main():
    """메인 실행 함수"""
    print("=" * 70)
    print("Cost Rhythm Loop - Lumen 철학 통합")
    print("=" * 70)
    print()
    
    # 1. Cost Rhythm Loop 초기화
    loop = CostRhythmLoop(PROJECT_ID, SERVICE_NAME)
    
    # 2. 리듬 상태 계산
    print("🔄 비용 리듬 상태 계산 중...")
    state = loop.calculate_rhythm_state()
    
    rhythm_icon = {
        "RESONANT": "🟢",
        "DISSONANT": "🟡",
        "CHAOTIC": "🔴",
    }[state.rhythm_status]
    
    print(f"\n{rhythm_icon} Rhythm Status: {state.rhythm_status}")
    print(f"💰 Forecasted: ${state.forecasted_spend:.2f} / ${MONTHLY_BUDGET_USD:.2f}")
    print(f"📊 Coherence: {state.coherence:.3f} | Phase: {state.phase:.3f} | Entropy: {state.entropy:.3f}")
    print(f"🎯 Action: {state.adaptive_action} (Confidence: {state.confidence:.0%})")
    print()
    
    # 3. 상태 저장
    loop.save_state(state)
    
    # 4. 리포트 생성
    print("=" * 70)
    print("Cost Rhythm Report")
    print("=" * 70)
    print()
    
    report = loop.generate_report(state)
    print(report)
    
    # 5. 리포트 파일 저장
    report_path = PROJECT_ROOT / "outputs" / f"cost_rhythm_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 리포트 저장: {report_path}")
    
    # 6. Exit code 결정
    exit_code = {
        "RESONANT": 0,
        "DISSONANT": 1,
        "CHAOTIC": 2,
    }[state.rhythm_status]
    
    print()
    print("=" * 70)
    print(f"Exit Code: {exit_code}")
    print("  0 = RESONANT (안정)")
    print("  1 = DISSONANT (불안정)")
    print("  2 = CHAOTIC (혼란)")
    print("=" * 70)
    
    return exit_code


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)
