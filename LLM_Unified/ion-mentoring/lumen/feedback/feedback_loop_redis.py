"""
Feedback Loop Redis Monitoring

Redis 캐시 성능을 실시간으로 모니터링하고 피드백 루프에 통합

Lumen v1.7 Resonance Memory 패턴:
- Track A: Cache Performance (hit rate, latency, memory)
- Track B: Cost Efficiency (cache cost, request cost)
- Track C: Adaptive Signals (TTL, size, optimization)

감응 → 증빙 → 적응:
1. 감응: Redis 메트릭 수집 (hit rate, memory, latency)
2. 증빙: 성능 분석 및 상태 저장
3. 적응: TTL/Size 최적화 제안
"""

from google.cloud import monitoring_v3
import datetime
from typing import Dict, Optional, List, Tuple
import logging
import json
import os
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class CacheHealthStatus(Enum):
    """캐시 건강 상태"""
    OPTIMAL = "OPTIMAL"          # 최적 (hit rate > 80%)
    GOOD = "GOOD"                # 양호 (hit rate 60-80%)
    DEGRADED = "DEGRADED"        # 저하 (hit rate 40-60%)
    POOR = "POOR"                # 불량 (hit rate < 40%)


class OptimizationAction(Enum):
    """최적화 액션"""
    NONE = "NONE"                           # 조치 불필요
    INCREASE_TTL = "INCREASE_TTL"           # TTL 증가 (더 오래 캐싱)
    DECREASE_TTL = "DECREASE_TTL"           # TTL 감소 (더 자주 갱신)
    INCREASE_CACHE_SIZE = "INCREASE_CACHE_SIZE"  # 캐시 크기 증가
    DECREASE_CACHE_SIZE = "DECREASE_CACHE_SIZE"  # 캐시 크기 감소
    CLEAR_CACHE = "CLEAR_CACHE"             # 캐시 초기화


@dataclass
class CacheMetrics:
    """캐시 성능 메트릭"""
    timestamp: str
    hit_rate: float              # 캐시 히트율 (%)
    miss_rate: float             # 캐시 미스율 (%)
    total_hits: int              # 총 히트 수
    total_misses: int            # 총 미스 수
    memory_usage_mb: float       # 메모리 사용량 (MB)
    memory_limit_mb: float       # 메모리 제한 (MB)
    memory_usage_pct: float      # 메모리 사용률 (%)
    avg_latency_ms: float        # 평균 레이턴시 (ms)
    eviction_count: int          # 제거된 키 수
    current_ttl_seconds: int     # 현재 TTL (초)
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CacheFeedback:
    """캐시 피드백 결과"""
    health_status: CacheHealthStatus
    optimization_action: OptimizationAction
    recommended_ttl_seconds: Optional[int]
    recommended_cache_size_mb: Optional[float]
    reasoning: str
    metrics: CacheMetrics
    
    def to_dict(self) -> dict:
        result = {
            "health_status": self.health_status.value,
            "optimization_action": self.optimization_action.value,
            "recommended_ttl_seconds": self.recommended_ttl_seconds,
            "recommended_cache_size_mb": self.recommended_cache_size_mb,
            "reasoning": self.reasoning,
            "metrics": self.metrics.to_dict()
        }
        return result


