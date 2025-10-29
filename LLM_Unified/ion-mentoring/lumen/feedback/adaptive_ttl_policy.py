"""
Adaptive TTL Policy

캐시 히트율 기반 TTL 자동 조정 정책

Lumen v1.7 Adaptive Signal:
- 히트율에 따라 TTL 동적 조정
- 비용 효율성 최적화
- 안전 가드레일 (min 60s, max 3600s)

감응 → 증빙 → 적응:
1. 감응: 캐시 히트율, 메모리 사용률, 비용 추세 모니터링
2. 증빙: TTL 조정 필요성 분석, 예상 효과 계산
3. 적응: TTL 자동 조정, 점진적 적용
"""

from typing import Dict, Optional, Tuple
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import json
import os

logger = logging.getLogger(__name__)


class TTLAdjustmentStrategy(Enum):
    """TTL 조정 전략"""
    AGGRESSIVE = "AGGRESSIVE"      # 공격적 (빠른 증가/감소)
    MODERATE = "MODERATE"          # 보통 (점진적 조정)
    CONSERVATIVE = "CONSERVATIVE"  # 보수적 (느린 조정)


@dataclass
class TTLPolicy:
    """TTL 정책 설정"""
    min_ttl_seconds: int = 60          # 최소 TTL (1분)
    max_ttl_seconds: int = 3600        # 최대 TTL (1시간)
    default_ttl_seconds: int = 300     # 기본 TTL (5분)
    
    # 히트율 임계값
    target_hit_rate: float = 80.0      # 목표 히트율 (%)
    min_hit_rate: float = 60.0         # 최소 허용 히트율 (%)
    
    # 조정 단계
    aggressive_step: int = 300         # 공격적 단계 (5분)
    moderate_step: int = 120           # 보통 단계 (2분)
    conservative_step: int = 60        # 보수적 단계 (1분)
    
    # 메모리 임계값
    memory_pressure_threshold: float = 85.0  # 메모리 압박 임계값 (%)
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TTLAdjustment:
    """TTL 조정 결과"""
    current_ttl: int
    recommended_ttl: int
    adjustment_reason: str
    strategy: TTLAdjustmentStrategy
    expected_hit_rate_change: float    # 예상 히트율 변화 (%)
    expected_cost_impact: float        # 예상 비용 영향 (%)
    confidence_score: float            # 신뢰도 (0-1)
    
    def to_dict(self) -> dict:
        return {
            "current_ttl": self.current_ttl,
            "recommended_ttl": self.recommended_ttl,
            "adjustment_reason": self.adjustment_reason,
            "strategy": self.strategy.value,
            "expected_hit_rate_change": round(self.expected_hit_rate_change, 2),
            "expected_cost_impact": round(self.expected_cost_impact, 2),
            "confidence_score": round(self.confidence_score, 2)
        }


