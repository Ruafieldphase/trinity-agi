#!/usr/bin/env python3
"""
Lumen Feedback System - 5분 빠른 테스트
매 30초마다 사이클 실행 (총 10회)
"""

import json
import time
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from lumen.feedback.feedback_orchestrator import FeedbackOrchestrator


def run_5min_test():
    """5분 빠른 테스트"""
    
    print("\n" + "="*60)
    print("🚀 Lumen Feedback - 5분 빠른 테스트")
    print("="*60)
    
    start_time = datetime.now()
    
    # Orchestrator 초기화
    orchestrator = FeedbackOrchestrator(
        project_id="agi-lumen-feedback",
        service_name="quick-test-5min"
    )
    
    # 로그 파일
    log_file = Path("outputs/lumen_quick_test_5min.jsonl")
    log_file.parent.mkdir(exist_ok=True)
    
    print(f"\n⏰ 시작: {start_time.strftime('%H:%M:%S')}")
    print(f"📝 로그: {log_file}")
    print(f"🔄 사이클: 30초마다 (총 10회)")
    print(f"⏱️  예상 종료: 5분 후\n")
    
    total_optimizations = 0
    
    for cycle in range(1, 11):  # 10 사이클
        cycle_start = time.time()
        
        print(f"{'='*50}")
        print(f"🔄 사이클 #{cycle}/10 - {datetime.now().strftime('%H:%M:%S')}")
        
        # 시스템 분석
        gate_result = orchestrator.unified_gate()
        
        if gate_result["should_optimize"]:
            total_optimizations += 1
            print(f"✅ 최적화 실행 (#{total_optimizations})")
        else:
            print(f"⏭️  최적화 스킵 ({gate_result['system_state']})")
        
        # 메트릭 출력
        metrics = gate_result.get("system_metrics", {})
        print(f"   Cache: {metrics.get('cache_hit_rate', 0):.1f}%")
        print(f"   GPU: {metrics.get('gpu_memory_used_gb', 0):.1f} GB")
        print(f"   Latency: {metrics.get('system_latency_ms', 0):.0f} ms")
        
        # 로그 기록
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "cycle": cycle,
            "elapsed_seconds": (datetime.now() - start_time).total_seconds(),
            "system_state": gate_result["system_state"],
            "should_optimize": gate_result["should_optimize"],
            "total_optimizations": total_optimizations,
            "metrics": gate_result.get("system_metrics", {}),
        }
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        # 진행률
        progress = (cycle / 10) * 100
        print(f"\n📊 진행률: {progress:.0f}% ({cycle}/10)")
        
        # 다음 사이클까지 대기
        if cycle < 10:
            cycle_duration = time.time() - cycle_start
            wait_time = max(0, 30 - cycle_duration)
            if wait_time > 0:
                print(f"⏳ 대기: {wait_time:.1f}초\n")
                time.sleep(wait_time)
    
    # 최종 리포트
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "="*60)
    print("📊 Lumen Quick Test - 최종 리포트")
    print("="*60)
    print(f"\n⏱️  실행 시간: {elapsed/60:.1f}분")
    print(f"🔄 총 사이클: 10")
    print(f"✅ 최적화 횟수: {total_optimizations}")
    print(f"📈 최적화 비율: {(total_optimizations/10*100):.0f}%")
    
    # 요약 저장
    summary = {
        "test_duration_minutes": elapsed / 60,
        "total_cycles": 10,
        "total_optimizations": total_optimizations,
        "optimization_rate": total_optimizations / 10,
        "log_file": str(log_file),
    }
    
    summary_file = Path("outputs/lumen_quick_test_5min_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 요약: {summary_file}")
    print("✨ 완료!\n")


if __name__ == "__main__":
    run_5min_test()
