#!/usr/bin/env python3
"""
Monitoring-Driven Router v1.0
모니터링 메트릭 기반 인텔리전트 라우팅

역할:
  1. 채널 건강도 기반 라우팅 우선순위 제공
  2. 레이턴시 기반 최적 채널 선택
  3. Fallback 체인 자동 생성
  4. 라우팅 결정 로그

연동:
  - scripts/orchestration_bridge.py (모니터링 컨텍스트)
  - LLM_Unified/ion-mentoring/orchestrator/intent_router.py (의도 파싱)
"""

import logging
from typing import List, Optional, Tuple

from orchestration_bridge import OrchestrationBridge, ChannelHealth, RoutingPriority

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MonitoringRouter:
    """모니터링 기반 인텔리전트 라우팅"""
    
    def __init__(self, workspace_root: Optional[str] = None):
        """
        Args:
            workspace_root: 워크스페이스 루트 (None이면 자동)
        """
        self.bridge = OrchestrationBridge(workspace_root=workspace_root)
        logger.info("MonitoringRouter initialized")
    
    def get_best_channel(self, exclude: Optional[List[str]] = None) -> Tuple[str, str]:
        """
        최적 채널 선택
        
        Args:
            exclude: 제외할 채널 리스트 (예: ["Local"])
        
        Returns:
            (channel_name, reason)
        """
        exclude = exclude or []
        context = self.bridge.get_orchestration_context()
        
        # Optional 채널 제외 & exclude 리스트 반영
        available = {
            name: ch for name, ch in context.channels.items()
            if not ch.optional and name not in exclude
        }
        
        if not available:
            logger.warning("No available channels after filtering")
            return ("Cloud", "Default fallback (no available channels)")
        
        # 우선순위 정렬
        sorted_channels = sorted(
            available.items(),
            key=lambda x: (x[1].routing_priority.value, x[1].mean_latency_ms)
        )
        
        best_name, best_ch = sorted_channels[0]
        
        reason = (
            f"{best_ch.health.value} health, "
            f"{best_ch.mean_latency_ms:.0f}ms latency, "
            f"{best_ch.availability:.1f}% availability"
        )
        
        logger.info(f"Best channel selected: {best_name} ({reason})")
        return (best_name, reason)
    
    def get_fallback_chain(self, max_depth: int = 3) -> List[str]:
        """
        Fallback 체인 생성 (우선순위 순)
        
        Args:
            max_depth: 최대 fallback 깊이
        
        Returns:
            ["Gateway", "Cloud", "Local"]
        """
        context = self.bridge.get_orchestration_context()
        
        # Optional 제외하고 우선순위 정렬
        core_channels = {k: v for k, v in context.channels.items() if not v.optional}
        sorted_channels = sorted(
            core_channels.items(),
            key=lambda x: (x[1].routing_priority.value, x[1].mean_latency_ms)
        )
        
        chain = [name for name, _ in sorted_channels[:max_depth]]
        logger.info(f"Fallback chain: {' → '.join(chain)}")
        return chain
    
    def should_avoid_channel(self, channel_name: str) -> Tuple[bool, Optional[str]]:
        """
        특정 채널을 회피해야 하는지 판단
        
        Args:
            channel_name: 확인할 채널
        
        Returns:
            (should_avoid, reason)
        """
        context = self.bridge.get_orchestration_context()
        
        if channel_name not in context.channels:
            return (False, None)
        
        ch = context.channels[channel_name]
        
        # AVOID 우선순위 = 회피
        if ch.routing_priority == RoutingPriority.AVOID:
            return (True, f"{ch.health.value} health")
        
        # OFFLINE = 회피
        if ch.health == ChannelHealth.OFFLINE:
            return (True, "Channel is OFFLINE")
        
        # POOR + 스파이크 많음 = 회피
        if ch.health == ChannelHealth.POOR and ch.spikes > 5:
            return (True, f"POOR health with {ch.spikes} spikes")
        
        return (False, None)
    
    def get_routing_decision(
        self,
        intent: str,
        exclude: Optional[List[str]] = None
    ) -> dict:
        """
        의도 기반 라우팅 결정 (종합)
        
        Args:
            intent: 사용자 의도 (예: "빠른 응답 필요", "안정성 우선")
            exclude: 제외 채널
        
        Returns:
            {
                "primary": "Gateway",
                "fallback_chain": ["Cloud", "Local"],
                "reason": "...",
                "recovery_needed": False
            }
        """
        intent_lower = intent.lower()
        
        # 의도 파싱
        prefer_speed = any(k in intent_lower for k in ["빠른", "fast", "quick", "latency"])
        prefer_stability = any(k in intent_lower for k in ["안정", "stable", "reliable"])
        
        context = self.bridge.get_orchestration_context()
        
        # Primary 선택
        if prefer_speed:
            # 레이턴시 기준으로 선택
            latency_map = self.bridge.get_channel_latency_map()
            exclude_set = set(exclude or [])
            filtered = {k: v for k, v in latency_map.items() if k not in exclude_set}
            if filtered:
                primary = min(filtered, key=lambda k: filtered[k])
                reason = f"Fastest channel ({latency_map[primary]:.0f}ms)"
            else:
                primary, reason = self.get_best_channel(exclude=exclude)
        
        elif prefer_stability:
            # 가용성 기준으로 선택
            available = {
                name: ch for name, ch in context.channels.items()
                if not ch.optional and name not in (exclude or [])
            }
            if available:
                primary = max(available, key=lambda k: available[k].availability)
                reason = f"Most available ({available[primary].availability:.1f}%)"
            else:
                primary, reason = self.get_best_channel(exclude=exclude)
        
        else:
            # 기본: 종합 우선순위
            primary, reason = self.get_best_channel(exclude=exclude)
        
        # Fallback chain
        fallback_chain = [ch for ch in self.get_fallback_chain() if ch != primary]
        
        return {
            "primary": primary,
            "fallback_chain": fallback_chain,
            "reason": reason,
            "recovery_needed": context.recovery_needed,
            "recovery_reason": context.recovery_reason,
            "monitoring_timestamp": context.timestamp
        }