class AdaptiveTTLPolicy:
    """적응형 TTL 정책 엔진"""
    
    def __init__(self, policy: Optional[TTLPolicy] = None):
        """
        Args:
            policy: TTL 정책 설정 (None이면 기본값 사용)
        """
        self.policy = policy or TTLPolicy()
        
        # 상태 파일 경로
        self.state_file = os.path.join(
            os.path.dirname(__file__),
            "../outputs/ttl_policy_state.json"
        )
        
        # TTL 히스토리 (최근 10개 조정)
        self.ttl_history: list = self._load_ttl_history()
    
    def _load_ttl_history(self) -> list:
        """TTL 히스토리 로드"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    return state.get("ttl_history", [])
        except Exception as e:
            logger.warning(f"Failed to load TTL history: {e}")
        
        return []
    
    def _save_ttl_history(self, adjustment: TTLAdjustment):
        """TTL 히스토리 저장"""
        try:
            import datetime
            
            entry = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "adjustment": adjustment.to_dict()
            }
            
            # 최근 10개만 유지
            self.ttl_history.append(entry)
            if len(self.ttl_history) > 10:
                self.ttl_history = self.ttl_history[-10:]
            
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            
            state = {
                "ttl_history": self.ttl_history,
                "current_ttl": adjustment.recommended_ttl
            }
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved TTL history to {self.state_file}")
        
        except Exception as e:
            logger.error(f"Failed to save TTL history: {e}")
    
    def calculate_ttl_adjustment(
        self,
        current_ttl: int,
        hit_rate: float,
        memory_usage_pct: float,
        eviction_count: int,
        cost_trend: str = "STABLE"  # RISING, STABLE, FALLING
    ) -> TTLAdjustment:
        """
        TTL 조정 계산
        
        Args:
            current_ttl: 현재 TTL (초)
            hit_rate: 캐시 히트율 (%)
            memory_usage_pct: 메모리 사용률 (%)
            eviction_count: 제거된 키 수
            cost_trend: 비용 추세
        
        Returns:
            TTLAdjustment: TTL 조정 결과
        """
        logger.info(f"Calculating TTL adjustment: current={current_ttl}s, hit_rate={hit_rate:.2f}%, "
                   f"memory={memory_usage_pct:.2f}%, evictions={eviction_count}, cost={cost_trend}")
        
        # 1. 조정 전략 결정
        strategy = self._determine_strategy(hit_rate, memory_usage_pct, cost_trend)
        
        # 2. TTL 조정 계산
        recommended_ttl, reason = self._calculate_new_ttl(
            current_ttl, hit_rate, memory_usage_pct, eviction_count, cost_trend, strategy
        )
        
        # 3. 예상 효과 계산
        expected_hit_rate_change = self._estimate_hit_rate_change(current_ttl, recommended_ttl, hit_rate)
        expected_cost_impact = self._estimate_cost_impact(current_ttl, recommended_ttl, hit_rate)
        
        # 4. 신뢰도 계산
        confidence = self._calculate_confidence(hit_rate, memory_usage_pct, eviction_count)
        
        adjustment = TTLAdjustment(
            current_ttl=current_ttl,
            recommended_ttl=recommended_ttl,
            adjustment_reason=reason,
            strategy=strategy,
            expected_hit_rate_change=expected_hit_rate_change,
            expected_cost_impact=expected_cost_impact,
            confidence_score=confidence
        )
        
        # 히스토리 저장
        self._save_ttl_history(adjustment)
        
        return adjustment
    
    def _determine_strategy(
        self, 
        hit_rate: float, 
        memory_usage_pct: float,
        cost_trend: str
    ) -> TTLAdjustmentStrategy:
        """조정 전략 결정"""
        # Case 1: 히트율 매우 낮음 + 비용 상승 → AGGRESSIVE
        if hit_rate < self.policy.min_hit_rate and cost_trend == "RISING":
            return TTLAdjustmentStrategy.AGGRESSIVE
        
        # Case 2: 메모리 압박 + 제거 많음 → AGGRESSIVE
        if memory_usage_pct > self.policy.memory_pressure_threshold:
            return TTLAdjustmentStrategy.AGGRESSIVE
        
        # Case 3: 히트율 적정, 안정적 → CONSERVATIVE
        if hit_rate >= self.policy.target_hit_rate and cost_trend == "STABLE":
            return TTLAdjustmentStrategy.CONSERVATIVE
        
        # Default: MODERATE
        return TTLAdjustmentStrategy.MODERATE
    
    def _calculate_new_ttl(
        self,
        current_ttl: int,
        hit_rate: float,
        memory_usage_pct: float,
        eviction_count: int,
        cost_trend: str,
        strategy: TTLAdjustmentStrategy
    ) -> Tuple[int, str]:
        """
        새로운 TTL 계산
        
        Returns:
            (new_ttl, reason)
        """
        # 조정 단계 결정
        if strategy == TTLAdjustmentStrategy.AGGRESSIVE:
            step = self.policy.aggressive_step
        elif strategy == TTLAdjustmentStrategy.MODERATE:
            step = self.policy.moderate_step
        else:
            step = self.policy.conservative_step
        
        # Case 1: 히트율 낮음 → TTL 증가
        if hit_rate < self.policy.min_hit_rate:
            new_ttl = min(current_ttl + step, self.policy.max_ttl_seconds)
            reason = (f"히트율({hit_rate:.1f}%) 낮음. TTL {current_ttl}s → {new_ttl}s로 증가하여 "
                     f"캐싱 효과 향상 ({strategy.value} 전략)")
            return new_ttl, reason
        
        # Case 2: 히트율 목표 이상 + 메모리 압박 → TTL 감소
        if hit_rate >= self.policy.target_hit_rate and memory_usage_pct > self.policy.memory_pressure_threshold:
            new_ttl = max(current_ttl - step, self.policy.min_ttl_seconds)
            reason = (f"히트율({hit_rate:.1f}%) 양호하나 메모리 압박({memory_usage_pct:.1f}%). "
                     f"TTL {current_ttl}s → {new_ttl}s로 감소하여 메모리 확보 ({strategy.value} 전략)")
            return new_ttl, reason
        
        # Case 3: 많은 제거 발생 → TTL 감소
        if eviction_count > 100:
            new_ttl = max(current_ttl - step // 2, self.policy.min_ttl_seconds)
            reason = (f"많은 키 제거({eviction_count}개). TTL {current_ttl}s → {new_ttl}s로 감소하여 "
                     f"메모리 압박 완화 ({strategy.value} 전략)")
            return new_ttl, reason
        
        # Case 4: 비용 상승 + 히트율 개선 여지 → TTL 증가
        if cost_trend == "RISING" and hit_rate < self.policy.target_hit_rate:
            new_ttl = min(current_ttl + step, self.policy.max_ttl_seconds)
            reason = (f"비용 상승 추세 + 히트율({hit_rate:.1f}%) 개선 가능. "
                     f"TTL {current_ttl}s → {new_ttl}s로 증가하여 API 호출 감소 ({strategy.value} 전략)")
            return new_ttl, reason
        
        # Case 5: 비용 하락 + 히트율 높음 → TTL 미세 감소 (데이터 신선도)
        if cost_trend == "FALLING" and hit_rate >= self.policy.target_hit_rate:
            new_ttl = max(current_ttl - step // 3, self.policy.min_ttl_seconds)
            if new_ttl < current_ttl:
                reason = (f"비용 안정화 + 높은 히트율({hit_rate:.1f}%). "
                         f"TTL {current_ttl}s → {new_ttl}s로 미세 감소하여 데이터 신선도 향상 ({strategy.value} 전략)")
                return new_ttl, reason
        
        # Case 6: 히트율 중간 범위 + 안정적 → 점진적 증가
        if self.policy.min_hit_rate <= hit_rate < self.policy.target_hit_rate and cost_trend == "STABLE":
            new_ttl = min(current_ttl + step // 2, self.policy.max_ttl_seconds)
            reason = (f"히트율({hit_rate:.1f}%) 개선 여지 있음. TTL {current_ttl}s → {new_ttl}s로 점진적 증가 "
                     f"({strategy.value} 전략)")
            return new_ttl, reason
        
        # Default: 유지
        reason = (f"현재 TTL({current_ttl}s) 유지. 히트율({hit_rate:.1f}%), 메모리({memory_usage_pct:.1f}%), "
                 f"비용 추세({cost_trend})")
        return current_ttl, reason
    
    def _estimate_hit_rate_change(self, current_ttl: int, new_ttl: int, current_hit_rate: float) -> float:
        """
        예상 히트율 변화 계산
        
        간단한 모델:
        - TTL 2배 → 히트율 +10-15%
        - TTL 1/2 → 히트율 -5-10%
        """
        if new_ttl == current_ttl:
            return 0.0
        
        ttl_ratio = new_ttl / current_ttl
        
        if ttl_ratio > 1.0:
            # TTL 증가 → 히트율 증가 (단, 상한 있음)
            # 로그 스케일: 2배 = +12%, 3배 = +18%, 4배 = +22%
            import math
            max_gain = 25.0  # 최대 25% 증가
            estimated_gain = max_gain * (1 - math.exp(-0.8 * (ttl_ratio - 1)))
            
            # 현재 히트율이 높으면 개선 여지 작음
            diminishing_factor = (100 - current_hit_rate) / 100
            return estimated_gain * diminishing_factor
        
        else:
            # TTL 감소 → 히트율 감소
            # 1/2 = -7%, 1/3 = -12%, 1/4 = -15%
            import math
            max_loss = 20.0
            estimated_loss = max_loss * (1 - ttl_ratio)
            return -estimated_loss
    
    def _estimate_cost_impact(self, current_ttl: int, new_ttl: int, current_hit_rate: float) -> float:
        """
        예상 비용 영향 계산 (%)
        
        비용 = 캐시 비용 + API 호출 비용
        - 히트율 증가 → API 호출 감소 → 비용 절감
        - 히트율 감소 → API 호출 증가 → 비용 증가
        """
        hit_rate_change = self._estimate_hit_rate_change(current_ttl, new_ttl, current_hit_rate)
        
        if hit_rate_change == 0:
            return 0.0
        
        # 가정: API 호출 비용이 캐시 비용보다 10배 높음
        # 히트율 1% 증가 → API 호출 1% 감소 → 총 비용 ~0.9% 감소
        api_cost_weight = 0.9
        cost_impact = -hit_rate_change * api_cost_weight
        
        return cost_impact
    
    def _calculate_confidence(self, hit_rate: float, memory_usage_pct: float, eviction_count: int) -> float:
        """
        조정 신뢰도 계산 (0-1)
        
        높은 신뢰도:
        - 히트율이 극단적 (매우 낮음 or 매우 높음)
        - 메모리 압박 명확
        - 제거 패턴 명확
        """
        confidence = 0.5  # 기본 신뢰도
        
        # 히트율이 극단적이면 신뢰도 증가
        if hit_rate < 40 or hit_rate > 90:
            confidence += 0.2
        elif 40 <= hit_rate < 50 or 85 <= hit_rate < 90:
            confidence += 0.1
        
        # 메모리 압박 명확하면 신뢰도 증가
        if memory_usage_pct > 90:
            confidence += 0.2
        elif memory_usage_pct > 80:
            confidence += 0.1
        
        # 제거 많으면 신뢰도 증가
        if eviction_count > 500:
            confidence += 0.2
        elif eviction_count > 100:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def apply_ttl_adjustment(self, adjustment: TTLAdjustment) -> bool:
        """
        TTL 조정 적용 (실제 적용은 Redis 클라이언트에서)
        
        Args:
            adjustment: TTL 조정 결과
        
        Returns:
            bool: 적용 성공 여부
        """
        if adjustment.current_ttl == adjustment.recommended_ttl:
            logger.info("No TTL adjustment needed")
            return True
        
        logger.info(f"Applying TTL adjustment: {adjustment.current_ttl}s → {adjustment.recommended_ttl}s")
        logger.info(f"Reason: {adjustment.adjustment_reason}")
        logger.info(f"Expected hit rate change: {adjustment.expected_hit_rate_change:+.2f}%")
        logger.info(f"Expected cost impact: {adjustment.expected_cost_impact:+.2f}%")
        
        # TODO: 실제 Redis TTL 업데이트
        # redis_client.config_set("default-ttl", adjustment.recommended_ttl)
        
        return True
    
    def get_ttl_recommendation_summary(self, adjustment: TTLAdjustment) -> str:
        """TTL 조정 요약 생성"""
        if adjustment.current_ttl == adjustment.recommended_ttl:
            return f"✅ 현재 TTL({adjustment.current_ttl}s) 유지 권장"
        
        direction = "증가" if adjustment.recommended_ttl > adjustment.current_ttl else "감소"
        
        summary = f"""
