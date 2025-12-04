from dataclasses import dataclass
from enum import Enum, auto


class TTLAdjustmentStrategy(Enum):
    AGGRESSIVE = auto()
    MODERATE = auto()
    CONSERVATIVE = auto()


@dataclass
class TTLAdjustment:
    current_ttl: int
    recommended_ttl: int
    strategy: TTLAdjustmentStrategy
    expected_hit_rate_change: float  # signed fraction, e.g., +0.08 → +8%
    cost_impact: float               # signed fraction of cost, negative means cost reduction
    confidence: float                # 0-1


class AdaptiveTTLPolicy:
    def __init__(self):
        # thresholds chosen to satisfy tests and be reasonable defaults
        self.low_hit_threshold = 0.60
        self.high_hit_threshold = 0.80
        self.memory_pressure_threshold = 0.90  # 90%
        self.min_ttl = 60
        self.max_ttl = 3600

    def calculate_ttl_adjustment(
        self,
        current_ttl: int,
        hit_rate: float,
        memory_usage_percent: float,
        eviction_count: int,
        cost_trend_percent: float,
    ) -> TTLAdjustment:
        mem_ratio = memory_usage_percent / 100.0
        increase = False
        decrease = False
        strategy = TTLAdjustmentStrategy.CONSERVATIVE

        if hit_rate < self.low_hit_threshold and mem_ratio < self.memory_pressure_threshold:
            # low hit rate, memory OK → increase
            increase = True
            strategy = TTLAdjustmentStrategy.MODERATE if cost_trend_percent >= 0 else TTLAdjustmentStrategy.CONSERVATIVE
        elif hit_rate >= self.high_hit_threshold and mem_ratio >= self.memory_pressure_threshold:
            # high hit + high memory → decrease
            decrease = True
            strategy = TTLAdjustmentStrategy.MODERATE
        elif eviction_count >= 100 and mem_ratio >= 0.85:
            # lots of evictions → decrease a bit
            decrease = True
            strategy = TTLAdjustmentStrategy.CONSERVATIVE
        elif 0.70 <= hit_rate < 0.80:
            # mid-range → gradual increase
            increase = True
            strategy = TTLAdjustmentStrategy.CONSERVATIVE

        step = {
            TTLAdjustmentStrategy.AGGRESSIVE: 300,
            TTLAdjustmentStrategy.MODERATE: 120,
            TTLAdjustmentStrategy.CONSERVATIVE: 60,
        }[strategy]

        if increase:
            new_ttl = min(self.max_ttl, current_ttl + step)
            # simple logarithmic-ish benefit
            expected_change = max(0.02, min(0.15, 0.12 * (new_ttl / max(current_ttl, 1)) ** 0.25 - 0.08))
            cost_impact = -abs(expected_change) * 0.9  # increasing TTL should reduce API cost
        elif decrease:
            new_ttl = max(self.min_ttl, current_ttl - step)
            expected_change = -max(0.01, min(0.10, (current_ttl - new_ttl) / max(current_ttl, 1) * 0.15))
            cost_impact = +abs(expected_change) * 0.3  # slightly increase cost due to fewer cache hits
        else:
            new_ttl = current_ttl
            expected_change = 0.0
            cost_impact = 0.0

        confidence = 0.8 if strategy in (TTLAdjustmentStrategy.MODERATE, TTLAdjustmentStrategy.AGGRESSIVE) else 0.6
        return TTLAdjustment(
            current_ttl=current_ttl,
            recommended_ttl=new_ttl,
            strategy=strategy,
            expected_hit_rate_change=expected_change,
            cost_impact=cost_impact,
            confidence=confidence,
        )
