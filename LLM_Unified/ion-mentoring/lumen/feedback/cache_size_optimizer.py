"""
Cache Size Optimizer

L1 캐시 크기 동적 조정 및 메모리 최적화

Lumen v1.7 Resonance Memory:
- 메모리 사용 패턴 분석
- 최적 캐시 크기 계산
- 비용 vs 성능 트레이드오프

감응 → 증빙 → 적응:
1. 감응: 메모리 사용률, 제거 패턴, 히트율 모니터링
2. 증빙: 최적 크기 계산, ROI 분석
3. 적응: 캐시 크기 자동 조정
"""

from typing import Dict, Optional, Tuple, List
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import json
import os
import math

logger = logging.getLogger(__name__)


class CacheSizeStrategy(Enum):
    """캐시 크기 조정 전략"""
    SCALE_UP = "SCALE_UP"          # 크기 증가
    SCALE_DOWN = "SCALE_DOWN"      # 크기 감소
    MAINTAIN = "MAINTAIN"          # 현재 유지
    OPTIMIZE = "OPTIMIZE"          # 최적화 (작은 조정)


@dataclass
class CacheSizeConfig:
    """캐시 크기 설정"""
    min_size_mb: float = 10.0          # 최소 크기 (10MB)
    max_size_mb: float = 1024.0        # 최대 크기 (1GB)
    default_size_mb: float = 256.0     # 기본 크기 (256MB)
    
    # 메모리 임계값
    low_memory_threshold: float = 50.0      # 낮은 사용률 (%)
    optimal_memory_range: Tuple[float, float] = (70.0, 85.0)  # 최적 범위
    high_memory_threshold: float = 90.0     # 높은 사용률 (%)
    
    # 조정 단계
    scale_up_factor: float = 1.5           # 증가 배수
    scale_down_factor: float = 0.75        # 감소 배수
    optimize_step_mb: float = 32.0         # 미세 조정 단계
    
    # 비용 설정 (MB당 월간 비용)
    cost_per_mb_per_month: float = 0.0365  # $9.36 / 256MB ≈ $0.0365/MB
    
    def to_dict(self) -> dict:
        result = asdict(self)
        result['optimal_memory_range'] = list(self.optimal_memory_range)
        return result


@dataclass
class CacheSizeAdjustment:
    """캐시 크기 조정 결과"""
    current_size_mb: float
    recommended_size_mb: float
    strategy: CacheSizeStrategy
    adjustment_reason: str
    expected_memory_usage_pct: float       # 예상 메모리 사용률
    expected_hit_rate_change: float        # 예상 히트율 변화 (%)
    expected_monthly_cost_usd: float       # 예상 월간 비용 (USD)
    cost_change_usd: float                 # 비용 변화 (USD)
    roi_score: float                       # ROI 점수 (0-10)
    confidence_score: float                # 신뢰도 (0-1)
    
    def to_dict(self) -> dict:
        return {
            "current_size_mb": round(self.current_size_mb, 2),
            "recommended_size_mb": round(self.recommended_size_mb, 2),
            "strategy": self.strategy.value,
            "adjustment_reason": self.adjustment_reason,
            "expected_memory_usage_pct": round(self.expected_memory_usage_pct, 2),
            "expected_hit_rate_change": round(self.expected_hit_rate_change, 2),
            "expected_monthly_cost_usd": round(self.expected_monthly_cost_usd, 2),
            "cost_change_usd": round(self.cost_change_usd, 2),
            "roi_score": round(self.roi_score, 2),
            "confidence_score": round(self.confidence_score, 2)
        }