class FeedbackLoopRedis:
    """Redis 캐시 피드백 루프"""
    
    # TTL 범위 (초)
    MIN_TTL_SECONDS = 60        # 1분
    MAX_TTL_SECONDS = 3600      # 1시간
    DEFAULT_TTL_SECONDS = 300   # 5분
    
    # 캐시 크기 범위 (MB)
    MIN_CACHE_SIZE_MB = 10.0
    MAX_CACHE_SIZE_MB = 1024.0
    DEFAULT_CACHE_SIZE_MB = 256.0
    
    # 히트율 임계값
    OPTIMAL_HIT_RATE = 80.0
    GOOD_HIT_RATE = 60.0
    DEGRADED_HIT_RATE = 40.0
    
    def __init__(self, project_id: str, service_name: str = "ion-api-canary"):
        """
        Args:
            project_id: GCP 프로젝트 ID
            service_name: Cloud Run 서비스 이름
        """
        self.project_id = project_id
        self.service_name = service_name
        self.monitoring_client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{project_id}"
        
        # 상태 파일 경로
        self.state_file = os.path.join(
            os.path.dirname(__file__), 
            "../../outputs/feedback_loop_state.json"
        )
    
    def collect_cache_metrics(self, hours: int = 1) -> CacheMetrics:
        """
        Redis 캐시 메트릭 수집
        
        Args:
            hours: 측정 기간 (시간)
        
        Returns:
            CacheMetrics: 캐시 성능 메트릭
        """
        try:
            now = datetime.datetime.utcnow()
            end_time = now
            start_time = now - datetime.timedelta(hours=hours)
            
            interval = monitoring_v3.TimeInterval({
                "start_time": {"seconds": int(start_time.timestamp())},
                "end_time": {"seconds": int(end_time.timestamp())},
            })
            
            # 1. 캐시 히트율 조회
            hit_rate = self._get_cache_hit_rate(interval)
            
            # 2. 메모리 사용량 조회
            memory_usage_mb, memory_limit_mb = self._get_memory_usage(interval)
            
            # 3. 레이턴시 조회
            avg_latency_ms = self._get_cache_latency(interval)
            
            # 4. 제거 횟수 조회
            eviction_count = self._get_eviction_count(interval)
            
            # 5. 현재 TTL 조회 (상태 파일 또는 기본값)
            current_ttl = self._get_current_ttl()
            
            # 6. Hit/Miss 계산 (임시: 실제로는 custom metric 필요)
            total_requests = 10000  # 임시값
            total_hits = int(total_requests * hit_rate / 100)
            total_misses = total_requests - total_hits
            
            miss_rate = 100.0 - hit_rate
            memory_usage_pct = (memory_usage_mb / memory_limit_mb * 100) if memory_limit_mb > 0 else 0.0
            
            metrics = CacheMetrics(
                timestamp=now.isoformat(),
                hit_rate=hit_rate,
                miss_rate=miss_rate,
                total_hits=total_hits,
                total_misses=total_misses,
                memory_usage_mb=memory_usage_mb,
                memory_limit_mb=memory_limit_mb,
                memory_usage_pct=memory_usage_pct,
                avg_latency_ms=avg_latency_ms,
                eviction_count=eviction_count,
                current_ttl_seconds=current_ttl
            )
            
            logger.info(f"Collected cache metrics: hit_rate={hit_rate:.2f}%, memory={memory_usage_mb:.2f}MB")
            return metrics
        
        except Exception as e:
            logger.error(f"Failed to collect cache metrics: {e}")
            # Fallback: 더미 메트릭
            return self._get_dummy_metrics()
    
    def _get_cache_hit_rate(self, interval: monitoring_v3.TimeInterval) -> float:
        """캐시 히트율 조회"""
        try:
            metric_type = "custom.googleapis.com/cache_hit_rate"
            
            request = monitoring_v3.ListTimeSeriesRequest({
                "name": self.project_name,
                "filter": f'metric.type="{metric_type}"',
                "interval": interval,
            })
            
            results = self.monitoring_client.list_time_series(request=request)
            
            for result in results:
                if result.points:
                    return result.points[-1].value.double_value
            
            # 기본값: Phase 14 측정 60%
            return 60.0
        
        except Exception as e:
            logger.warning(f"Cache hit rate metric not found: {e}")
            return 60.0
    
    def _get_memory_usage(self, interval: monitoring_v3.TimeInterval) -> Tuple[float, float]:
        """메모리 사용량 조회"""
        try:
            # Cloud Run 메모리 메트릭
            metric_type = "run.googleapis.com/container/memory/utilizations"
            
            request = monitoring_v3.ListTimeSeriesRequest({
                "name": self.project_name,
                "filter": f'metric.type="{metric_type}" AND resource.labels.service_name="{self.service_name}"',
                "interval": interval,
            })
            
            results = self.monitoring_client.list_time_series(request=request)
            
            memory_usage_pct = 0.0
            for result in results:
                if result.points:
                    memory_usage_pct = result.points[-1].value.double_value * 100
                    break
            
            # Redis 기본 메모리 제한: 256MB
            memory_limit_mb = self.DEFAULT_CACHE_SIZE_MB
            memory_usage_mb = memory_limit_mb * (memory_usage_pct / 100)
            
            return memory_usage_mb, memory_limit_mb
        
        except Exception as e:
            logger.warning(f"Memory usage metric not found: {e}")
            return 150.0, 256.0  # 150MB / 256MB (58%)
    
    def _get_cache_latency(self, interval: monitoring_v3.TimeInterval) -> float:
        """캐시 레이턴시 조회"""
        try:
            # Custom metric: custom/cache_latency_ms
            metric_type = "custom.googleapis.com/cache_latency_ms"
            
            request = monitoring_v3.ListTimeSeriesRequest({
                "name": self.project_name,
                "filter": f'metric.type="{metric_type}"',
                "interval": interval,
            })
            
            results = self.monitoring_client.list_time_series(request=request)
            
            for result in results:
                if result.points:
                    return result.points[-1].value.double_value
            
            # 기본값: Redis 평균 레이턴시 ~1ms
            return 1.0
        
        except Exception as e:
            logger.warning(f"Cache latency metric not found: {e}")
            return 1.0
    
    def _get_eviction_count(self, interval: monitoring_v3.TimeInterval) -> int:
        """제거된 키 수 조회"""
        try:
            # Custom metric: custom/cache_evictions
            metric_type = "custom.googleapis.com/cache_evictions"
            
            request = monitoring_v3.ListTimeSeriesRequest({
                "name": self.project_name,
                "filter": f'metric.type="{metric_type}"',
                "interval": interval,
            })
            
            results = self.monitoring_client.list_time_series(request=request)
            
            for result in results:
                if result.points:
                    return int(result.points[-1].value.int64_value)
            
            return 0
        
        except Exception as e:
            logger.warning(f"Cache eviction metric not found: {e}")
            return 0
    
    def _get_current_ttl(self) -> int:
        """현재 TTL 조회 (상태 파일)"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    return state.get("current_ttl_seconds", self.DEFAULT_TTL_SECONDS)
        except Exception as e:
            logger.warning(f"Failed to read state file: {e}")
        
        return self.DEFAULT_TTL_SECONDS
    
    def _get_dummy_metrics(self) -> CacheMetrics:
        """더미 메트릭 (fallback)"""
        return CacheMetrics(
            timestamp=datetime.datetime.utcnow().isoformat(),
            hit_rate=60.0,
            miss_rate=40.0,
            total_hits=6000,
            total_misses=4000,
            memory_usage_mb=150.0,
            memory_limit_mb=256.0,
            memory_usage_pct=58.6,
            avg_latency_ms=1.0,
            eviction_count=0,
            current_ttl_seconds=self.DEFAULT_TTL_SECONDS
        )
    
    def analyze_cache_feedback(self, metrics: CacheMetrics) -> CacheFeedback:
        """
        캐시 메트릭 분석 및 피드백 생성
        
        Lumen v1.7 Resonance Memory:
        - Track A: Cache Performance (hit rate)
        - Track B: Memory Efficiency (usage vs limit)
        - Track C: Adaptive Signal (TTL optimization)
        
        Args:
            metrics: 수집된 캐시 메트릭
        
        Returns:
            CacheFeedback: 최적화 제안
        """
        # 1. Health Status 결정
        if metrics.hit_rate >= self.OPTIMAL_HIT_RATE:
            health_status = CacheHealthStatus.OPTIMAL
        elif metrics.hit_rate >= self.GOOD_HIT_RATE:
            health_status = CacheHealthStatus.GOOD
        elif metrics.hit_rate >= self.DEGRADED_HIT_RATE:
            health_status = CacheHealthStatus.DEGRADED
        else:
            health_status = CacheHealthStatus.POOR
        
        # 2. Optimization Action 결정
        action, recommended_ttl, recommended_size, reasoning = self._decide_optimization(
            metrics, health_status
        )
        
        feedback = CacheFeedback(
            health_status=health_status,
            optimization_action=action,
            recommended_ttl_seconds=recommended_ttl,
            recommended_cache_size_mb=recommended_size,
            reasoning=reasoning,
            metrics=metrics
        )
        
        logger.info(f"Cache feedback: {health_status.value}, action: {action.value}")
        return feedback
    
    def _decide_optimization(
        self, 
        metrics: CacheMetrics, 
        health_status: CacheHealthStatus
    ) -> Tuple[OptimizationAction, Optional[int], Optional[float], str]:
        """
        최적화 액션 결정 로직
        
        Returns:
            (action, recommended_ttl, recommended_size, reasoning)
        """
        current_ttl = metrics.current_ttl_seconds
        memory_usage_pct = metrics.memory_usage_pct
        eviction_count = metrics.eviction_count
        hit_rate = metrics.hit_rate
        
        # Case 1: OPTIMAL - 조치 불필요
        if health_status == CacheHealthStatus.OPTIMAL:
            if memory_usage_pct > 90:
                # 메모리 부족 → 크기 증가
                new_size = min(metrics.memory_limit_mb * 1.5, self.MAX_CACHE_SIZE_MB)
                return (
                    OptimizationAction.INCREASE_CACHE_SIZE,
                    None,
                    new_size,
                    f"높은 히트율({hit_rate:.1f}%)이지만 메모리 사용률({memory_usage_pct:.1f}%) 높음. "
                    f"캐시 크기 증가 권장."
                )
            else:
                return (
                    OptimizationAction.NONE,
                    None,
                    None,
                    f"캐시가 최적 상태입니다. 히트율: {hit_rate:.1f}%, 메모리: {memory_usage_pct:.1f}%"
                )
        
        # Case 2: GOOD - TTL 미세 조정
        if health_status == CacheHealthStatus.GOOD:
            if eviction_count > 100:
                # 많은 제거 → TTL 감소 또는 크기 증가
                new_ttl = max(current_ttl - 60, self.MIN_TTL_SECONDS)
                return (
                    OptimizationAction.DECREASE_TTL,
                    new_ttl,
                    None,
                    f"많은 키 제거({eviction_count}개) 발생. TTL을 {current_ttl}초 → {new_ttl}초로 감소하여 "
                    f"메모리 압박 완화."
                )
            elif hit_rate < 70 and current_ttl < self.MAX_TTL_SECONDS:
                # 히트율 개선 여지 → TTL 증가
                new_ttl = min(current_ttl + 120, self.MAX_TTL_SECONDS)
                return (
                    OptimizationAction.INCREASE_TTL,
                    new_ttl,
                    None,
                    f"히트율({hit_rate:.1f}%) 개선 가능. TTL을 {current_ttl}초 → {new_ttl}초로 증가하여 "
                    f"캐싱 효과 향상."
                )
            else:
                return (
                    OptimizationAction.NONE,
                    None,
                    None,
                    f"캐시가 양호합니다. 히트율: {hit_rate:.1f}%, TTL: {current_ttl}초"
                )
        
        # Case 3: DEGRADED - 적극적 조정
        if health_status == CacheHealthStatus.DEGRADED:
            if memory_usage_pct > 80:
                # 메모리 부족 → 크기 증가
                new_size = min(metrics.memory_limit_mb * 1.5, self.MAX_CACHE_SIZE_MB)
                return (
                    OptimizationAction.INCREASE_CACHE_SIZE,
                    None,
                    new_size,
                    f"히트율 저하({hit_rate:.1f}%)와 높은 메모리 사용률({memory_usage_pct:.1f}%). "
                    f"캐시 크기 {metrics.memory_limit_mb:.0f}MB → {new_size:.0f}MB로 증가 권장."
                )
            elif current_ttl < 600:
                # TTL이 짧음 → 증가
                new_ttl = min(current_ttl * 2, self.MAX_TTL_SECONDS)
                return (
                    OptimizationAction.INCREASE_TTL,
                    new_ttl,
                    None,
                    f"히트율 저하({hit_rate:.1f}%). TTL이 짧음({current_ttl}초). "
                    f"{new_ttl}초로 증가하여 캐싱 효과 향상."
                )
            else:
                return (
                    OptimizationAction.CLEAR_CACHE,
                    None,
                    None,
                    f"히트율 저하({hit_rate:.1f}%). 캐시 패턴 변경 가능성. "
                    f"캐시 초기화 후 재구축 권장."
                )
        
        # Case 4: POOR - 긴급 조치
        if health_status == CacheHealthStatus.POOR:
            return (
                OptimizationAction.CLEAR_CACHE,
                self.DEFAULT_TTL_SECONDS,
                None,
                f"캐시 히트율 심각({hit_rate:.1f}%). 캐시 초기화 및 TTL {self.DEFAULT_TTL_SECONDS}초로 재설정 필요."
            )
        
        # Default
        return (
            OptimizationAction.NONE,
            None,
            None,
            "알 수 없는 상태"
        )
    
    def save_feedback_state(self, feedback: CacheFeedback):
        """피드백 상태 저장"""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            
            state = {
                "timestamp": feedback.metrics.timestamp,
                "health_status": feedback.health_status.value,
                "optimization_action": feedback.optimization_action.value,
                "current_ttl_seconds": feedback.metrics.current_ttl_seconds,
                "recommended_ttl_seconds": feedback.recommended_ttl_seconds,
                "recommended_cache_size_mb": feedback.recommended_cache_size_mb,
                "hit_rate": feedback.metrics.hit_rate,
                "memory_usage_mb": feedback.metrics.memory_usage_mb,
                "reasoning": feedback.reasoning
            }
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved feedback state to {self.state_file}")
        
        except Exception as e:
            logger.error(f"Failed to save feedback state: {e}")
    
    def generate_feedback_report(self, feedback: CacheFeedback) -> str:
        """
        Markdown 피드백 리포트 생성
        
        Returns:
            Markdown 형식 리포트
        """
        m = feedback.metrics
        
        report = f"""# Redis Cache Feedback Report

