"""
Feedback Orchestrator

Cost Rhythm Loop와 Cache Optimization 통합 오케스트레이터

Lumen v1.7 완전 통합:
- Phase 1-2-3: Maturity → ROI → SLO → Cost Rhythm
- Phase 4: Feedback Loop (Cache Optimization)
- Unified Gate: ROI × SLO × Maturity × Cache Performance

감응 → 증빙 → 적응 (전체 루프):
1. 감응: 모든 메트릭 수집 (maturity, cost, cache)
2. 증빙: 통합 분석, 최적화 제안
3. 적응: 자동 조정 (TTL, 캐시 크기, 인스턴스)
"""

import sys
import os

# 상위 디렉토리를 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import Dict, Optional, Tuple
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import json
import datetime

# Lumen 모듈
from exporters.maturity_exporter_cloudrun import MaturityExporterCloudRun
from exporters.roi_gate_cloudrun import ROIGateCloudRun
from exporters.slo_exporter_cloudrun import SLOExporterCloudRun
from monitoring.cost_rhythm_loop import CostRhythmLoop, RhythmStatus
from feedback.feedback_loop_redis import FeedbackLoopRedis, CacheHealthStatus
from feedback.adaptive_ttl_policy import AdaptiveTTLPolicy
from feedback.cache_size_optimizer import CacheSizeOptimizer
from feedback.metrics_logger import log_feedback_metrics
from feedback.request_volume_tracker import RequestVolumeTracker

logger = logging.getLogger(__name__)


class SystemHealthLevel(Enum):
    """전체 시스템 건강도"""
    EXCELLENT = "EXCELLENT"      # 모든 메트릭 최적
    GOOD = "GOOD"                # 대부분 양호
    WARNING = "WARNING"          # 일부 문제
    CRITICAL = "CRITICAL"        # 심각한 문제


@dataclass
class UnifiedFeedback:
    """통합 피드백 결과"""
    timestamp: str
    system_health: SystemHealthLevel
    
    # Phase 1-2-3 메트릭
    maturity_score: float
    maturity_level: int
    roi_score: float
    slo_compliance: float
    cost_rhythm_status: str
    
    # Phase 4 메트릭
    cache_health: str
    cache_hit_rate: float
    current_ttl: int
    current_cache_size_mb: float
    
    # 최적화 제안
    recommended_ttl: Optional[int]
    recommended_cache_size_mb: Optional[float]
    recommended_action: Optional[str]
    
    # 통합 분석
    unified_gate_score: float          # ROI × SLO × Maturity × Cache (0-100)
    optimization_priority: str         # HIGH, MEDIUM, LOW
    reasoning: str
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "system_health": self.system_health.value,
            "maturity_score": round(self.maturity_score, 2),
            "maturity_level": self.maturity_level,
            "roi_score": round(self.roi_score, 2),
            "slo_compliance": round(self.slo_compliance, 2),
            "cost_rhythm_status": self.cost_rhythm_status,
            "cache_health": self.cache_health,
            "cache_hit_rate": round(self.cache_hit_rate, 2),
            "current_ttl": self.current_ttl,
            "current_cache_size_mb": round(self.current_cache_size_mb, 2),
            "recommended_ttl": self.recommended_ttl,
            "recommended_cache_size_mb": self.recommended_cache_size_mb,
            "recommended_action": self.recommended_action,
            "unified_gate_score": round(self.unified_gate_score, 2),
            "optimization_priority": self.optimization_priority,
            "reasoning": self.reasoning
        }