def main():
    """CLI 테스트"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitoring-Driven Router CLI")
    parser.add_argument("--best", action="store_true", help="Show best channel")
    parser.add_argument("--chain", action="store_true", help="Show fallback chain")
    parser.add_argument("--avoid", type=str, help="Check if channel should be avoided (e.g., 'Local')")
    parser.add_argument("--decide", type=str, help="Get routing decision for intent (e.g., '빠른 응답 필요')")
    parser.add_argument("--exclude", type=str, help="Comma-separated channels to exclude")
    
    args = parser.parse_args()
    
    router = MonitoringRouter()
    exclude_list = args.exclude.split(",") if args.exclude else None
    
    if args.best:
        channel, reason = router.get_best_channel(exclude=exclude_list)
        print(f"🎯 Best Channel: {channel}")
        print(f"   Reason: {reason}")
    
    elif args.chain:
        chain = router.get_fallback_chain()
        print(f"🔗 Fallback Chain: {' → '.join(chain)}")
    
    elif args.avoid:
        should_avoid, reason = router.should_avoid_channel(args.avoid)
        if should_avoid:
            print(f"❌ Avoid {args.avoid}: {reason}")
        else:
            print(f"✅ {args.avoid} is usable")
    
    elif args.decide:
        decision = router.get_routing_decision(args.decide, exclude=exclude_list)
        print(f"\n🎯 Routing Decision")
        print(f"=" * 60)
        print(f"Intent: {args.decide}")
        print(f"Primary: {decision['primary']}")
        print(f"Fallback Chain: {' → '.join(decision['fallback_chain'])}")
        print(f"Reason: {decision['reason']}")
        if decision['recovery_needed']:
            print(f"⚠️  Recovery Needed: {decision['recovery_reason']}")
        print(f"\nMonitoring Timestamp: {decision['monitoring_timestamp']}")
    
    else:
        # 기본: 전체 출력
        channel, reason = router.get_best_channel(exclude=exclude_list)
        chain = router.get_fallback_chain()
        
        print(f"\n🎯 Monitoring Router Status")
        print(f"=" * 60)
        print(f"Best Channel: {channel}")
        print(f"  Reason: {reason}")
        print(f"\nFallback Chain: {' → '.join(chain)}")


if __name__ == "__main__":
    main()
