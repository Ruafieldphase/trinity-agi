#!/usr/bin/env python3
"""
Resonance Ledger Backfill: 필드명 정규화 소급 적용

기존 34,314개 이벤트에 정규화된 quality/latency_ms 필드 추가

루멘(合) 권장: 시간 투자 대비 효과 극대화 (10분 → 10%+ 커버리지)

Usage:
    python scripts/backfill_ledger_metrics.py [--dry-run] [--recent-days 7]

Options:
    --dry-run: 실제 쓰기 없이 시뮬레이션
    --recent-days: 최근 N일 이벤트만 처리 (기본: 전체)
    --backup: Ledger 백업 생성 (기본: True)
"""

import argparse
import json
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List

# Repo root detection
REPO_ROOT = Path(__file__).parent.parent
LEDGER_PATH = REPO_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"


# Field normalization rules (event_emitter.py와 동일)
FIELD_ALIASES = {
    'agi_quality': 'quality',
    'lumen_latency_ms': 'latency_ms',
    'duration_sec': 'latency_ms',  # 변환 필요 (초 → 밀리초)
}


def normalize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    이벤트에 정규화된 필드 추가
    
    Args:
        event: 원본 이벤트
    
    Returns:
        정규화된 이벤트 (원본 필드 유지)
    """
    normalized = event.copy()
    
    for old_name, new_name in FIELD_ALIASES.items():
        # 이미 정규화된 필드가 있으면 스킵
        if new_name in normalized:
            continue
        
        # 레거시 필드가 없으면 스킵
        if old_name not in normalized:
            continue
        
        value = normalized[old_name]
        
        # duration_sec → latency_ms 변환 (초 → 밀리초)
        if old_name == 'duration_sec' and new_name == 'latency_ms':
            value = float(value) * 1000
        
        normalized[new_name] = value
    
    return normalized


def should_process_event(event: Dict[str, Any], recent_days: int = None) -> bool:
    """
    이벤트 처리 여부 결정
    
    Args:
        event: 이벤트
        recent_days: 최근 N일 이벤트만 처리 (None: 전체)
    
    Returns:
        처리 여부
    """
    # recent_days 지정 안 됨: 모두 처리
    if recent_days is None:
        return True
    
    # 타임스탬프 없음: 스킵
    if 'timestamp' not in event:
        return False
    
    # Unix timestamp 기반 필터링
    cutoff = datetime.now(timezone.utc) - timedelta(days=recent_days)
    event_time = datetime.fromtimestamp(event['timestamp'], tz=timezone.utc)
    
    return event_time >= cutoff


def backfill_metrics(
    dry_run: bool = False,
    recent_days: int = None,
    backup: bool = True
) -> Dict[str, Any]:
    """
    Ledger 메트릭 소급 적용
    
    Args:
        dry_run: True면 시뮬레이션만
        recent_days: 최근 N일만 처리 (None: 전체)
        backup: True면 백업 생성
    
    Returns:
        처리 통계
    """
    stats = {
        'total_events': 0,
        'processed_events': 0,
        'quality_added': 0,
        'latency_added': 0,
        'skipped_events': 0,
    }
    
    # Ledger 읽기
    print(f"📖 Reading Ledger: {LEDGER_PATH}")
    events = []
    
    with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            
            try:
                event = json.loads(line)
                events.append(event)
            except json.JSONDecodeError as e:
                print(f"⚠️ Line {line_num}: Invalid JSON - {e}")
                continue
    
    stats['total_events'] = len(events)
    print(f"✅ Loaded {len(events):,} events")
    
    # 이벤트 정규화
    print(f"\n🔄 Normalizing events...")
    normalized_events = []
    
    for event in events:
        # 최근 N일 필터링
        if not should_process_event(event, recent_days):
            stats['skipped_events'] += 1
            normalized_events.append(event)  # 원본 유지
            continue
        
        # 정규화 전 상태
        had_quality = 'quality' in event
        had_latency = 'latency_ms' in event
        
        # 정규화 실행
        normalized = normalize_event(event)
        normalized_events.append(normalized)
        
        # 통계 업데이트
        stats['processed_events'] += 1
        
        if not had_quality and 'quality' in normalized:
            stats['quality_added'] += 1
        
        if not had_latency and 'latency_ms' in normalized:
            stats['latency_added'] += 1
    
    # 통계 출력
    print(f"\n📊 Backfill Statistics:")
    print(f"   Total Events: {stats['total_events']:,}")
    print(f"   Processed: {stats['processed_events']:,}")
    print(f"   Skipped (too old): {stats['skipped_events']:,}")
    print(f"   Quality Added: {stats['quality_added']:,}")
    print(f"   Latency Added: {stats['latency_added']:,}")
    
    if recent_days:
        print(f"   Filter: Recent {recent_days} days")
    
    # 예상 커버리지
    if stats['total_events'] > 0:
        quality_coverage = ((stats['quality_added'] + 123) / stats['total_events']) * 100
        latency_coverage = ((stats['latency_added'] + 85) / stats['total_events']) * 100
        
        print(f"\n🎯 Expected Coverage:")
        print(f"   Quality: 0.4% → {quality_coverage:.1f}%")
        print(f"   Latency: 0.2% → {latency_coverage:.1f}%")
    
    # Dry-run 종료
    if dry_run:
        print(f"\n⚠️ DRY-RUN MODE - No changes written")
        return stats
    
    # 백업 생성
    if backup:
        backup_path = LEDGER_PATH.with_suffix('.jsonl.backup')
        print(f"\n💾 Creating backup: {backup_path}")
        shutil.copy2(LEDGER_PATH, backup_path)
        print(f"✅ Backup saved")
    
    # Ledger 쓰기
    print(f"\n💾 Writing normalized Ledger...")
    
    with open(LEDGER_PATH, 'w', encoding='utf-8') as f:
        for event in normalized_events:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
    
    print(f"✅ Ledger updated: {LEDGER_PATH}")
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Backfill Resonance Ledger with normalized metrics"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate without writing changes'
    )
    parser.add_argument(
        '--recent-days',
        type=int,
        default=None,
        help='Only process events from last N days (default: all)'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip backup creation (not recommended)'
    )
    
    args = parser.parse_args()
    
    print("🚀 Resonance Ledger Backfill\n")
    print("=" * 60)
    
    stats = backfill_metrics(
        dry_run=args.dry_run,
        recent_days=args.recent_days,
        backup=not args.no_backup
    )
    
    print("\n" + "=" * 60)
    print("🎉 Backfill Complete!")
    
    if args.dry_run:
        print("\n💡 Run without --dry-run to apply changes")


if __name__ == '__main__':
    main()
