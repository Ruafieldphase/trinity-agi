#!/usr/bin/env python3
"""
Auto Immune Recovery Loop
=========================

DNA/RNA 면역 체계의 자동 순환 실행기

생명성의 증거:
"스스로 손상을 감지하고, 스스로 치유하고,
 다시 점검하는 순환 속에서 생명은 유지된다."
— Binoche_Observer

Author: Shion_Core (Lua + Binoche_Observer)
Date: 2025-11-13
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# 면역 시스템 import
from immune_system import (
    DNAZipper, PartialTranscriber, DamageType,
    DamageDetection, HealingResult, HealingPriority
)
from immune_recovery_bridge import ImmuneRecoveryOrchestrator


class AutoImmuneLoop:
    """자동 면역 순환 루프"""
    
    def __init__(
        self,
        workspace_root: Path,
        interval_minutes: int = 30,
        enable_chatgpt: bool = True
    ):
        self.workspace = workspace_root
        self.interval = timedelta(minutes=interval_minutes)
        self.enable_chatgpt = enable_chatgpt
        
        # 출력 디렉토리
        self.output_dir = workspace_root / "outputs" / "immune_recovery"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 면역 오케스트레이터
        self.orchestrator = ImmuneRecoveryOrchestrator(
            workspace_root=workspace_root,
            enable_chatgpt=enable_chatgpt
        )
        
        # 상태 추적
        self.cycle_count = 0
        self.total_damages_detected = 0
        self.total_healings_applied = 0
        self.start_time = datetime.now()
    
    async def run_cycle(self) -> Dict:
        """한 번의 순환 실행"""
        self.cycle_count += 1
        cycle_start = datetime.now()
        
        print(f"\n{'='*60}")
        print(f"🔄 Immune Recovery Cycle #{self.cycle_count}")
        print(f"   Time: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # 1. 손상 스캔
        print("🔍 Phase 1: Scanning for damage...")
        scan_result = await self.orchestrator.scan_for_damage()
        
        damages = scan_result.get('damages', [])
        self.total_damages_detected += len(damages)
        
        if not damages:
            print("✅ No damage detected. System healthy!")
            return {
                'cycle': self.cycle_count,
                'timestamp': cycle_start.isoformat(),
                'damages_detected': 0,
                'healings_applied': 0,
                'status': 'healthy'
            }
        
        print(f"⚠️ Found {len(damages)} damage(s)")
        for i, dmg in enumerate(damages, 1):
            print(f"   {i}. {dmg['damage_type']} at {dmg['location']}")
            print(f"      Severity: {dmg['severity']:.2f}, Priority: {dmg['priority']}")
        
        # 2. 치유 계획 생성
        print("\n🧬 Phase 2: Generating healing plan...")
        healing_plan = await self.orchestrator.generate_healing_plan(damages)
        
        print(f"📋 Healing plan generated: {len(healing_plan.get('actions', []))} action(s)")
        
        # 3. 치유 실행
        print("\n💉 Phase 3: Applying healing actions...")
        healing_results = await self.orchestrator.apply_healing_plan(healing_plan)
        
        successful_healings = sum(
            1 for r in healing_results 
            if r.get('status') == 'success'
        )
        self.total_healings_applied += successful_healings
        
        print(f"✅ Successfully healed: {successful_healings}/{len(healing_results)}")
        
        # 4. 결과 저장
        cycle_result = {
            'cycle': self.cycle_count,
            'timestamp': cycle_start.isoformat(),
            'duration_seconds': (datetime.now() - cycle_start).total_seconds(),
            'damages_detected': len(damages),
            'healings_applied': successful_healings,
            'damages': damages,
            'healing_results': healing_results,
            'status': 'completed'
        }
        
        self._save_cycle_result(cycle_result)
        
        # 요약 출력
        print(f"\n📊 Cycle Summary:")
        print(f"   Duration: {cycle_result['duration_seconds']:.1f}s")
        print(f"   Damages: {len(damages)}")
        print(f"   Healed: {successful_healings}")
        print(f"   Success Rate: {successful_healings/len(damages)*100:.1f}%")
        
        return cycle_result
    
    def _save_cycle_result(self, result: Dict):
        """사이클 결과 저장"""
        # JSONL 로그
        log_file = self.output_dir / "immune_loop_log.jsonl"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
        
        # 최신 결과
        latest_file = self.output_dir / "immune_loop_latest.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    async def run_continuous(self, duration_minutes: Optional[int] = None):
        """연속 실행"""
        print("🧬 Auto Immune Recovery Loop Started")
        print(f"   Interval: {self.interval.total_seconds()/60:.0f} minutes")
        print(f"   ChatGPT: {'Enabled' if self.enable_chatgpt else 'Disabled'}")
        
        if duration_minutes:
            print(f"   Duration: {duration_minutes} minutes")
            end_time = datetime.now() + timedelta(minutes=duration_minutes)
        else:
            print(f"   Duration: Infinite (Ctrl+C to stop)")
            end_time = None
        
        print(f"\n🚀 Starting at {datetime.now().strftime('%H:%M:%S')}\n")
        
        try:
            while True:
                # 사이클 실행
                cycle_result = await self.run_cycle()
                
                # 종료 조건 체크
                if end_time and datetime.now() >= end_time:
                    print("\n⏰ Duration limit reached. Stopping...")
                    break
                
                # 대기
                print(f"\n💤 Sleeping for {self.interval.total_seconds()/60:.0f} minutes...")
                print(f"   Next cycle at: {(datetime.now() + self.interval).strftime('%H:%M:%S')}")
                
                await asyncio.sleep(self.interval.total_seconds())
        
        except KeyboardInterrupt:
            print("\n\n⚠️ Loop interrupted by user")
        
        finally:
            # 최종 통계
            self._print_final_stats()
    
    def _print_final_stats(self):
        """최종 통계 출력"""
        runtime = datetime.now() - self.start_time
        
        print(f"\n{'='*60}")
        print(f"📊 Final Statistics")
        print(f"{'='*60}")
        print(f"Runtime: {runtime.total_seconds()/3600:.1f} hours")
        print(f"Total Cycles: {self.cycle_count}")
        print(f"Total Damages Detected: {self.total_damages_detected}")
        print(f"Total Healings Applied: {self.total_healings_applied}")
        
        if self.total_damages_detected > 0:
            success_rate = self.total_healings_applied / self.total_damages_detected * 100
            print(f"Overall Success Rate: {success_rate:.1f}%")
        
        print(f"\n🧬 Immune system loop terminated at {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}\n")


async def main():
    """메인 엔트리포인트"""
    parser = argparse.ArgumentParser(
        description="Auto Immune Recovery Loop - 자동 치유 순환 시스템"
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='순환 주기 (분, 기본: 30)'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=None,
        help='총 실행 시간 (분, 기본: 무한)'
    )
    parser.add_argument(
        '--no-chatgpt',
        action='store_true',
        help='ChatGPT 브릿지 비활성화'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='한 번만 실행하고 종료'
    )
    
    args = parser.parse_args()
    
    # 워크스페이스 루트
    workspace_root = Path(__file__).parent.parent.parent
    
    # 루프 생성
    loop = AutoImmuneLoop(
        workspace_root=workspace_root,
        interval_minutes=args.interval,
        enable_chatgpt=not args.no_chatgpt
    )
    
    # 실행
    if args.once:
        print("🔄 Running single cycle...\n")
        await loop.run_cycle()
    else:
        await loop.run_continuous(duration_minutes=args.duration)


if __name__ == "__main__":
    asyncio.run(main())