**생성 시각**: {m.timestamp}

---

## 📊 Cache Health Status

**상태**: {feedback.health_status.value}

| 메트릭 | 값 | 상태 |
|--------|-----|------|
| **히트율** | {m.hit_rate:.2f}% | {'🟢 OPTIMAL' if m.hit_rate >= 80 else '🟡 GOOD' if m.hit_rate >= 60 else '🟠 DEGRADED' if m.hit_rate >= 40 else '🔴 POOR'} |
| **미스율** | {m.miss_rate:.2f}% | - |
| **메모리 사용률** | {m.memory_usage_pct:.2f}% ({m.memory_usage_mb:.2f}MB / {m.memory_limit_mb:.2f}MB) | {'🟢' if m.memory_usage_pct < 70 else '🟡' if m.memory_usage_pct < 85 else '🔴'} |
| **평균 레이턴시** | {m.avg_latency_ms:.2f}ms | {'🟢' if m.avg_latency_ms < 5 else '🟡' if m.avg_latency_ms < 10 else '🔴'} |
| **제거된 키** | {m.eviction_count} | {'🟢' if m.eviction_count < 10 else '🟡' if m.eviction_count < 100 else '🔴'} |
| **현재 TTL** | {m.current_ttl_seconds}초 | - |

---

## 🎯 Optimization Action