class CacheSizeOptimizer:
    """캐시 크기 최적화 엔진"""
    
    def __init__(self, config: Optional[CacheSizeConfig] = None):
        """
        Args:
            config: 캐시 크기 설정 (None이면 기본값)
        """
        self.config = config or CacheSizeConfig()
        
        # 상태 파일
        self.state_file = os.path.join(
            os.path.dirname(__file__),
            "../outputs/cache_size_state.json"
        )
        
        # 크기 조정 히스토리
        self.size_history: list = self._load_size_history()
    
    def _load_size_history(self) -> list:
        """크기 조정 히스토리 로드"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    return state.get("size_history", [])
        except Exception as e:
            logger.warning(f"Failed to load size history: {e}")
        
        return []
    
    def _save_size_history(self, adjustment: CacheSizeAdjustment):
        """크기 조정 히스토리 저장"""
        try:
            import datetime
            
            entry = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "adjustment": adjustment.to_dict()
            }
            
            # 최근 20개만 유지
            self.size_history.append(entry)
            if len(self.size_history) > 20:
                self.size_history = self.size_history[-20:]
            
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            
            state = {
                "size_history": self.size_history,
                "current_size_mb": adjustment.recommended_size_mb
            }
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved size history to {self.state_file}")
        
        except Exception as e:
            logger.error(f"Failed to save size history: {e}")
    
    def calculate_optimal_size(
        self,
        current_size_mb: float,
        memory_usage_pct: float,
        hit_rate: float,
        eviction_count: int,
        eviction_rate_per_hour: float,
        request_rate_per_second: float = 10.0
    ) -> CacheSizeAdjustment:
        """
        최적 캐시 크기 계산
        
        Args:
            current_size_mb: 현재 캐시 크기 (MB)
            memory_usage_pct: 메모리 사용률 (%)
            hit_rate: 캐시 히트율 (%)
            eviction_count: 제거된 키 수
            eviction_rate_per_hour: 시간당 제거율 (keys/hour)
            request_rate_per_second: 초당 요청 수
        
        Returns:
            CacheSizeAdjustment: 크기 조정 결과
        """
        logger.info(f"Calculating optimal cache size: current={current_size_mb}MB, "
                   f"memory={memory_usage_pct:.2f}%, hit_rate={hit_rate:.2f}%, "
                   f"evictions={eviction_count}, eviction_rate={eviction_rate_per_hour:.2f}/h")
        
        # 1. 전략 결정
        strategy = self._determine_size_strategy(
            memory_usage_pct, hit_rate, eviction_count, eviction_rate_per_hour
        )
        
        # 2. 최적 크기 계산
        recommended_size, reason = self._calculate_new_size(
            current_size_mb, memory_usage_pct, hit_rate, eviction_count, 
            eviction_rate_per_hour, strategy
        )
        
        # 3. 예상 메모리 사용률 계산
        expected_memory_usage = self._estimate_memory_usage(
            current_size_mb, recommended_size, memory_usage_pct
        )
        
        # 4. 예상 히트율 변화 계산
        expected_hit_rate_change = self._estimate_hit_rate_change(
            current_size_mb, recommended_size, hit_rate, eviction_rate_per_hour
        )
        
        # 5. 비용 계산
        current_cost = current_size_mb * self.config.cost_per_mb_per_month
        new_cost = recommended_size * self.config.cost_per_mb_per_month
        cost_change = new_cost - current_cost
        
        # 6. ROI 점수 계산
        roi_score = self._calculate_roi_score(
            cost_change, expected_hit_rate_change, request_rate_per_second
        )
        
        # 7. 신뢰도 계산
        confidence = self._calculate_confidence(
            memory_usage_pct, eviction_count, hit_rate
        )
        
        adjustment = CacheSizeAdjustment(
            current_size_mb=current_size_mb,
            recommended_size_mb=recommended_size,
            strategy=strategy,
            adjustment_reason=reason,
            expected_memory_usage_pct=expected_memory_usage,
            expected_hit_rate_change=expected_hit_rate_change,
            expected_monthly_cost_usd=new_cost,
            cost_change_usd=cost_change,
            roi_score=roi_score,
            confidence_score=confidence
        )
        
        # 히스토리 저장
        self._save_size_history(adjustment)
        
        return adjustment
    
    def _determine_size_strategy(
        self,
        memory_usage_pct: float,
        hit_rate: float,
        eviction_count: int,
        eviction_rate_per_hour: float
    ) -> CacheSizeStrategy:
        """크기 조정 전략 결정"""
        optimal_min, optimal_max = self.config.optimal_memory_range
        
        # Case 1: 메모리 압박 심함 → SCALE_UP
        if memory_usage_pct > self.config.high_memory_threshold:
            return CacheSizeStrategy.SCALE_UP
        
        # Case 2: 많은 제거 발생 → SCALE_UP
        if eviction_rate_per_hour > 100:
            return CacheSizeStrategy.SCALE_UP
        
        # Case 3: 메모리 사용률 낮음 + 히트율 낮음 → SCALE_DOWN
        if memory_usage_pct < self.config.low_memory_threshold and hit_rate < 60:
            return CacheSizeStrategy.SCALE_DOWN
        
        # Case 4: 최적 범위 → MAINTAIN or OPTIMIZE
        if optimal_min <= memory_usage_pct <= optimal_max:
            if hit_rate >= 80:
                return CacheSizeStrategy.MAINTAIN
            else:
                return CacheSizeStrategy.OPTIMIZE
        
        # Case 5: 메모리 약간 높음 → OPTIMIZE
        if optimal_max < memory_usage_pct < self.config.high_memory_threshold:
            return CacheSizeStrategy.OPTIMIZE
        
        return CacheSizeStrategy.MAINTAIN
    
    def _calculate_new_size(
        self,
        current_size: float,
        memory_usage_pct: float,
        hit_rate: float,
        eviction_count: int,
        eviction_rate_per_hour: float,
        strategy: CacheSizeStrategy
    ) -> Tuple[float, str]:
        """
        새로운 캐시 크기 계산
        
        Returns:
            (new_size_mb, reason)
        """
        if strategy == CacheSizeStrategy.SCALE_UP:
            # 증가: 1.5배
            new_size = min(current_size * self.config.scale_up_factor, self.config.max_size_mb)
            reason = (f"메모리 압박({memory_usage_pct:.1f}%) 또는 높은 제거율({eviction_rate_per_hour:.1f}/h). "
                     f"캐시 크기 {current_size:.0f}MB → {new_size:.0f}MB로 증가하여 "
                     f"히트율 향상 및 API 호출 감소.")
            return new_size, reason
        
        elif strategy == CacheSizeStrategy.SCALE_DOWN:
            # 감소: 0.75배
            new_size = max(current_size * self.config.scale_down_factor, self.config.min_size_mb)
            reason = (f"낮은 메모리 사용률({memory_usage_pct:.1f}%) + 낮은 히트율({hit_rate:.1f}%). "
                     f"캐시 크기 {current_size:.0f}MB → {new_size:.0f}MB로 감소하여 "
                     f"비용 절감 (${(current_size - new_size) * self.config.cost_per_mb_per_month:.2f}/월).")
            return new_size, reason
        
        elif strategy == CacheSizeStrategy.OPTIMIZE:
            # 미세 조정: ±32MB
            if memory_usage_pct > 80:
                new_size = min(current_size + self.config.optimize_step_mb, self.config.max_size_mb)
                reason = (f"메모리 사용률({memory_usage_pct:.1f}%) 높음. "
                         f"캐시 크기 {current_size:.0f}MB → {new_size:.0f}MB로 미세 증가.")
            elif memory_usage_pct < 60 and eviction_count < 10:
                new_size = max(current_size - self.config.optimize_step_mb, self.config.min_size_mb)
                reason = (f"메모리 여유({memory_usage_pct:.1f}%) + 적은 제거({eviction_count}). "
                         f"캐시 크기 {current_size:.0f}MB → {new_size:.0f}MB로 미세 감소.")
            else:
                new_size = current_size
                reason = f"최적 범위 내. 캐시 크기 {current_size:.0f}MB 유지."
            return new_size, reason
        
        else:  # MAINTAIN
            reason = (f"현재 설정 최적. 메모리: {memory_usage_pct:.1f}%, 히트율: {hit_rate:.1f}%, "
                     f"캐시 크기: {current_size:.0f}MB 유지.")
            return current_size, reason
    
    def _estimate_memory_usage(
        self, 
        current_size: float, 
        new_size: float, 
        current_usage_pct: float
    ) -> float:
        """예상 메모리 사용률 계산"""
        if new_size == current_size:
            return current_usage_pct
        
        # 사용 중인 메모리 (MB)
        used_mb = current_size * (current_usage_pct / 100)
        
        # 새로운 크기에서의 사용률
        new_usage_pct = (used_mb / new_size) * 100
        
        return min(new_usage_pct, 100.0)
    
    def _estimate_hit_rate_change(
        self,
        current_size: float,
        new_size: float,
        current_hit_rate: float,
        eviction_rate: float
    ) -> float:
        """
        예상 히트율 변화 계산
        
        모델:
        - 크기 증가 → 제거 감소 → 히트율 증가
        - 크기 감소 → 제거 증가 → 히트율 감소
        """
        if new_size == current_size:
            return 0.0
        
        size_ratio = new_size / current_size
        
        if size_ratio > 1.0:
            # 크기 증가 → 히트율 증가
            # 제거가 많을수록 개선 효과 큼
            eviction_factor = min(eviction_rate / 100, 1.0)
            max_gain = 15.0  # 최대 15% 증가
            
            # 로그 스케일: 1.5배 = +8%, 2배 = +12%
            estimated_gain = max_gain * (1 - math.exp(-1.2 * (size_ratio - 1))) * (0.5 + 0.5 * eviction_factor)
            
            # 현재 히트율이 높으면 개선 여지 작음
            diminishing_factor = (100 - current_hit_rate) / 100
            return estimated_gain * diminishing_factor
        
        else:
            # 크기 감소 → 히트율 감소
            # 0.75배 = -5%, 0.5배 = -10%
            max_loss = 12.0
            estimated_loss = max_loss * (1 - size_ratio)
            
            # 현재 제거가 적으면 영향 작음
            eviction_factor = max(1.0 - eviction_rate / 100, 0.3)
            return -estimated_loss * eviction_factor
    
    def _calculate_roi_score(
        self,
        cost_change: float,
        hit_rate_change: float,
        request_rate: float
    ) -> float:
        """
        ROI 점수 계산 (0-10)
        
        ROI = (히트율 향상으로 인한 API 비용 절감) / (캐시 비용 증가)
        
        가정:
        - API 호출당 비용: $0.01 (Vertex AI)
        - 월간 요청 수: request_rate * 86400 * 30
        """
        if cost_change == 0:
            return 5.0  # 중립
        
        # API 호출당 비용
        api_cost_per_call = 0.01
        
        # 월간 요청 수
        requests_per_month = request_rate * 86400 * 30
        
        # 히트율 변화로 인한 API 호출 변화
        api_call_change = requests_per_month * (hit_rate_change / 100)
        
        # API 비용 절감
        api_cost_savings = api_call_change * api_cost_per_call
        
        # ROI = 절감 / 비용 증가
        if cost_change > 0:
            # 비용 증가 → ROI가 양수여야 좋음
            roi = api_cost_savings / cost_change
            
            # ROI → 0-10 점수로 변환
            # ROI > 5 → 10점, ROI = 2 → 7점, ROI = 1 → 5점, ROI < 0.5 → 2점
            if roi >= 5:
                score = 10.0
            elif roi >= 2:
                score = 5.0 + (roi - 2) * (5.0 / 3)
            elif roi >= 1:
                score = 5.0 + (roi - 1) * 2.0
            elif roi >= 0.5:
                score = 2.0 + (roi - 0.5) * 6.0
            else:
                score = max(roi * 4, 0)
            
            return min(score, 10.0)
        
        else:
            # 비용 감소 → 대부분 긍정적
            # 단, 히트율이 크게 떨어지면 감점
            if hit_rate_change < -10:
                return 4.0  # 히트율 대폭 감소
            elif hit_rate_change < -5:
                return 6.0
            else:
                return 8.0  # 비용 절감 + 히트율 유지
    
    def _calculate_confidence(
        self, 
        memory_usage_pct: float, 
        eviction_count: int,
        hit_rate: float
    ) -> float:
        """신뢰도 계산 (0-1)"""
        confidence = 0.5
        
        # 메모리 사용률이 극단적이면 신뢰도 증가
        if memory_usage_pct > 85 or memory_usage_pct < 55:
            confidence += 0.2
        elif memory_usage_pct > 80 or memory_usage_pct < 60:
            confidence += 0.1
        
        # 제거 패턴 명확하면 신뢰도 증가
        if eviction_count > 200:
            confidence += 0.2
        elif eviction_count > 50:
            confidence += 0.1
        
        # 히트율이 극단적이면 신뢰도 증가
        if hit_rate < 50 or hit_rate > 90:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def get_size_recommendation_summary(self, adjustment: CacheSizeAdjustment) -> str:
        """크기 조정 요약 생성"""
        if adjustment.current_size_mb == adjustment.recommended_size_mb:
            return f"✅ 현재 캐시 크기({adjustment.current_size_mb:.0f}MB) 유지 권장"
        
        direction = "증가" if adjustment.recommended_size_mb > adjustment.current_size_mb else "감소"
        
        summary = f"""
