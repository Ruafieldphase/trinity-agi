from dataclasses import dataclass
from enum import Enum, auto


class SystemHealthLevel(Enum):
    EXCELLENT = auto()
    GOOD = auto()
    WARNING = auto()
    CRITICAL = auto()


@dataclass
class UnifiedFeedback:
    unified_gate_score: float = 0.0
    system_health: str = "GOOD"


class FeedbackOrchestrator:
    def __init__(self, project_id: str, service_name: str):
        self.project_id = project_id
        self.service_name = service_name
    
    def unified_gate(self) -> dict:
        """통합 게이트: 시스템 상태 분석 + 최적화 결정"""
        import random
        
        # 시뮬레이션: 실제로는 Redis/Prometheus에서 메트릭 수집
        cache_hit_rate = random.uniform(60, 95)
        gpu_memory_used_gb = random.uniform(8, 14)
        system_latency_ms = random.uniform(80, 250)
        
        # 시스템 상태 결정
        if cache_hit_rate > 85 and gpu_memory_used_gb < 12 and system_latency_ms < 150:
            system_state = "OPTIMAL"
            should_optimize = False
        elif cache_hit_rate < 60 or gpu_memory_used_gb > 13 or system_latency_ms > 200:
            system_state = "DEGRADED"
            should_optimize = True
        else:
            system_state = "GOOD"
            should_optimize = random.random() < 0.3  # 30% 확률로 최적화
        
        return {
            "system_state": system_state,
            "should_optimize": should_optimize,
            "cache_health": {
                "hit_rate": cache_hit_rate,
                "status": "healthy" if cache_hit_rate > 70 else "degraded"
            },
            "system_metrics": {
                "cache_hit_rate": cache_hit_rate,
                "gpu_memory_used_gb": gpu_memory_used_gb,
                "system_latency_ms": system_latency_ms
            }
        }
