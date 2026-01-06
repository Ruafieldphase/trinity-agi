#!/usr/bin/env python3
"""
Orchestration Bridge v1.0
모니터링 메트릭을 오케스트레이션 의사결정에 연결하는 브리지 모듈

역할:
  1. 모니터링 메트릭 읽기 (JSON)
  2. 채널 건강도 평가
  3. 라우팅 우선순위 제공
  4. 자동 복구 트리거 판단
  5. 오케스트레이터에게 실시간 컨텍스트 제공

연동 대상:
  - LLM_Unified/ion-mentoring/Core/feedback/feedback_orchestrator.py
  - LLM_Unified/ion-mentoring/orchestrator/intent_router.py
  - fdo_agi_repo/scripts/auto_recover.py
  - scripts/quick_status.ps1 (via JSON)
"""

import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
from workspace_root import get_workspace_root

# Suppress logging to stderr when running as CLI (only output JSON to stdout)
if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
else:
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChannelHealth(Enum):
    """채널 건강 상태"""
    EXCELLENT = "EXCELLENT"  # 100% 가용, 레이턴시 낮음
    GOOD = "GOOD"           # 95%+ 가용
    DEGRADED = "DEGRADED"   # 90%+ 가용, 레이턴시 높거나 스파이크
    POOR = "POOR"           # <90% 가용 또는 심각한 지연
    OFFLINE = "OFFLINE"     # 0% 가용


class RoutingPriority(Enum):
    """라우팅 우선순위"""
    HIGHEST = 1  # 가장 빠르고 안정적
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    AVOID = 5    # 가능하면 회피


@dataclass
class ChannelStatus:
    """채널 상태 요약"""
    name: str
    health: ChannelHealth
    availability: float  # 백분율
    mean_latency_ms: float
    p95_latency_ms: float
    trend_direction: str  # IMPROVING, STABLE, DEGRADING
    baseline_alerts: int
    adaptive_alerts: int
    spikes: int
    routing_priority: RoutingPriority
    optional: bool = False  # Optional 채널 여부


@dataclass
@dataclass
class OrchestrationContext:
    """오케스트레이션 컨텍스트"""
    timestamp: str
    overall_health: str
    effective_availability: float
    channels: Dict[str, 'ChannelStatus']
    recommended_primary: str
    recommended_fallback: str
    recovery_needed: bool
    recovery_reason: Optional[str]
    monitoring_metrics_path: str
    
    def to_dict(self) -> dict:
        """JSON 직렬화용 딕셔너리 변환"""
        return {
            "timestamp": self.timestamp,
            "overall_health": self.overall_health,
            "effective_availability": self.effective_availability,
            "channels": [
                {
                    "name": name,
                    "health": ch.health.value,
                    "availability": ch.availability,
                    "mean_latency_ms": ch.mean_latency_ms,
                    "routing_priority": ch.routing_priority.value,
                    "optional": ch.optional
                }
                for name, ch in self.channels.items()
            ],
            "routing": {
                "recommended_primary": self.recommended_primary,
                "recommended_fallback": self.recommended_fallback,
                "fallback_channels": [
                    name for name, ch in self.channels.items()
                    if ch.health in [ChannelHealth.EXCELLENT, ChannelHealth.GOOD]
                    and name != self.recommended_primary
                ]
            },
            "recovery": {
                "should_trigger": self.recovery_needed,
                "reason": self.recovery_reason or "",
                "recommended_actions": ["restart_worker", "check_gateway"] if self.recovery_needed else []
            }
        }


