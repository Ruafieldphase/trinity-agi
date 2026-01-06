#!/usr/bin/env python3
"""
Thesis 페르소나 내부 병목 분석
RAG 호출 vs LLM 호출 시간 측정
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from workspace_root import get_workspace_root

# Add parent directory to path
sys.path.insert(0, str(get_workspace_root()))

def analyze_thesis_breakdown(hours: int = 24):
    """Ledger에서 Thesis 관련 이벤트만 추출하여 병목 분석"""
    ledger_path = get_workspace_root() / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
    
    if not ledger_path.exists():
        print(f"❌ Ledger not found: {ledger_path}")
        return
    
    cutoff = datetime.now() - timedelta(hours=hours)
    
    # RAG 호출 및 LLM 호출 시간 수집
    rag_times = []
    llm_times = []
    task_map = {}  # task_id -> {rag_time, llm_time, thesis_time}
    
    with open(ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                ts_str = entry.get("timestamp") or entry.get("ts")
                if not ts_str:
                    continue
                
                # Handle both ISO format and Unix timestamp
                if isinstance(ts_str, (int, float)):
                    ts = datetime.fromtimestamp(ts_str)
                else:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                
                if ts < cutoff:
                    continue
                
                event = entry.get("event", "")
                task_id = entry.get("task_id", "")
                persona = entry.get("persona", "")
                
                # Thesis 관련 이벤트만 수집
                if persona == "thesis":
                    if event == "rag_call_failed":
                        # RAG 실패
                        if task_id not in task_map:
                            task_map[task_id] = {}
                        task_map[task_id]["rag_time"] = 0.0  # 실패는 0초로 처리
                    
                    elif event == "persona_llm_run":
                        # LLM 호출 시간
                        duration = entry.get("duration_sec", 0.0)
                        llm_times.append(duration)
                        if task_id not in task_map:
                            task_map[task_id] = {}
                        task_map[task_id]["llm_time"] = duration
                    
                    elif event == "persona_run":
                        # 전체 Thesis 실행 시간
                        duration = entry.get("duration_sec", 0.0)
                        if task_id not in task_map:
                            task_map[task_id] = {}
                        task_map[task_id]["thesis_time"] = duration
            
            except Exception as e:
                continue
    
    if not llm_times:
        print(f"⚠️  No Thesis LLM calls found in last {hours}h")
        return
    
    # 통계 계산
    avg_llm = sum(llm_times) / len(llm_times)
    total_llm = sum(llm_times)
    
    # Task별 분석 (RAG + LLM vs Total Thesis Time)
    complete_tasks = [tid for tid, data in task_map.items() if "thesis_time" in data and "llm_time" in data]
    
    rag_overhead = []
    for tid in complete_tasks:
        data = task_map[tid]
        thesis_time = data.get("thesis_time", 0.0)
        llm_time = data.get("llm_time", 0.0)
        rag_time = data.get("rag_time")
        
        if rag_time is None:
            # RAG 시간 = Thesis 전체 시간 - LLM 시간 (추정)
            rag_time = thesis_time - llm_time
        
        rag_overhead.append(rag_time)
    
    avg_rag = sum(rag_overhead) / len(rag_overhead) if rag_overhead else 0.0
    
    # 결과 출력
    print(f"\n{'=' * 60}")
    print(f"📊 Thesis Breakdown Analysis (Last {hours}h)")
    print(f"{'=' * 60}\n")
    
    print(f"📈 LLM Call Statistics:")
    print(f"   Total calls:    {len(llm_times)}")
    print(f"   Average time:   {avg_llm:.3f}s")
    print(f"   Total time:     {total_llm:.2f}s")
    print(f"   Min/Max:        {min(llm_times):.3f}s / {max(llm_times):.3f}s")
    
    if rag_overhead:
        print(f"\n📈 RAG + Overhead Statistics:")
        print(f"   Total tasks:    {len(rag_overhead)}")
        print(f"   Average time:   {avg_rag:.3f}s")
        print(f"   Min/Max:        {min(rag_overhead):.3f}s / {max(rag_overhead):.3f}s")
        
        print(f"\n💡 Breakdown (Average):")
        total_avg = avg_llm + avg_rag
        llm_pct = (avg_llm / total_avg * 100) if total_avg > 0 else 0
        rag_pct = (avg_rag / total_avg * 100) if total_avg > 0 else 0
        
        print(f"   LLM:            {avg_llm:.3f}s ({llm_pct:.1f}%)")
        print(f"   RAG+Overhead:   {avg_rag:.3f}s ({rag_pct:.1f}%)")
        print(f"   Total:          {total_avg:.3f}s")
        
        # 최적화 제안
        print(f"\n🎯 Optimization Recommendations:")
        if llm_pct > 70:
            print(f"   ✅ LLM is the bottleneck ({llm_pct:.1f}%)")
            print(f"      → Consider: Streaming, model switching, prompt optimization")
        elif rag_pct > 30:
            print(f"   ✅ RAG+Overhead is significant ({rag_pct:.1f}%)")
            print(f"      → Consider: Parallel RAG queries, caching")
        else:
            print(f"   ℹ️  Balanced breakdown")
    
    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Measure Thesis persona internal breakdown")
    parser.add_argument("hours", type=int, nargs="?", default=24, help="Lookback hours (default: 24)")
    args = parser.parse_args()
    
    analyze_thesis_breakdown(args.hours)
