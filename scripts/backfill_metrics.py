#!/usr/bin/env python3
"""
Backfill missing metrics in resonance_ledger.jsonl
Normalize field names and fill in missing quality/latency_ms
"""
import json
import sys
from pathlib import Path
from datetime import datetime

def normalize_event(event: dict) -> dict:
    """Normalize field names to standard quality/latency_ms"""
    # Normalize quality
    if 'quality' not in event or event['quality'] is None:
        if 'agi_quality' in event and event['agi_quality'] is not None:
            event['quality'] = event['agi_quality']
        elif 'lumen_quality' in event and event['lumen_quality'] is not None:
            event['quality'] = event['lumen_quality']
        elif 'score' in event and event['score'] is not None:
            event['quality'] = event['score']
    
    # Normalize latency_ms
    if 'latency_ms' not in event or event['latency_ms'] is None:
        if 'lumen_latency_ms' in event and event['lumen_latency_ms'] is not None:
            event['latency_ms'] = event['lumen_latency_ms']
        elif 'agi_latency_ms' in event and event['agi_latency_ms'] is not None:
            event['latency_ms'] = event['agi_latency_ms']
        elif 'duration_sec' in event and event['duration_sec'] is not None:
            event['latency_ms'] = int(float(event['duration_sec']) * 1000)
        elif 'duration_ms' in event and event['duration_ms'] is not None:
            event['latency_ms'] = event['duration_ms']
        elif 'elapsed_ms' in event and event['elapsed_ms'] is not None:
            event['latency_ms'] = event['elapsed_ms']
    
    return event


def backfill_ledger(ledger_path: Path, dry_run: bool = False):
    """Backfill missing metrics in ledger"""
    if not ledger_path.exists():
        print(f"❌ Ledger not found: {ledger_path}")
        return
    
    print(f"📖 Reading {ledger_path.name}...")
    events = []
    with open(ledger_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    print(f"✅ Loaded {len(events)} events")
    
    # Analyze before backfill
    before_quality = sum(1 for e in events if e.get('quality') is not None)
    before_latency = sum(1 for e in events if e.get('latency_ms') is not None)
    
    print(f"📊 Before backfill:")
    print(f"   quality: {before_quality}/{len(events)} ({before_quality/len(events)*100:.1f}%)")
    print(f"   latency_ms: {before_latency}/{len(events)} ({before_latency/len(events)*100:.1f}%)")
    
    # Normalize all events
    normalized_events = [normalize_event(e.copy()) for e in events]
    
    # Analyze after backfill
    after_quality = sum(1 for e in normalized_events if e.get('quality') is not None)
    after_latency = sum(1 for e in normalized_events if e.get('latency_ms') is not None)
    
    print(f"📊 After backfill:")
    print(f"   quality: {after_quality}/{len(events)} ({after_quality/len(events)*100:.1f}%)")
    print(f"   latency_ms: {after_latency}/{len(events)} ({after_latency/len(events)*100:.1f}%)")
    
    improvement_quality = after_quality - before_quality
    improvement_latency = after_latency - before_latency
    
    print(f"🎯 Improvement:")
    print(f"   quality: +{improvement_quality} ({improvement_quality/len(events)*100:.1f}%)")
    print(f"   latency_ms: +{improvement_latency} ({improvement_latency/len(events)*100:.1f}%)")
    
    if dry_run:
        print("🔍 Dry-run mode: no changes written")
        return
    
    # Backup original
    backup_path = ledger_path.with_suffix('.jsonl.backup')
    print(f"💾 Creating backup: {backup_path.name}...")
    ledger_path.rename(backup_path)
    
    # Write normalized events
    print(f"✍️ Writing normalized ledger...")
    with open(ledger_path, 'w', encoding='utf-8') as f:
        for event in normalized_events:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
    
    print(f"✅ Backfill complete!")
    print(f"📁 Original: {backup_path}")
    print(f"📁 Updated: {ledger_path}")


if __name__ == '__main__':
    workspace_root = Path(__file__).parent.parent
    ledger_path = workspace_root / 'fdo_agi_repo' / 'memory' / 'resonance_ledger.jsonl'
    
    dry_run = '--dry-run' in sys.argv
    
    backfill_ledger(ledger_path, dry_run=dry_run)