class OrchestrationBridge:
    """모니터링 → 오케스트레이션 브리지"""

    def __init__(self, workspace_root: Optional[str] = None):
        """
        Args:
            workspace_root: 워크스페이스 루트 (None이면 자동 감지)
        """
        if workspace_root is None:
            # 스크립트 위치에서 워크스페이스 루트 찾기
            workspace_root_path = get_workspace_root()
        else:
            workspace_root_path = Path(workspace_root)
        
        self.workspace_root = workspace_root_path
        self.metrics_path = self.workspace_root / "outputs" / "monitoring_metrics_latest.json"
        logger.info(f"OrchestrationBridge initialized. Metrics path: {self.metrics_path}")

    def get_orchestration_context(self) -> OrchestrationContext:
        """
        현재 모니터링 상태를 읽어 오케스트레이션 컨텍스트 생성

        Returns:
            OrchestrationContext: 의사결정에 필요한 전체 컨텍스트
        """
        if not self.metrics_path.exists():
            logger.warning(f"Metrics file not found: {self.metrics_path}")
            return self._get_fallback_context()

        try:
            with open(self.metrics_path, 'r', encoding='utf-8-sig') as f:
                metrics = json.load(f)
            
            logger.info(f"Loaded monitoring metrics from: {self.metrics_path}")
            return self._build_context_from_metrics(metrics)
        
        except Exception as e:
            logger.error(f"Failed to load metrics: {e}")
            return self._get_fallback_context()

    def _build_context_from_metrics(self, metrics: dict) -> OrchestrationContext:
        """메트릭 데이터로부터 컨텍스트 생성"""
        timestamp = metrics.get("Timestamp", datetime.now().isoformat())
        overall_health = metrics.get("OverallHealth", "UNKNOWN")
        effective_avail = metrics.get("EffectiveAvailability", 0.0)

        # 채널 상태 분석
        channels = {}
        channel_data = metrics.get("Channels", {})
        
        for channel_key, channel_metrics in channel_data.items():
            status = self._evaluate_channel(channel_key, channel_metrics, optional=False)
            channels[channel_key] = status

        # Optional 채널 (있으면 추가)
        optional_channels = metrics.get("OptionalChannels", {})
        for channel_key, channel_metrics in optional_channels.items():
            status = self._evaluate_channel(channel_key, channel_metrics, optional=True)
            channels[channel_key] = status

        # 라우팅 추천
        primary, fallback = self._recommend_routing(channels)

        # 복구 필요 여부
        recovery_needed, recovery_reason = self._check_recovery_needed(channels, overall_health)

        return OrchestrationContext(
            timestamp=timestamp,
            overall_health=overall_health,
            effective_availability=effective_avail,
            channels=channels,
            recommended_primary=primary,
            recommended_fallback=fallback,
            recovery_needed=recovery_needed,
            recovery_reason=recovery_reason,
            monitoring_metrics_path=str(self.metrics_path)
        )

    def _evaluate_channel(self, name: str, metrics: dict, optional: bool) -> ChannelStatus:
        """채널 건강도 및 라우팅 우선순위 평가"""
        availability = metrics.get("Availability", 0.0)
        mean_latency = metrics.get("Mean", 999.0)
        p95_latency = metrics.get("P95", 999.0)
        trend = metrics.get("Trend", {})
        trend_direction = trend.get("Direction", "STABLE")
        
        baseline_alerts = metrics.get("BaselineAlerts", 0)
        adaptive_alerts = metrics.get("AdaptiveAlerts", 0)
        spikes = metrics.get("Spikes", 0)

        # 건강도 판정
        if availability == 0:
            health = ChannelHealth.OFFLINE
        elif availability >= 99 and mean_latency < 100 and baseline_alerts == 0:
            health = ChannelHealth.EXCELLENT
        elif availability >= 95 and mean_latency < 200:
            health = ChannelHealth.GOOD
        elif availability >= 90:
            health = ChannelHealth.DEGRADED
        else:
            health = ChannelHealth.POOR

        # 라우팅 우선순위 (낮을수록 우선)
        if health == ChannelHealth.EXCELLENT and trend_direction == "IMPROVING":
            priority = RoutingPriority.HIGHEST
        elif health == ChannelHealth.EXCELLENT or health == ChannelHealth.GOOD:
            priority = RoutingPriority.HIGH
        elif health == ChannelHealth.DEGRADED:
            priority = RoutingPriority.MEDIUM
        elif health == ChannelHealth.POOR:
            priority = RoutingPriority.LOW
        else:  # OFFLINE
            priority = RoutingPriority.AVOID

        # Optional 채널은 우선순위 하향
        if optional and priority.value < RoutingPriority.LOW.value:
            priority = RoutingPriority(priority.value + 1)

        return ChannelStatus(
            name=name,
            health=health,
            availability=availability,
            mean_latency_ms=mean_latency,
            p95_latency_ms=p95_latency,
            trend_direction=trend_direction,
            baseline_alerts=baseline_alerts,
            adaptive_alerts=adaptive_alerts,
            spikes=spikes,
            routing_priority=priority,
            optional=optional
        )

    def _recommend_routing(self, channels: Dict[str, ChannelStatus]) -> tuple[str, str]:
        """
        최적 라우팅 추천
        
        Returns:
            (primary_channel, fallback_channel)
        """
        # Optional 채널 제외하고 정렬
        core_channels = {k: v for k, v in channels.items() if not v.optional}
        
        if not core_channels:
            return ("Cloud", "Gateway")  # 기본값

        # 우선순위로 정렬
        sorted_channels = sorted(
            core_channels.items(),
            key=lambda x: (x[1].routing_priority.value, x[1].mean_latency_ms)
        )

        primary = sorted_channels[0][0]
        fallback = sorted_channels[1][0] if len(sorted_channels) > 1 else sorted_channels[0][0]

        logger.info(f"Routing recommendation: Primary={primary}, Fallback={fallback}")
        return (primary, fallback)

    def _check_recovery_needed(
        self,
        channels: Dict[str, ChannelStatus],
        overall_health: str
    ) -> tuple[bool, Optional[str]]:
        """
        자동 복구 필요 여부 판단

        Returns:
            (recovery_needed, reason)
        """
        # 전체 건강도가 DEGRADED 이하
        if overall_health in ["DEGRADED", "POOR", "CRITICAL"]:
            return (True, f"Overall health is {overall_health}")

        # 2개 이상 채널이 POOR 이하
        poor_count = sum(
            1 for ch in channels.values()
            if ch.health in [ChannelHealth.POOR, ChannelHealth.OFFLINE] and not ch.optional
        )
        if poor_count >= 2:
            return (True, f"{poor_count} channels are POOR or OFFLINE")

        # Primary 추천 채널이 DEGRADED 이하
        primary, _ = self._recommend_routing(channels)
        if primary in channels:
            primary_health = channels[primary].health
            if primary_health.value in ["DEGRADED", "POOR", "OFFLINE"]:
                return (True, f"Primary channel {primary} is {primary_health.value}")

        return (False, None)

    def _get_fallback_context(self) -> OrchestrationContext:
        """메트릭 파일 없을 때 fallback 컨텍스트"""
        logger.warning("Using fallback orchestration context")
        return OrchestrationContext(
            timestamp=datetime.now().isoformat(),
            overall_health="UNKNOWN",
            effective_availability=0.0,
            channels={},
            recommended_primary="Cloud",
            recommended_fallback="Gateway",
            recovery_needed=False,
            recovery_reason=None,
            monitoring_metrics_path=str(self.metrics_path)
        )

    def get_channel_latency_map(self) -> Dict[str, float]:
        """
        채널별 평균 레이턴시 맵 반환 (라우터에서 사용)
        
        Returns:
            {"Local": 25.5, "Cloud": 270.0, "Gateway": 218.0}
        """
        context = self.get_orchestration_context()
        return {
            name: ch.mean_latency_ms
            for name, ch in context.channels.items()
            if not ch.optional
        }

    def should_trigger_recovery(self) -> tuple[bool, Optional[str]]:
        """
        자동 복구 트리거 여부 (auto_recover.py에서 호출)
        
        Returns:
            (should_recover, reason)
        """
        context = self.get_orchestration_context()
        return (context.recovery_needed, context.recovery_reason)

    def export_orchestration_state(self, output_path: Optional[str] = None) -> str:
        """
        오케스트레이션 상태를 JSON으로 내보내기
        
        Args:
            output_path: 출력 경로 (None이면 자동)
        
        Returns:
            저장된 파일 경로
        """
        output_path_obj: Path
        if output_path is None:
            output_path_obj = self.workspace_root / "outputs" / "orchestration_context_latest.json"
        else:
            output_path_obj = Path(output_path)

        context = self.get_orchestration_context()

        # dataclass → dict 변환
        data = {
            "timestamp": context.timestamp,
            "overall_health": context.overall_health,
            "effective_availability": context.effective_availability,
            "channels": {
                name: {
                    "name": ch.name,
                    "health": ch.health.value,
                    "availability": ch.availability,
                    "mean_latency_ms": ch.mean_latency_ms,
                    "p95_latency_ms": ch.p95_latency_ms,
                    "trend_direction": ch.trend_direction,
                    "baseline_alerts": ch.baseline_alerts,
                    "adaptive_alerts": ch.adaptive_alerts,
                    "spikes": ch.spikes,
                    "routing_priority": ch.routing_priority.value,
                    "optional": ch.optional
                }
                for name, ch in context.channels.items()
            },
            "routing": {
                "recommended_primary": context.recommended_primary,
                "recommended_fallback": context.recommended_fallback
            },
            "recovery": {
                "needed": context.recovery_needed,
                "reason": context.recovery_reason
            },
            "monitoring_metrics_path": context.monitoring_metrics_path
        }

        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path_obj, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Orchestration context exported to: {output_path_obj}")
        return str(output_path_obj)


