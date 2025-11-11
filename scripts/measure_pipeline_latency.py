#!/usr/bin/env python3
"""
Pipeline Latency 실측 분석

Resonance Ledger에서 최근 작업의 레이턴시를 분석하여
실제 병목 지점을 명확히 파악합니다.
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


def analyze_pipeline_latency(hours: int = 1):
    """최근 N시간 동안의 Pipeline 레이턴시 분석"""
    ledger_path = Path(__file__).parent.parent / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
    
    if not ledger_path.exists():
        print(f"❌ Ledger not found: {ledger_path}")
        return
    
    # 시간 필터
    cutoff = datetime.now() - timedelta(hours=hours)
    
    # 작업별 타이밍 저장
    tasks = defaultdict(lambda: {
        "thesis_dur": None,
        "antithesis_dur": None,
        "synthesis_dur": None,
        "total_dur": None,
        "cache_hits": [],
        "cache_misses": []
    })
    
    # Ledger 파싱
    with open(ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            # 시간 필터
            if "timestamp" in event:
                try:
                    event_time = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
                    if event_time < cutoff:
                        continue
                except Exception:
                    pass
            
            task_id = event.get("task_id")
            if not task_id:
                continue
            
            # Duration 추출
            event_type = event.get("event", "")
            duration = event.get("duration_sec")
            
            if duration is not None:
                if event_type == "thesis_end":
                    tasks[task_id]["thesis_dur"] = duration
                elif event_type == "antithesis_end":
                    tasks[task_id]["antithesis_dur"] = duration
                elif event_type == "synthesis_end":
                    tasks[task_id]["synthesis_dur"] = duration
                elif event_type == "total_latency":
                    tasks[task_id]["total_dur"] = duration
            
            # Cache 이벤트
            if "_cache_hit" in event_type:
                tasks[task_id]["cache_hits"].append(event_type.replace("_cache_hit", ""))
            elif "_cache_miss" in event_type:
                tasks[task_id]["cache_misses"].append(event_type.replace("_cache_miss", ""))
    
    if not tasks:
        print(f"⚠️  No tasks found in last {hours} hour(s)")
        return
    
    # 분석 결과 출력
    print(f"\n{'='*70}")
    print(f"Pipeline Latency Analysis (Last {hours} hour(s))")
    print(f"{'='*70}\n")
    
    total_thesis = []
    total_antithesis = []
    total_synthesis = []
    total_pipeline = []
    
    for task_id, data in sorted(tasks.items(), key=lambda x: x[0])[-5:]:  # 최근 5개만
        print(f"Task: {task_id}")
        
        if data["thesis_dur"] is not None:
            print(f"  Thesis:     {data['thesis_dur']:.2f}s")
            total_thesis.append(data["thesis_dur"])
        
        if data["antithesis_dur"] is not None:
            print(f"  Antithesis: {data['antithesis_dur']:.2f}s")
            total_antithesis.append(data["antithesis_dur"])
        
        if data["synthesis_dur"] is not None:
            print(f"  Synthesis:  {data['synthesis_dur']:.2f}s")
            total_synthesis.append(data["synthesis_dur"])
        
        if data["total_dur"] is not None:
            print(f"  Total:      {data['total_dur']:.2f}s")
            total_pipeline.append(data["total_dur"])
        
        if data["cache_hits"]:
            print(f"  ✅ Cache Hits: {', '.join(data['cache_hits'])}")
        if data["cache_misses"]:
            print(f"  ❌ Cache Misses: {', '.join(data['cache_misses'])}")
        
        print()
    
    # 통계 요약
    if total_thesis:
        avg_thesis = sum(total_thesis) / len(total_thesis)
        print(f"Avg Thesis:     {avg_thesis:.2f}s")
    
    if total_antithesis:
        avg_antithesis = sum(total_antithesis) / len(total_antithesis)
        print(f"Avg Antithesis: {avg_antithesis:.2f}s")
    
    if total_synthesis:
        avg_synthesis = sum(total_synthesis) / len(total_synthesis)
        print(f"Avg Synthesis:  {avg_synthesis:.2f}s")
    
    if total_pipeline:
        avg_pipeline = sum(total_pipeline) / len(total_pipeline)
        print(f"\n🎯 Avg Total Pipeline: {avg_pipeline:.2f}s")
        
        if total_thesis and total_antithesis and total_synthesis:
            avg_sum = avg_thesis + avg_antithesis + avg_synthesis
            overhead = avg_pipeline - avg_sum
            print(f"   (Overhead: {overhead:.2f}s = {overhead/avg_pipeline*100:.1f}%)")
    
    print(f"\n{'='*70}\n")
    
    # 병목 판단
    if total_thesis and total_antithesis and total_synthesis:
        durations = [
            ("Thesis", avg_thesis),
            ("Antithesis", avg_antithesis),
            ("Synthesis", avg_synthesis)
        ]
        durations.sort(key=lambda x: x[1], reverse=True)
        
        print("🔍 Bottleneck Analysis:")
        for i, (name, dur) in enumerate(durations, 1):
            pct = dur / (avg_thesis + avg_antithesis + avg_synthesis) * 100
            print(f"  {i}. {name}: {dur:.2f}s ({pct:.1f}%)")
        
        print(f"\n💡 Optimization Opportunity:")
        if all(d[1] > 1.5 for d in durations):
            print("   All phases are slow (>1.5s) → LLM API latency is the bottleneck")
            print("   Consider: Parallel execution, caching, or faster models")
        else:
            print(f"   {durations[0][0]} is the slowest → Focus optimization there")


if __name__ == "__main__":
    import sys
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    analyze_pipeline_latency(hours)
