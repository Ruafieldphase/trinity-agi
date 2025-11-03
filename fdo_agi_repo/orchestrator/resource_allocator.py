"""
Resource Allocator - 자원 분배기

리듬에 따라 시스템 자원을 적응적으로 분배합니다.

생명체 비유:
- NORMAL: 탄수화물 (기본 대사) → 모든 기능 활성화
- BUSY: 단백질 (지속 가능) → 필수 기능만
- EMERGENCY: 전투 모드 → 생존 최우선
- LEARNING: 보충 모드 → 학습 & 최적화
"""

import json
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path
from enum import Enum


class SystemRhythm(Enum):
    """시스템 리듬 모드"""
    NORMAL = "NORMAL"
    BUSY = "BUSY"
    EMERGENCY = "EMERGENCY"
    LEARNING = "LEARNING"


@dataclass
class ResourceBudget:
    """에너지 예산 (각 레이어의 자원 할당)"""
    
    # 메타 정보
    rhythm_mode: str
    timestamp: str
    description: str
    
    # AGI Pipeline 설정
    max_layers: int  # 활성화할 최대 레이어 수
    worker_poll_ms: int  # Worker 폴링 간격 (ms)
    direct_mode: bool  # 큐 우회 모드 (빠른 처리)
    
    # Resonance 설정
    resonance_mode: str  # "disabled" / "observe" / "enforce"
    resonance_policy: str  # "quality-first" / "ops-safety" / "latency-first"
    
    # BQI 학습 설정
    bqi_learning_enabled: bool
    bqi_learning_intensity: float  # 0.0-1.0 (학습 강도)
    
    # 모니터링 설정
    monitoring_enabled: bool
    monitoring_interval_sec: int
    
    # 캐시 설정
    cache_aggressive: bool  # 공격적 캐싱 (EMERGENCY)
    cache_ttl_multiplier: float  # TTL 배수 (1.0 = 기본)
    
    # 레이턴시 목표
    target_latency_sec: float
    max_acceptable_latency_sec: float
    
    # 예산 사용률
    budget_usage_percent: int  # 전체 자원의 몇 %를 사용할지


class ResourceAllocator:
    """자원 분배기"""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.outputs_dir = self.repo_root / "outputs"
        
        # 기본 설정값
        self.defaults = {
            "worker_poll_ms": 100,
            "monitoring_interval_sec": 60,
            "cache_ttl_multiplier": 1.0,
        }
    
    def allocate_for_rhythm(self, rhythm_mode: SystemRhythm, timestamp: str) -> ResourceBudget:
        """리듬에 따른 자원 분배"""
        
        if rhythm_mode == SystemRhythm.EMERGENCY:
            return self._allocate_emergency(timestamp)
        elif rhythm_mode == SystemRhythm.BUSY:
            return self._allocate_busy(timestamp)
        elif rhythm_mode == SystemRhythm.LEARNING:
            return self._allocate_learning(timestamp)
        else:  # NORMAL
            return self._allocate_normal(timestamp)
    
    def _allocate_emergency(self, timestamp: str) -> ResourceBudget:
        """🔴 EMERGENCY 모드 (전투 모드 - 생존 최우선)"""
        return ResourceBudget(
            rhythm_mode="EMERGENCY",
            timestamp=timestamp,
            description="⚠️ EMERGENCY: 모든 에너지를 빠른 처리에 집중",
            
            # AGI Pipeline: 최소한으로 축소
            max_layers=3,  # 필수 레이어만 (예: 입력 검증, 핵심 처리, 출력)
            worker_poll_ms=10,  # 매우 빠른 폴링 (10ms)
            direct_mode=True,  # 큐 우회! (Direct execution)
            
            # Resonance: 비활성화 (검증 스킵)
            resonance_mode="disabled",
            resonance_policy="latency-first",  # 사용 안 함
            
            # BQI: 학습 중지
            bqi_learning_enabled=False,
            bqi_learning_intensity=0.0,
            
            # 모니터링: 최소화
            monitoring_enabled=False,
            monitoring_interval_sec=300,  # 5분 (거의 안 함)
            
            # 캐시: 공격적 사용
            cache_aggressive=True,
            cache_ttl_multiplier=2.0,  # TTL 2배 (더 오래 캐싱)
            
            # 레이턴시: 극단적 최적화
            target_latency_sec=1.0,
            max_acceptable_latency_sec=1.5,
            
            # 예산: 30% (생존 최우선)
            budget_usage_percent=30
        )
    
    def _allocate_busy(self, timestamp: str) -> ResourceBudget:
        """🟡 BUSY 모드 (단백질 모드 - 지속 가능)"""
        return ResourceBudget(
            rhythm_mode="BUSY",
            timestamp=timestamp,
            description="⚡ BUSY: 필수 기능만 활성화하여 효율 유지",
            
            # AGI Pipeline: 필수 기능만
            max_layers=5,  # 필수 + 일부 옵션
            worker_poll_ms=50,  # 빠른 폴링 (50ms)
            direct_mode=False,  # 큐 사용 (안정성 유지)
            
            # Resonance: 빠른 검증만
            resonance_mode="enforce",
            resonance_policy="ops-safety",  # 안전성 중심
            
            # BQI: 학습 일시 중지
            bqi_learning_enabled=False,
            bqi_learning_intensity=0.0,
            
            # 모니터링: 경량화
            monitoring_enabled=False,
            monitoring_interval_sec=180,  # 3분
            
            # 캐시: 일반 사용
            cache_aggressive=True,
            cache_ttl_multiplier=1.5,  # TTL 1.5배
            
            # 레이턴시: 빠르게
            target_latency_sec=2.5,
            max_acceptable_latency_sec=3.0,
            
            # 예산: 70% (효율 중심)
            budget_usage_percent=70
        )
    
    def _allocate_learning(self, timestamp: str) -> ResourceBudget:
        """🔵 LEARNING 모드 (보충 모드 - 학습 & 최적화)"""
        return ResourceBudget(
            rhythm_mode="LEARNING",
            timestamp=timestamp,
            description="🌙 LEARNING: 휴식 시간에 학습 & 최적화 강화",
            
            # AGI Pipeline: 정상 처리
            max_layers=10,  # 모든 레이어
            worker_poll_ms=200,  # 느린 폴링 (200ms) - 배터리 절약
            direct_mode=False,
            
            # Resonance: 관찰 모드
            resonance_mode="observe",
            resonance_policy="quality-first",  # 품질 중심
            
            # BQI: 학습 강화!
            bqi_learning_enabled=True,
            bqi_learning_intensity=1.0,  # 최대 강도
            
            # 모니터링: 활성화
            monitoring_enabled=True,
            monitoring_interval_sec=60,
            
            # 캐시: 일반 사용
            cache_aggressive=False,
            cache_ttl_multiplier=1.0,  # 기본 TTL
            
            # 레이턴시: 여유롭게 (학습 오버헤드 허용)
            target_latency_sec=4.0,
            max_acceptable_latency_sec=4.5,
            
            # 예산: 120% (내일을 위한 투자)
            budget_usage_percent=120
        )
    
    def _allocate_normal(self, timestamp: str) -> ResourceBudget:
        """🟢 NORMAL 모드 (탄수화물 모드 - 기본 대사)"""
        return ResourceBudget(
            rhythm_mode="NORMAL",
            timestamp=timestamp,
            description="✅ NORMAL: 모든 기능 활성화, 안정적 운영",
            
            # AGI Pipeline: 모든 기능
            max_layers=10,
            worker_poll_ms=100,  # 기본 폴링
            direct_mode=False,
            
            # Resonance: 관찰 모드
            resonance_mode="observe",
            resonance_policy="quality-first",
            
            # BQI: 학습 활성화
            bqi_learning_enabled=True,
            bqi_learning_intensity=0.5,  # 중간 강도
            
            # 모니터링: 활성화
            monitoring_enabled=True,
            monitoring_interval_sec=60,
            
            # 캐시: 일반 사용
            cache_aggressive=False,
            cache_ttl_multiplier=1.0,
            
            # 레이턴시: 정상
            target_latency_sec=3.5,
            max_acceptable_latency_sec=4.0,
            
            # 예산: 100% (기본 대사)
            budget_usage_percent=100
        )
    
    def save_budget(self, budget: ResourceBudget):
        """예산 저장"""
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. 최신 예산 (덮어쓰기)
        latest_file = self.outputs_dir / "resource_budget_latest.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(budget), f, indent=2, ensure_ascii=False)
        
        # 2. 히스토리 (추가)
        history_file = self.outputs_dir / "resource_budget_history.jsonl"
        with open(history_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(budget), ensure_ascii=False) + '\n')
        
        print(f"✅ Budget saved: {latest_file}")


