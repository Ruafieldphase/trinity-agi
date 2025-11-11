#!/usr/bin/env python3
"""
Lumen Feedback System - 24시간 Production 실행
실시간 최적화 + 성능 추적
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys

# AGI 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from lumen.feedback.feedback_orchestrator import FeedbackOrchestrator


async def run_24h_production():
    """24시간 Production 실행"""
    
    print("\n" + "="*60)
    print("🚀 Lumen Feedback System - 24시간 Production")
    print("="*60)
    
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=24)
    
    print(f"\n⏰ 시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏰ 종료 예정: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Orchestrator 초기화
    orchestrator = FeedbackOrchestrator(
        project_id="agi-lumen-feedback",
        service_name="production-24h"
    )
    
    # 로그 파일 설정
    log_file = Path("outputs/lumen_production_24h.jsonl")
    log_file.parent.mkdir(exist_ok=True)
    
    print(f"\n📝 로그: {log_file}")
    print(f"\n🔄 학습 사이클: 5분마다 (총 288회)")
    print(f"📊 예상 최적화 액션: 50-100회")
    
    cycle_count = 0
    total_optimizations = 0
    
    try:
        while datetime.now() < end_time:
            cycle_count += 1
            cycle_start = time.time()
            
            print(f"\n{'='*50}")
            print(f"🔄 사이클 #{cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
            
            # 시스템 상태 분석
            gate_result = orchestrator.unified_gate()
            
            # 최적화 실행 여부
            if gate_result["should_optimize"]:
                total_optimizations += 1
                print(f"✅ 최적화 실행 (#{total_optimizations})")
            else:
                print(f"⏭️  최적화 스킵 (상태: {gate_result['system_state']})")
            
            # 로그 기록
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "cycle": cycle_count,
                "elapsed_hours": (datetime.now() - start_time).total_seconds() / 3600,
                "system_state": gate_result["system_state"],
                "should_optimize": gate_result["should_optimize"],
                "total_optimizations": total_optimizations,
                "cache_health": gate_result.get("cache_health", {}),
                "system_metrics": gate_result.get("system_metrics", {}),
            }
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
            # 주요 메트릭 출력
            metrics = gate_result.get("system_metrics", {})
            print(f"   Cache Hit Rate: {metrics.get('cache_hit_rate', 0):.1f}%")
            print(f"   GPU Memory: {metrics.get('gpu_memory_used_gb', 0):.1f} GB")
            print(f"   System Latency: {metrics.get('system_latency_ms', 0):.0f} ms")
            
            # 진행률 표시
            elapsed = datetime.now() - start_time
            progress = (elapsed.total_seconds() / (24 * 3600)) * 100
            print(f"\n📊 진행률: {progress:.1f}% ({elapsed.total_seconds()/3600:.1f}h / 24h)")
            print(f"   최적화 횟수: {total_optimizations}")
            
            # 다음 사이클까지 대기 (5분)
            cycle_duration = time.time() - cycle_start
            wait_time = max(0, 300 - cycle_duration)  # 5분 = 300초
            
            if wait_time > 0:
                remaining = end_time - datetime.now()
                if remaining.total_seconds() < wait_time:
                    wait_time = max(0, remaining.total_seconds())
                
                if wait_time > 0:
                    print(f"\n⏳ 다음 사이클까지 대기: {wait_time:.0f}초")
                    await asyncio.sleep(wait_time)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자 중단")
    
    finally:
        # 최종 리포트
        elapsed = datetime.now() - start_time
        
        print("\n" + "="*60)
        print("📊 Lumen Production 24h - 최종 리포트")
        print("="*60)
        print(f"\n⏱️  실행 시간: {elapsed.total_seconds()/3600:.1f}시간")
        print(f"🔄 총 사이클: {cycle_count}")
        print(f"✅ 최적화 횟수: {total_optimizations}")
        print(f"📈 최적화 비율: {(total_optimizations/cycle_count*100):.1f}%")
        
        # 요약 저장
        summary_file = Path("outputs/lumen_production_24h_summary.json")
        summary = {
            "start_time": start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_hours": elapsed.total_seconds() / 3600,
            "total_cycles": cycle_count,
            "total_optimizations": total_optimizations,
            "optimization_rate": total_optimizations / cycle_count if cycle_count > 0 else 0,
            "log_file": str(log_file),
        }
        
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 요약 저장: {summary_file}")
        print("\n✨ 완료!\n")


if __name__ == "__main__":
    asyncio.run(run_24h_production())