## 캐시 크기 조정 권장

**현재 크기**: {adjustment.current_size_mb:.0f}MB  
**권장 크기**: {adjustment.recommended_size_mb:.0f}MB ({direction})  
**전략**: {adjustment.strategy.value}

**조정 이유**:
{adjustment.adjustment_reason}

**예상 효과**:
- 메모리 사용률: {adjustment.expected_memory_usage_pct:.2f}%
- 히트율 변화: {adjustment.expected_hit_rate_change:+.2f}%
- 월간 비용: ${adjustment.expected_monthly_cost_usd:.2f} ({adjustment.cost_change_usd:+.2f} USD/월)
- ROI 점수: {adjustment.roi_score:.1f}/10
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
    optimizer = CacheSizeOptimizer()
    
    print("\n" + "=" * 60)
    print("Scenario 1: 메모리 압박 (92%), 높은 제거율")
    print("=" * 60)
    adjustment1 = optimizer.calculate_optimal_size(
        current_size_mb=256.0,
        memory_usage_pct=92.0,
        hit_rate=75.0,
        eviction_count=350,
        eviction_rate_per_hour=150.0,
        request_rate_per_second=10.0
    )
    print(optimizer.get_size_recommendation_summary(adjustment1))
    
    print("\n" + "=" * 60)
    print("Scenario 2: 낮은 메모리 사용 (45%), 낮은 히트율 (50%)")
    print("=" * 60)
    adjustment2 = optimizer.calculate_optimal_size(
        current_size_mb=512.0,
        memory_usage_pct=45.0,
        hit_rate=50.0,
        eviction_count=5,
        eviction_rate_per_hour=2.0,
        request_rate_per_second=10.0
    )
    print(optimizer.get_size_recommendation_summary(adjustment2))
    
    print("\n" + "=" * 60)
    print("Scenario 3: 최적 범위 (75%), 높은 히트율 (85%)")
    print("=" * 60)
    adjustment3 = optimizer.calculate_optimal_size(
        current_size_mb=256.0,
        memory_usage_pct=75.0,
        hit_rate=85.0,
        eviction_count=10,
        eviction_rate_per_hour=5.0,
        request_rate_per_second=10.0
    )
    print(optimizer.get_size_recommendation_summary(adjustment3))
    
    print("\n" + "=" * 60)
    print("Scenario 4: 약간 높은 메모리 (82%), 보통 히트율 (70%)")
    print("=" * 60)
    adjustment4 = optimizer.calculate_optimal_size(
        current_size_mb=256.0,
        memory_usage_pct=82.0,
        hit_rate=70.0,
        eviction_count=45,
        eviction_rate_per_hour=20.0,
        request_rate_per_second=10.0
    )
    print(optimizer.get_size_recommendation_summary(adjustment4))