def main():
    """테스트 실행"""
    import argparse
    from datetime import datetime, timezone
    
    parser = argparse.ArgumentParser(description="Resource Allocator - 자원 분배기")
    parser.add_argument("--mode", choices=["NORMAL", "BUSY", "EMERGENCY", "LEARNING"],
                       default="NORMAL", help="리듬 모드")
    parser.add_argument("--save", action="store_true", help="예산 저장")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    args = parser.parse_args()
    
    allocator = ResourceAllocator()
    rhythm_mode = SystemRhythm[args.mode]
    timestamp = datetime.now(timezone.utc).isoformat()
    
    budget = allocator.allocate_for_rhythm(rhythm_mode, timestamp)
    
    if args.save:
        allocator.save_budget(budget)
    
    if args.json:
        print(json.dumps(asdict(budget), indent=2, ensure_ascii=False))
    else:
        # 예쁘게 출력
        print(f"\n{'=' * 70}")
        print(f"💰 Resource Budget Allocation")
        print(f"{'=' * 70}\n")
        print(f"Mode:        {budget.rhythm_mode}")
        print(f"Description: {budget.description}")
        print(f"\n📊 AGI Pipeline:")
        print(f"  Max Layers:      {budget.max_layers}")
        print(f"  Worker Poll:     {budget.worker_poll_ms}ms")
        print(f"  Direct Mode:     {'✅ YES' if budget.direct_mode else '❌ NO'}")
        print(f"\n🎭 Resonance:")
        print(f"  Mode:            {budget.resonance_mode}")
        print(f"  Policy:          {budget.resonance_policy}")
        print(f"\n🧠 BQI Learning:")
        print(f"  Enabled:         {'✅ YES' if budget.bqi_learning_enabled else '❌ NO'}")
        print(f"  Intensity:       {budget.bqi_learning_intensity:.0%}")
        print(f"\n📈 Monitoring:")
        print(f"  Enabled:         {'✅ YES' if budget.monitoring_enabled else '❌ NO'}")
        print(f"  Interval:        {budget.monitoring_interval_sec}s")
        print(f"\n💾 Cache:")
        print(f"  Aggressive:      {'✅ YES' if budget.cache_aggressive else '❌ NO'}")
        print(f"  TTL Multiplier:  {budget.cache_ttl_multiplier}x")
        print(f"\n⏱️ Latency:")
        print(f"  Target:          {budget.target_latency_sec}s")
        print(f"  Max Acceptable:  {budget.max_acceptable_latency_sec}s")
        print(f"\n💰 Budget:")
        print(f"  Usage:           {budget.budget_usage_percent}%")
        print(f"\nTimestamp: {budget.timestamp}")
        print()


if __name__ == "__main__":
    main()
