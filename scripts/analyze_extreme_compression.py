#!/usr/bin/env python3
"""극단 압축 이벤트 분석"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

from workspace_root import get_workspace_root

def analyze_extreme_compression():
    ledger = get_workspace_root() / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
    
    # 173.9x 압축 시점: 2025-11-05T15:57:57
    compression_time = datetime.fromisoformat('2025-11-05T15:57:57')
    window_start = compression_time - timedelta(hours=6)
    
    events = []
    with open(ledger, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except:
                    pass
    
    # 6시간 윈도우 필터링
    filtered = []
    for e in events:
        try:
            ts = datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00').replace('+00:00+00:00', '+00:00'))
            if ts.tzinfo:
                ts = ts.replace(tzinfo=None)
            if window_start <= ts <= compression_time:
                filtered.append(e)
        except:
            pass
    
    print(f"⚫ 극단 압축 분석 (173.9x)")
    print(f"   시간: 2025-11-05T15:57:57")
    print(f"   윈도우: 6시간 전부터")
    print()
    print(f"📊 총 이벤트: {len(filtered)}개")
    print()
    
    # 이벤트 타입별 분포
    types = Counter(e['event_type'] for e in filtered)
    print("📋 이벤트 타입 분포:")
    for event_type, count in types.most_common(10):
        print(f"   {event_type}: {count}개")
    print()
    
    # 시간대별 분포
    hourly = Counter()
    for e in filtered:
        try:
            ts = datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00').replace('+00:00+00:00', '+00:00'))
            if ts.tzinfo:
                ts = ts.replace(tzinfo=None)
            hour = ts.strftime("%H:00")
            hourly[hour] += 1
        except:
            pass
    
    print("⏰ 시간대별 분포:")
    for hour in sorted(hourly.keys()):
        count = hourly[hour]
        bar = "█" * (count // 10) if count >= 10 else "▌"
        print(f"   {hour}: {count:4d}개 {bar}")
    print()
    
    # 압축률 계산
    # 173.9x = 원본 크기 / 압축 후 크기
    # 원본: filtered 이벤트들
    # 압축 후: 1개 요약 (hippocampus_analysis)
    
    original_size = len(filtered)
    compressed_size = original_size / 173.9
    
    print("🌀 블랙홀 효과:")
    print(f"   원본 이벤트: {original_size}개")
    print(f"   압축 후: {compressed_size:.1f}개 상당")
    print(f"   손실된 정보: {original_size - compressed_size:.1f}개 ({(1 - compressed_size/original_size)*100:.1f}%)")
    print()
    print("💡 해석:")
    print("   → 세부사항 99.4% 소실")
    print("   → 본질 패턴만 남음")
    print("   → 이것이 'Implicate Order' (내재 질서)")

if __name__ == "__main__":
    analyze_extreme_compression()