def main():
    """CLI 테스트"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Orchestration Bridge CLI")
    parser.add_argument("--export", action="store_true", help="Export orchestration context to JSON")
    parser.add_argument("--check-recovery", action="store_true", help="Check if recovery needed")
    parser.add_argument("--routing", action="store_true", help="Show routing recommendations")
    parser.add_argument("--latency-map", action="store_true", help="Show channel latency map")
    
    args = parser.parse_args()
    
    bridge = OrchestrationBridge()
    
    if args.export:
        path = bridge.export_orchestration_state()
        print(f"✅ Orchestration context exported to: {path}")
    
    elif args.check_recovery:
        needed, reason = bridge.should_trigger_recovery()
        if needed:
            print(f"🔴 Recovery needed: {reason}", file=sys.stderr)
        else:
            print("✅ No recovery needed", file=sys.stderr)
    
    elif args.routing:
        context = bridge.get_orchestration_context()
        print(f"🎯 Routing Recommendations:", file=sys.stderr)
        print(f"  Primary: {context.recommended_primary}", file=sys.stderr)
        print(f"  Fallback: {context.recommended_fallback}", file=sys.stderr)
    
    elif args.latency_map:
        latency_map = bridge.get_channel_latency_map()
        print("📊 Channel Latency Map:", file=sys.stderr)
        for channel, latency in sorted(latency_map.items(), key=lambda x: x[1]):
            print(f"  {channel:10s}: {latency:6.1f} ms", file=sys.stderr)
    
    else:
        # 기본: JSON 출력 (stdout), 사람이 읽을 수 있는 요약은 stderr로
        context = bridge.get_orchestration_context()
        
        # Human-readable summary to stderr
        print(f"\n🎯 Orchestration Context", file=sys.stderr)
        print(f"=" * 60, file=sys.stderr)
        print(f"Timestamp: {context.timestamp}", file=sys.stderr)
        print(f"Overall Health: {context.overall_health}", file=sys.stderr)
        print(f"Effective Availability: {context.effective_availability:.2f}%", file=sys.stderr)
        print(f"\nChannels:", file=sys.stderr)
        for name, ch in context.channels.items():
            opt_badge = " [OPTIONAL]" if ch.optional else ""
            print(f"  {name:10s}{opt_badge}: {ch.health.value:10s} | "
                  f"{ch.availability:5.1f}% | {ch.mean_latency_ms:6.1f}ms | "
                  f"Priority={ch.routing_priority.value}", file=sys.stderr)
        print(f"\nRouting:", file=sys.stderr)
        print(f"  Primary: {context.recommended_primary}", file=sys.stderr)
        print(f"  Fallback: {context.recommended_fallback}", file=sys.stderr)
        print(f"\nRecovery:", file=sys.stderr)
        if context.recovery_needed:
            print(f"  🔴 Needed: {context.recovery_reason}", file=sys.stderr)
        else:
            print(f"  ✅ Not needed", file=sys.stderr)
        
        # JSON to stdout for parsing
        print(json.dumps(context.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
