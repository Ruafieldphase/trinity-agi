import math
from dataclasses import dataclass
from enum import Enum, auto


class CacheSizeStrategy(Enum):
    SCALE_UP = auto()
    SCALE_DOWN = auto()
    MAINTAIN = auto()
    OPTIMIZE = auto()


@dataclass
class CacheSizeAdjustment:
    current_size_mb: float
    recommended_size_mb: int
    strategy: CacheSizeStrategy
    expected_memory_usage: float  # 0-1 ratio
    expected_hit_rate_change: float  # signed fraction
    monthly_cost_delta: float  # USD
    roi_score: float  # 0-10
    confidence: float  # 0-1


class CacheSizeOptimizer:
    def __init__(self):
        self.min_size = 10
        self.max_size = 1024
        self.cost_per_mb_per_month = 0.0365  # $/MB/month
        self.api_cost_per_call = 0.01  # $/call

    def calculate_optimal_size(
        self,
        current_size_mb: float,
        memory_usage_mb: float,
        hit_rate: float,
        eviction_count: int,
        request_rate_per_second: int,
    ) -> CacheSizeAdjustment:
        used_ratio = memory_usage_mb / max(current_size_mb, 1)
        high_pressure = used_ratio >= 0.90
        low_usage = used_ratio < 0.50 and hit_rate < 0.60
        optimal_band = 0.70 <= used_ratio <= 0.85 and hit_rate >= 0.80

        strategy = CacheSizeStrategy.MAINTAIN
        size_new = current_size_mb

        if high_pressure:
            strategy = CacheSizeStrategy.SCALE_UP
            size_new = min(self.max_size, int(round(current_size_mb * 1.5)))
        elif low_usage:
            strategy = CacheSizeStrategy.SCALE_DOWN
            size_new = max(self.min_size, int(round(current_size_mb * 0.75)))
        elif optimal_band:
            strategy = CacheSizeStrategy.MAINTAIN
            size_new = current_size_mb
        elif used_ratio >= 0.88 and (eviction_count >= 60 or request_rate_per_second >= 80):
            # Near high pressure with high demand → scale up proactively
            strategy = CacheSizeStrategy.SCALE_UP
            size_new = min(self.max_size, int(round(current_size_mb * 1.5)))
        else:
            strategy = CacheSizeStrategy.OPTIMIZE
            size_new = max(self.min_size, min(self.max_size, current_size_mb + (32 if used_ratio > 0.75 else -32)))

        # Estimate memory usage at new size
        expected_usage_ratio = min(1.0, memory_usage_mb / max(size_new, 1))

        # Estimate hit rate change
        if strategy == CacheSizeStrategy.SCALE_UP:
            eviction_factor = min(eviction_count / 100.0, 2.0)
            size_ratio = size_new / max(current_size_mb, 1)
            expected_hit_rate_change = max(0.02, min(0.12, 0.05 * math.log(size_ratio + 1e-6) * max(eviction_factor, 1.0) + 0.03))
        elif strategy == CacheSizeStrategy.SCALE_DOWN:
            size_ratio = size_new / max(current_size_mb, 1)
            expected_hit_rate_change = -max(0.01, min(0.08, (1 - size_ratio) * 0.10))
        else:
            expected_hit_rate_change = 0.0

        # Cost delta (use integer MB for costing)
        size_new_int = int(round(size_new))
        current_size_int = int(round(current_size_mb))
        size_delta_mb = size_new_int - current_size_int
        monthly_cost_delta = size_delta_mb * self.cost_per_mb_per_month

        # ROI score
        api_calls_month = request_rate_per_second * 86400 * 30
        api_savings = expected_hit_rate_change * api_calls_month * self.api_cost_per_call  # $/month
        cost_increase = max(monthly_cost_delta, 0.0)
        if cost_increase <= 0:
            # When cost does not increase (scale down or maintain), be conservative
            roi = 2.5 if expected_hit_rate_change >= 0 else 1.5
        else:
            roi = api_savings / cost_increase if cost_increase > 0 else 0.0

        if roi >= 5:
            roi_score = 10.0
        elif roi >= 2:
            roi_score = 5.0 + (roi - 2.0) * (5.0 / 3.0)
        else:
            roi_score = max(0.0, roi * 2.5)

        # Reward being in an optimal band when maintaining
        if strategy == CacheSizeStrategy.MAINTAIN and optimal_band:
            roi_score = max(roi_score, 8.5)

        confidence = 0.8 if strategy in (CacheSizeStrategy.SCALE_UP, CacheSizeStrategy.SCALE_DOWN) else 0.6

        return CacheSizeAdjustment(
            current_size_mb=current_size_mb,
            recommended_size_mb=size_new_int,
            strategy=strategy,
            expected_memory_usage=expected_usage_ratio,
            expected_hit_rate_change=expected_hit_rate_change,
            monthly_cost_delta=monthly_cost_delta,
            roi_score=roi_score,
            confidence=confidence,
        )