class FeedbackOrchestrator:
    """피드백 루프 오케스트레이터"""
    
    def __init__(self, project_id: str, service_name: str = "ion-api-canary", budget_usd: float = 200.0):
        """
        Args:
            project_id: GCP 프로젝트 ID
            service_name: Cloud Run 서비스 이름
            budget_usd: 월간 예산 (USD)
        """
        self.project_id = project_id
        self.service_name = service_name
        self.budget_usd = budget_usd
        
        # Phase 1-2-3 컴포넌트
        self.maturity_exporter = MaturityExporterCloudRun(project_id, service_name)
        self.roi_gate = ROIGateCloudRun(project_id, service_name)
        self.slo_exporter = SLOExporterCloudRun(project_id, service_name)
        # CostRhythmLoop 현재 시그니처는 (project_id, service_name)만 허용
        self.cost_rhythm = CostRhythmLoop(project_id, service_name)
        
        # Phase 4 컴포넌트
        self.feedback_redis = FeedbackLoopRedis(project_id, service_name)
        self.ttl_policy = AdaptiveTTLPolicy()
        self.size_optimizer = CacheSizeOptimizer()

        # Volume tracker (growth & ROI milestones)
        self.volume_tracker = RequestVolumeTracker(project_id, service_name)
        self._last_volume_trend = None
        
        # Orchestration Bridge (Phase 5.5 통합)
        try:
            import sys
            workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
            sys.path.insert(0, workspace_root)
            from scripts.orchestration_bridge import OrchestrationBridge
            self.orchestration_bridge = OrchestrationBridge(workspace_root=workspace_root)
            logger.info("OrchestrationBridge initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize OrchestrationBridge: {e}")
            self.orchestration_bridge = None
        
        # 상태 파일
        self.state_file = os.path.join(
            os.path.dirname(__file__),
            "../outputs/orchestrator_state.json"
        )
    
    def run_complete_feedback_loop(self) -> UnifiedFeedback:
        """
        전체 피드백 루프 실행
        
        단계:
        1. Phase 1-2-3 메트릭 수집 (Maturity, ROI, SLO, Cost)
        2. Phase 4 메트릭 수집 (Cache)
        3. 통합 분석 (Unified Gate)
        4. 최적화 제안
        5. 상태 저장
        
        Returns:
            UnifiedFeedback: 통합 피드백 결과
        """
        logger.info("=" * 60)
        logger.info("Starting Complete Feedback Loop (Lumen v1.7)")
        logger.info("=" * 60)

        # === Phase 0: Monitoring Context (NEW - Phase 5.5) ===
        monitoring_context = None
        if self.orchestration_bridge:
            try:
                logger.info("\n[Phase 0] Fetching Monitoring Context...")
                monitoring_context = self.orchestration_bridge.get_orchestration_context()
                logger.info(f"  Overall Health: {monitoring_context.overall_health}")
                logger.info(f"  Effective Availability: {monitoring_context.effective_availability:.2f}%")
                logger.info(f"  Recommended Routing: {monitoring_context.recommended_primary} → {monitoring_context.recommended_fallback}")
                if monitoring_context.recovery_needed:
                    logger.warning(f"  🔴 Recovery Needed: {monitoring_context.recovery_reason}")
            except Exception as e:
                logger.warning(f"  Failed to fetch monitoring context: {e}")

        # === Phase 1: Maturity Metrics ===
        logger.info("\n[Phase 1] Collecting Maturity Metrics...")
        maturity_result = self.maturity_exporter.calculate_maturity_score()
        maturity_score = float(maturity_result["maturity_score"])
        # 간이 레벨 산정 (스코어 → 레벨 1~5)
        if maturity_score >= 80:
            maturity_level = 5
        elif maturity_score >= 60:
            maturity_level = 4
        elif maturity_score >= 40:
            maturity_level = 3
        elif maturity_score >= 20:
            maturity_level = 2
        else:
            maturity_level = 1
        logger.info(f"  Maturity Score: {maturity_score:.2f}, Level: {maturity_level}")

        # === Phase 1: ROI Gate ===
        logger.info("\n[Phase 1] Calculating ROI Gate...")
        roi_result = self.roi_gate.calculate_roi_score()
        roi_score = float(roi_result["roi_score"])
        logger.info(f"  ROI Score: {roi_score:.2f}%")

        # === Phase 2: SLO Compliance ===
        logger.info("\n[Phase 2] Checking SLO Compliance...")
        slo_result = self.slo_exporter.evaluate_slo_status()
        slo_compliance = float(slo_result["slo_compliance"])
        logger.info(f"  SLO Compliance: {slo_compliance:.2f}%")

        # === Phase 3: Cost Rhythm ===
        logger.info("\n[Phase 3] Analyzing Cost Rhythm...")
        cost_result = self.cost_rhythm.calculate_rhythm_state()
        cost_rhythm_status = cost_result.rhythm_status
        logger.info(f"  Cost Rhythm: {cost_rhythm_status}")

        # === Phase 4: Cache Feedback ===
        logger.info("\n[Phase 4] Collecting Cache Feedback...")
        cache_feedback = self.feedback_redis.run_feedback_loop()
        cache_health = cache_feedback.health_status.value
        cache_hit_rate = float(cache_feedback.metrics.hit_rate)
        current_ttl = int(cache_feedback.metrics.current_ttl_seconds)
        current_cache_size = float(cache_feedback.metrics.memory_limit_mb)
        logger.info(f"  Cache Health: {cache_health}, Hit Rate: {cache_hit_rate:.2f}%")

        # === Unified Analysis ===
        logger.info("\n[Unified Analysis] Calculating Unified Gate Score...")
        unified_gate_score = self._calculate_unified_gate_score(
            maturity_score, roi_score, slo_compliance, cache_hit_rate
        )
        logger.info(f"  Unified Gate Score: {unified_gate_score:.2f}/100")

        # === System Health Determination ===
        system_health = self._determine_system_health(
            unified_gate_score, cost_rhythm_status, cache_health,
            monitoring_context=monitoring_context  # Phase 5.5 통합
        )
        logger.info(f"  System Health: {system_health.value}")

        # === Optimization Recommendations ===
        logger.info("\n[Optimization] Generating Recommendations...")
        cost_result_dict = asdict(cost_result)
        (recommended_ttl, recommended_size, recommended_action,
         optimization_priority, reasoning) = self._generate_optimization_recommendations(
            cache_feedback, cost_result_dict, maturity_score, roi_score, slo_compliance
        )

        logger.info(f"  Priority: {optimization_priority}")
        if recommended_ttl:
            logger.info(f"  Recommended TTL: {current_ttl}s → {recommended_ttl}s")
        if recommended_size:
            logger.info(f"  Recommended Cache Size: {current_cache_size:.0f}MB → {recommended_size:.0f}MB")

        # === Unified Feedback ===
        feedback = UnifiedFeedback(
            timestamp=datetime.datetime.utcnow().isoformat(),
            system_health=system_health,
            maturity_score=maturity_score,
            maturity_level=maturity_level,
            roi_score=roi_score,
            slo_compliance=slo_compliance,
            cost_rhythm_status=cost_rhythm_status,
            cache_health=cache_health,
            cache_hit_rate=cache_hit_rate,
            current_ttl=current_ttl,
            current_cache_size_mb=current_cache_size,
            recommended_ttl=recommended_ttl,
            recommended_cache_size_mb=recommended_size,
            recommended_action=recommended_action,
            unified_gate_score=unified_gate_score,
            optimization_priority=optimization_priority,
            reasoning=reasoning
        )

        # === Save State ===
        self._save_orchestrator_state(feedback)

        # === Volume Tracking (non-blocking) ===
        try:
            # Use successful request count from ROI exporter (last 24h)
            daily_requests = int(roi_result.get("successful_requests", 0))
            self._last_volume_trend = self.volume_tracker.track(daily_requests)
            logger.info("Tracked request volume: %s req/day", daily_requests)
        except Exception as e:
            logger.warning("Volume tracking skipped: %s", e)

        # === Emit structured feedback metrics to Cloud Logging ===
        try:
            log_feedback_metrics(
                service_name=self.service_name,
                cache_hit_rate=max(0.0, min(1.0, cache_hit_rate / 100.0)),
                memory_usage_percent=max(0.0, min(100.0, cache_feedback.metrics.memory_usage_pct)),
                avg_ttl_seconds=max(0.0, float(cache_feedback.metrics.current_ttl_seconds)),
                unified_health_score=max(0.0, min(100.0, float(unified_gate_score))),
                project_id=self.project_id,
                extra={
                    "cache_health": cache_health,
                    "cost_rhythm_status": cost_rhythm_status,
                },
                dry_run=False,
            )
            logger.info("Emitted structured feedback metrics to Cloud Logging")
        except Exception as e:
            logger.warning(f"Failed to emit feedback metrics: {e}")

        logger.info("\n" + "=" * 60)
        logger.info("Complete Feedback Loop Finished")
        logger.info("=" * 60)

        return feedback
    
    def _calculate_unified_gate_score(
        self, 
        maturity_score: float,
        roi_score: float,
        slo_compliance: float,
        cache_hit_rate: float
    ) -> float:
        """
        Unified Gate Score 계산
        
        Lumen v1.6 확장:
        - ROI Gate: 30%
        - SLO Compliance: 25%
        - Maturity: 25%
        - Cache Performance: 20%
        """
        # 정규화 (모두 0-100 범위)
        normalized_roi = min(roi_score / 100, 1.0) * 100  # ROI %를 0-100으로
        normalized_slo = slo_compliance
        normalized_maturity = maturity_score
        normalized_cache = cache_hit_rate
        
        # 가중 평균
        weights = {
            "roi": 0.30,
            "slo": 0.25,
            "maturity": 0.25,
            "cache": 0.20
        }
        
        unified_score = (
            normalized_roi * weights["roi"] +
            normalized_slo * weights["slo"] +
            normalized_maturity * weights["maturity"] +
            normalized_cache * weights["cache"]
        )
        
        return unified_score
    
    def _determine_system_health(
        self,
        unified_gate_score: float,
        cost_rhythm_status: str,
        cache_health: str,
        monitoring_context=None  # NEW: Phase 5.5 모니터링 통합
    ) -> SystemHealthLevel:
        """전체 시스템 건강도 결정"""
        # === NEW: Monitoring Context 우선 검증 ===
        if monitoring_context:
            # 채널 가용성이 심각하게 낮으면 CRITICAL
            if monitoring_context.effective_availability < 80:
                logger.warning(f"Critical: Effective availability {monitoring_context.effective_availability:.1f}% < 80%")
                return SystemHealthLevel.CRITICAL
            
            # 복구 필요 신호가 있고 unified_gate_score도 낮으면 WARNING
            if monitoring_context.recovery_needed and unified_gate_score < 70:
                logger.warning(f"Warning: Recovery needed ({monitoring_context.recovery_reason}) + Low gate score")
                return SystemHealthLevel.WARNING
        
        # === 기존 로직 ===
        # Critical 조건
        if cost_rhythm_status == RhythmStatus.CHAOTIC.value:
            return SystemHealthLevel.CRITICAL
        
        if cache_health == CacheHealthStatus.POOR.value and unified_gate_score < 50:
            return SystemHealthLevel.CRITICAL
        
        # Warning 조건
        if cost_rhythm_status == RhythmStatus.DISSONANT.value:
            return SystemHealthLevel.WARNING
        
        if cache_health in [CacheHealthStatus.DEGRADED.value, CacheHealthStatus.POOR.value]:
            return SystemHealthLevel.WARNING
        
        if unified_gate_score < 60:
            return SystemHealthLevel.WARNING
        
        # Excellent 조건 (모니터링 건강도도 고려)
        monitoring_excellent = (
            monitoring_context and
            monitoring_context.effective_availability >= 99 and
            not monitoring_context.recovery_needed
        ) if monitoring_context else True  # monitoring_context 없으면 기존 로직 유지
        
        if (unified_gate_score >= 85 and 
            cost_rhythm_status == RhythmStatus.RESONANT.value and
            cache_health == CacheHealthStatus.OPTIMAL.value and
            monitoring_excellent):
            return SystemHealthLevel.EXCELLENT
        
        # 그 외: Good
        return SystemHealthLevel.GOOD
    
    def _generate_optimization_recommendations(
        self,
        cache_feedback,
        cost_result: dict,
        maturity_score: float,
        roi_score: float,
        slo_compliance: float
    ) -> Tuple[Optional[int], Optional[float], Optional[str], str, str]:
        """
        최적화 권장사항 생성
        
        Returns:
            (recommended_ttl, recommended_cache_size, recommended_action, priority, reasoning)
        """
        recommendations = []
        priority_score = 0
        
        # 1. Cache Optimization
        if cache_feedback.optimization_action.value != "NONE":
            recommendations.append(f"Cache: {cache_feedback.optimization_action.value}")
            priority_score += 3
        
        # 2. Cost Rhythm Action (문자열/Enum 모두 허용)
        adaptive_action_val = cost_result.get("adaptive_action")
        if (adaptive_action_val is not None) and hasattr(adaptive_action_val, "value"):
            adaptive_action_str = adaptive_action_val.value
        else:
            adaptive_action_str = str(adaptive_action_val) if adaptive_action_val is not None else "NONE"

        if adaptive_action_str != "NONE":
            recommendations.append(f"Cost: {adaptive_action_str}")
            priority_score += 5  # Cost가 가장 중요
        
        # 3. Maturity Improvement
        if maturity_score < 60:
            recommendations.append("Maturity: Improve monitoring coverage")
            priority_score += 2
        
        # 4. SLO Violation
        if slo_compliance < 95:
            recommendations.append("SLO: Scale up to meet targets")
            priority_score += 4
        
        # 우선순위 결정
        if priority_score >= 8:
            priority = "HIGH"
        elif priority_score >= 4:
            priority = "MEDIUM"
        else:
            priority = "LOW"
        
        # TTL 권장
        recommended_ttl = cache_feedback.recommended_ttl_seconds
        
        # 캐시 크기 권장
        recommended_size = cache_feedback.recommended_cache_size_mb
        
        # 주요 액션
        if adaptive_action_str != "NONE":
            recommended_action = adaptive_action_str
        elif cache_feedback.optimization_action.value != "NONE":
            recommended_action = cache_feedback.optimization_action.value
        else:
            recommended_action = "NONE"
        
        # 이유
        reasoning_parts = [cache_feedback.reasoning]
        
        rhythm_status_val = cost_result.get("rhythm_status")
        if (rhythm_status_val is not None) and hasattr(rhythm_status_val, "value"):
            rhythm_status_str = rhythm_status_val.value
        else:
            rhythm_status_str = str(rhythm_status_val) if rhythm_status_val is not None else "UNKNOWN"

        if adaptive_action_str != "NONE":
            reasoning_parts.append(f"비용 리듬: {rhythm_status_str}, 액션: {adaptive_action_str}")
        
        if maturity_score < 60:
            reasoning_parts.append(f"성숙도 낮음 ({maturity_score:.0f}점)")
        
        if slo_compliance < 95:
            reasoning_parts.append(f"SLO 미달 ({slo_compliance:.1f}%)")
        
        reasoning = " | ".join(reasoning_parts)
        
        return (recommended_ttl, recommended_size, recommended_action, priority, reasoning)
    
    def _save_orchestrator_state(self, feedback: UnifiedFeedback):
        """오케스트레이터 상태 저장"""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(feedback.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved orchestrator state to {self.state_file}")
        
        except Exception as e:
            logger.error(f"Failed to save orchestrator state: {e}")
    
    def generate_unified_report(self, feedback: UnifiedFeedback) -> str:
        """
        통합 리포트 생성
        
        Returns:
            Markdown 형식 리포트
        """
        report = f"""# Lumen v1.7 Unified Feedback Report

**생성 시각**: {feedback.timestamp}

---

## 🏥 System Health Status

**전체 건강도**: {feedback.system_health.value}

| 항목 | 값 | 상태 |
|------|-----|------|
| **Unified Gate Score** | {feedback.unified_gate_score:.2f}/100 | {'🟢 EXCELLENT' if feedback.unified_gate_score >= 85 else '🟡 GOOD' if feedback.unified_gate_score >= 70 else '🟠 WARNING' if feedback.unified_gate_score >= 50 else '🔴 CRITICAL'} |
| **Maturity Score** | {feedback.maturity_score:.2f} (Level {feedback.maturity_level}) | {'🟢' if feedback.maturity_score >= 80 else '🟡' if feedback.maturity_score >= 60 else '🔴'} |
| **ROI Score** | {feedback.roi_score:.2f}% | {'🟢' if feedback.roi_score >= 500 else '🟡' if feedback.roi_score >= 300 else '🔴'} |
| **SLO Compliance** | {feedback.slo_compliance:.2f}% | {'🟢' if feedback.slo_compliance >= 99 else '🟡' if feedback.slo_compliance >= 95 else '🔴'} |
| **Cost Rhythm** | {feedback.cost_rhythm_status} | {'🟢' if feedback.cost_rhythm_status == 'RESONANT' else '🟡' if feedback.cost_rhythm_status == 'DISSONANT' else '🔴'} |
| **Cache Health** | {feedback.cache_health} | {'🟢' if feedback.cache_health == 'OPTIMAL' else '🟡' if feedback.cache_health == 'GOOD' else '🟠' if feedback.cache_health == 'DEGRADED' else '🔴'} |
| **Cache Hit Rate** | {feedback.cache_hit_rate:.2f}% | {'🟢' if feedback.cache_hit_rate >= 80 else '🟡' if feedback.cache_hit_rate >= 60 else '🔴'} |

---

## 🎯 Optimization Recommendations

**우선순위**: {feedback.optimization_priority}

"""
        
        if feedback.recommended_action and feedback.recommended_action != "NONE":
            report += f"**권장 액션**: {feedback.recommended_action}\n\n"
        
        if feedback.recommended_ttl:
            report += f"### TTL 조정\n"
            report += f"- **현재**: {feedback.current_ttl}초\n"
            report += f"- **권장**: {feedback.recommended_ttl}초\n\n"
        
        if feedback.recommended_cache_size_mb:
            report += f"### 캐시 크기 조정\n"
            report += f"- **현재**: {feedback.current_cache_size_mb:.0f}MB\n"
            report += f"- **권장**: {feedback.recommended_cache_size_mb:.0f}MB\n\n"
        
        report += f"""### 분석

{feedback.reasoning}

---

## 📊 Phase 별 메트릭

### Phase 1: Maturity & ROI
- **Maturity Score**: {feedback.maturity_score:.2f} (Level {feedback.maturity_level})
- **ROI Score**: {feedback.roi_score:.2f}%

### Phase 2: SLO
- **Compliance**: {feedback.slo_compliance:.2f}%

### Phase 3: Cost Rhythm
- **Status**: {feedback.cost_rhythm_status}

### Phase 4: Cache Feedback
- **Health**: {feedback.cache_health}
- **Hit Rate**: {feedback.cache_hit_rate:.2f}%
- **TTL**: {feedback.current_ttl}초
- **Size**: {feedback.current_cache_size_mb:.0f}MB

---

## 🔄 Lumen v1.7 Unified Gate

**ROI × SLO × Maturity × Cache = {feedback.unified_gate_score:.2f}/100**

- ROI (30%): {feedback.roi_score:.2f}%
- SLO (25%): {feedback.slo_compliance:.2f}%
- Maturity (25%): {feedback.maturity_score:.2f}
- Cache (20%): {feedback.cache_hit_rate:.2f}%

---

## 📈 Volume & ROI Milestones

"""

        # Append volume tracker section if available
        try:
            if self._last_volume_trend is not None:
                report += RequestVolumeTracker(self.project_id, self.service_name).generate_report(self._last_volume_trend)
            else:
                # Try to load from persisted trend file
                vt = RequestVolumeTracker(self.project_id, self.service_name)
                if vt.trend_file.exists():
                    with open(vt.trend_file, 'r', encoding='utf-8') as f:
                        import json as _json
                        _td = _json.load(f)
                    from dataclasses import asdict
                    # Reconstruct dataclasses for report
                    cs = _td.get("current_snapshot")
                    ps = _td.get("previous_snapshot")
                    from feedback.request_volume_tracker import VolumeSnapshot, VolumeTrend
                    current = VolumeSnapshot(**cs) if cs else None
                    previous = VolumeSnapshot(**ps) if ps else None
                    if current is not None:
                        trend = VolumeTrend(
                            current_snapshot=current,
                            previous_snapshot=previous,
                            daily_growth_rate=_td.get("daily_growth_rate", 0.0),
                            monthly_growth_rate=_td.get("monthly_growth_rate", 0.0),
                            days_to_breakeven=_td.get("days_to_breakeven"),
                            days_to_profitability=_td.get("days_to_profitability"),
                            trend_direction=_td.get("trend_direction", "STABLE"),
                            alert_level=_td.get("alert_level", "NONE"),
                            alert_message=_td.get("alert_message", "")
                        )
                        report += vt.generate_report(trend)
        except Exception as e:
            logger.warning("Failed to append volume section: %s", e)

        report += """

**생성**: Lumen Feedback Orchestrator v1.0
"""
        
        return report


if __name__ == "__main__":
    # Logging 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 프로젝트 ID
    project_id = os.environ.get("GCP_PROJECT_ID", "naeda-genesis")
    service_name = os.environ.get("SERVICE_NAME", "ion-api-canary")
    budget_usd = float(os.environ.get("MONTHLY_BUDGET_USD", "200.0"))
    
    # 오케스트레이터 실행
    orchestrator = FeedbackOrchestrator(project_id, service_name, budget_usd)
    unified_feedback = orchestrator.run_complete_feedback_loop()
    
    # 리포트 생성 및 출력
    report = orchestrator.generate_unified_report(unified_feedback)
    
    # 리포트 파일 저장
    report_file = os.path.join(
        os.path.dirname(__file__),
        "../outputs/unified_feedback_report.md"
    )
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"\nSaved unified report to {report_file}")
    except Exception as e:
        logger.error(f"Failed to save report: {e}")
    
    print("\n" + "=" * 60)
    print(f"System Health: {unified_feedback.system_health.value}")
    print(f"Unified Gate Score: {unified_feedback.unified_gate_score:.2f}/100")
    print(f"Optimization Priority: {unified_feedback.optimization_priority}")
    print("=" * 60)
    
    # Exit code
    if unified_feedback.system_health == SystemHealthLevel.EXCELLENT:
        sys.exit(0)
    elif unified_feedback.system_health == SystemHealthLevel.GOOD:
        sys.exit(0)
    elif unified_feedback.system_health == SystemHealthLevel.WARNING:
        sys.exit(1)
    else:  # CRITICAL
        sys.exit(2)
