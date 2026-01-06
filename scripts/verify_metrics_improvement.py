#!/usr/bin/env python3
"""
메트릭 개선 효과 검증 스크립트
코드 수정 후 실제 메트릭 커버리지가 향상되었는지 확인
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from workspace_root import get_workspace_root

LEDGER_PATH = get_workspace_root() / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"

def count_metrics_in_recent_events(hours=1):
    """최근 이벤트에서 메트릭 커버리지 계산"""
    if not LEDGER_PATH.exists():
        return {"error": "No ledger found"}
    
    cutoff = datetime.now(timezone.utc).timestamp() - (hours * 3600)
    total_events = 0
    with_quality = 0
    with_latency = 0
    with_both = 0
    event_types = set()
    
    with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                event = json.loads(line.strip())
                ts = event.get('timestamp', 0)
                if ts < cutoff:
                    continue
                
                total_events += 1
                has_quality = 'quality' in event
                has_latency = 'latency_ms' in event or 'latency' in event
                
                if has_quality:
                    with_quality += 1
                if has_latency:
                    with_latency += 1
                if has_quality and has_latency:
                    with_both += 1
                
                evt = event.get('event_type') or event.get('event', 'unknown')
                event_types.add(evt)
                
            except:
                continue
    
    quality_coverage = (with_quality / total_events * 100) if total_events > 0 else 0
    latency_coverage = (with_latency / total_events * 100) if total_events > 0 else 0
    both_coverage = (with_both / total_events * 100) if total_events > 0 else 0
    
    return {
        "total_events": total_events,
        "with_quality": with_quality,
        "with_latency": with_latency,
        "with_both": with_both,
        "quality_coverage_%": round(quality_coverage, 1),
        "latency_coverage_%": round(latency_coverage, 1),
        "both_coverage_%": round(both_coverage, 1),
        "unique_event_types": len(event_types),
        "event_types": sorted(list(event_types))
    }

if __name__ == "__main__":
    print("🔍 메트릭 커버리지 검증 중...\n")
    
    # 최근 1시간 데이터 (코드 수정 전후 비교용)
    result = count_metrics_in_recent_events(hours=1)
    
    if "error" in result:
        print(f"⚠️  {result['error']}")
    else:
        print(f"📊 최근 1시간 이벤트 분석:")
        print(f"   총 이벤트: {result['total_events']}")
        print(f"   Quality 메트릭: {result['with_quality']} ({result['quality_coverage_%']}%)")
        print(f"   Latency 메트릭: {result['with_latency']} ({result['latency_coverage_%']}%)")
        print(f"   Both (Quality+Latency): {result['with_both']} ({result['both_coverage_%']}%)")
        print(f"   고유 이벤트 타입: {result['unique_event_types']}")
        
        print(f"\n📝 이벤트 타입 목록:")
        for evt in result['event_types'][:10]:  # 상위 10개만 표시
            print(f"   - {evt}")
        
        # 목표 달성 평가
        print(f"\n🎯 목표 달성 평가:")
        if result['quality_coverage_%'] >= 50:
            print(f"   ✅ Quality 커버리지 목표 달성! ({result['quality_coverage_%']}% >= 50%)")
        else:
            print(f"   ⏳ Quality 커버리지 진행 중 ({result['quality_coverage_%']}% / 50%)")
        
        if result['latency_coverage_%'] >= 50:
            print(f"   ✅ Latency 커버리지 목표 달성! ({result['latency_coverage_%']}% >= 50%)")
        else:
            print(f"   ⏳ Latency 커버리지 진행 중 ({result['latency_coverage_%']}% / 50%)")
    
    # JSON 출력 (자동화용)
    output_path = get_workspace_root() / "outputs" / "metrics_improvement_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 리포트 저장: {output_path}")