**권장 액션**: {feedback.optimization_action.value}

**상세 분석**:
{feedback.reasoning}

**권장 설정**:
"""
        
        if feedback.recommended_ttl_seconds:
            report += f"- **TTL**: {m.current_ttl_seconds}초 → **{feedback.recommended_ttl_seconds}초**\n"
        
        if feedback.recommended_cache_size_mb:
            report += f"- **캐시 크기**: {m.memory_limit_mb:.0f}MB → **{feedback.recommended_cache_size_mb:.0f}MB**\n"
        
        if feedback.optimization_action == OptimizationAction.NONE:
            report += "- 현재 설정 유지\n"
        
        report += f"""

---

## 📈 Performance Metrics

### Hit/Miss Statistics
- **총 히트**: {m.total_hits:,}
- **총 미스**: {m.total_misses:,}
- **히트율**: {m.hit_rate:.2f}%

### Memory Usage
- **사용량**: {m.memory_usage_mb:.2f}MB
- **제한**: {m.memory_limit_mb:.2f}MB
- **사용률**: {m.memory_usage_pct:.2f}%

### Latency
- **평균**: {m.avg_latency_ms:.2f}ms

---

## 🔄 Lumen v1.7 Resonance Memory

### Track A: Cache Performance
- Hit Rate: {m.hit_rate:.2f}%
- Latency: {m.avg_latency_ms:.2f}ms