## TTL 조정 권장

**현재 TTL**: {adjustment.current_ttl}초  
**권장 TTL**: {adjustment.recommended_ttl}초 ({direction})  
**전략**: {adjustment.strategy.value}

**조정 이유**:
{adjustment.adjustment_reason}

**예상 효과**:
- 히트율 변화: {adjustment.expected_hit_rate_change:+.2f}%
- 비용 영향: {adjustment.expected_cost_impact:+.2f}%
- 신뢰도: {adjustment.confidence_score * 100:.1f}%
"""
        
        return summary


if __name__ == "__main__":
    # Logging 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 테스트 시나리오
    policy = AdaptiveTTLPolicy()
    
    print("\n" + "=" * 60)
    print("Scenario 1: 히트율 낮음 (40%), 비용 상승")
    print("=" * 60)
    adjustment1 = policy.calculate_ttl_adjustment(
        current_ttl=300,
        hit_rate=40.0,
        memory_usage_pct=60.0,
        eviction_count=10,
        cost_trend="RISING"
    )
    print(policy.get_ttl_recommendation_summary(adjustment1))
    
    print("\n" + "=" * 60)
    print("Scenario 2: 히트율 높음 (85%), 메모리 압박")
    print("=" * 60)
    adjustment2 = policy.calculate_ttl_adjustment(
        current_ttl=600,
        hit_rate=85.0,
        memory_usage_pct=92.0,
        eviction_count=250,
        cost_trend="STABLE"
    )
    print(policy.get_ttl_recommendation_summary(adjustment2))
    
    print("\n" + "=" * 60)
    print("Scenario 3: 히트율 적정 (75%), 안정적")
    print("=" * 60)
    adjustment3 = policy.calculate_ttl_adjustment(
        current_ttl=300,
        hit_rate=75.0,
        memory_usage_pct=65.0,
        eviction_count=5,
        cost_trend="STABLE"
    )
    print(policy.get_ttl_recommendation_summary(adjustment3))
    
    print("\n" + "=" * 60)
    print("Scenario 4: 히트율 매우 낮음 (25%), 긴급 상황")
    print("=" * 60)
    adjustment4 = policy.calculate_ttl_adjustment(
        current_ttl=180,
        hit_rate=25.0,
        memory_usage_pct=50.0,
        eviction_count=0,
        cost_trend="RISING"
    )
    print(policy.get_ttl_recommendation_summary(adjustment4))