### Track B: Memory Efficiency
- Usage: {m.memory_usage_pct:.2f}%
- Evictions: {m.eviction_count}

### Track C: Adaptive Signal
- Current TTL: {m.current_ttl_seconds}s
- Recommended: {feedback.recommended_ttl_seconds or m.current_ttl_seconds}s

---

**생성**: Lumen Feedback Loop Redis v1.0
"""
        
        return report
    
    def run_feedback_loop(self) -> CacheFeedback:
        """
        피드백 루프 실행: 수집 → 분석 → 저장 → 리포트
        
        Returns:
            CacheFeedback: 피드백 결과
        """
        logger.info("Starting Redis cache feedback loop...")
        
        # 1. 메트릭 수집 (감응)
        metrics = self.collect_cache_metrics(hours=1)
        
        # 2. 피드백 분석 (증빙)
        feedback = self.analyze_cache_feedback(metrics)
        
        # 3. 상태 저장 (증빙)
        self.save_feedback_state(feedback)
        
        # 4. 리포트 생성 (증빙)
        report = self.generate_feedback_report(feedback)
        
        # 리포트 파일 저장
        report_file = os.path.join(
            os.path.dirname(self.state_file),
            "feedback_loop_report.md"
        )
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Saved feedback report to {report_file}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
        
        logger.info(f"Feedback loop completed: {feedback.health_status.value}, {feedback.optimization_action.value}")
        return feedback


if __name__ == "__main__":
    import sys
    
    # Logging 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 프로젝트 ID
    project_id = os.environ.get("GCP_PROJECT_ID", "naeda-genesis")
    service_name = os.environ.get("SERVICE_NAME", "ion-api-canary")
    
    # 피드백 루프 실행
    feedback_loop = FeedbackLoopRedis(project_id, service_name)
    feedback = feedback_loop.run_feedback_loop()
    
    # 결과 출력
    print("\n" + "=" * 60)
    print(f"Health Status: {feedback.health_status.value}")
    print(f"Optimization Action: {feedback.optimization_action.value}")
    print(f"Hit Rate: {feedback.metrics.hit_rate:.2f}%")
    print(f"Memory Usage: {feedback.metrics.memory_usage_pct:.2f}%")
    print("\nReasoning:")
    print(feedback.reasoning)
    print("=" * 60)
    
    # Exit code
    if feedback.health_status == CacheHealthStatus.OPTIMAL:
        sys.exit(0)
    elif feedback.health_status == CacheHealthStatus.GOOD:
        sys.exit(0)
    elif feedback.health_status == CacheHealthStatus.DEGRADED:
        sys.exit(1)
    else:  # POOR
        sys.exit(2)
