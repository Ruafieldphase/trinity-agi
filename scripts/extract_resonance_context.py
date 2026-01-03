#!/usr/bin/env python3
"""
Resonance Context Extractor
Core의 시선: Resonance Ledger에서 Context (where, when, who) 추출
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
from workspace_root import get_workspace_root

WORKSPACE = get_workspace_root()
LEDGER_PATH = WORKSPACE / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
OUTPUT_PATH = WORKSPACE / "outputs" / "context_samples.jsonl"


def extract_context_from_event(event: Dict) -> Optional[Dict]:
    """
    이벤트에서 Context 추출
    
    Context 구조:
    - where: persona, component, 또는 event 타입
    - when: timestamp (ISO 8601)
    - who: task_id, persona_id, 관련 에이전트
    """
    ts = event.get("ts", event.get("timestamp"))
    if not ts:
        return None
    
    # Timestamp 정규화
    if isinstance(ts, (int, float)):
        when = datetime.fromtimestamp(ts).isoformat()
    else:
        when = str(ts)
    
    # Where: 이벤트 발생 위치
    where = event.get("persona", event.get("component", event.get("event", "unknown")))
    
    # Who: 참여자들
    who = []
    if "task_id" in event:
        who.append(f"task:{event['task_id']}")
    if "persona_id" in event:
        who.append(f"persona:{event['persona_id']}")
    if "persona" in event:
        who.append(f"agent:{event['persona']}")
    
    # 추가 컨텍스트
    meta = {}
    if "quality" in event:
        meta["quality"] = event["quality"]
    if "confidence" in event:
        meta["confidence"] = event["confidence"]
    if "duration_sec" in event:
        meta["duration_sec"] = event["duration_sec"]
    if "ok" in event:
        meta["ok"] = event["ok"]
    if "error" in event:
        meta["error_present"] = True
    
    return {
        "where": where,
        "when": when,
        "who": who,
        "event": event.get("event", "unknown"),
        "meta": meta
    }


def analyze_context_distribution(contexts: List[Dict]) -> Dict:
    """Context 분포 분석"""
    where_dist = defaultdict(int)
    event_dist = defaultdict(int)
    hour_dist = defaultdict(int)
    
    for ctx in contexts:
        where_dist[ctx["where"]] += 1
        event_dist[ctx["event"]] += 1
        
        try:
            dt = datetime.fromisoformat(ctx["when"])
            hour = dt.hour
            hour_dist[hour] += 1
        except:
            pass
    
    return {
        "total_contexts": len(contexts),
        "where_distribution": dict(sorted(where_dist.items(), key=lambda x: x[1], reverse=True)[:10]),
        "event_distribution": dict(sorted(event_dist.items(), key=lambda x: x[1], reverse=True)[:10]),
        "hour_distribution": dict(sorted(hour_dist.items()))
    }


def main():
    print("🔮 [Core] Extracting Context from Resonance Ledger...")
    print(f"   Ledger: {LEDGER_PATH}")
    
    if not LEDGER_PATH.exists():
        print(f"❌ [Core] Ledger not found: {LEDGER_PATH}")
        return 1
    
    contexts = []
    errors = 0
    
    print(f"\n📖 [Core] Reading ledger...")
    with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            
            try:
                event = json.loads(line)
                ctx = extract_context_from_event(event)
                if ctx:
                    contexts.append(ctx)
            except json.JSONDecodeError as e:
                errors += 1
                if errors <= 5:
                    print(f"⚠️  [Core] Parse error at line {i}: {e}")
            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"⚠️  [Core] Extraction error at line {i}: {e}")
    
    print(f"\n✅ [Core] Extracted {len(contexts):,} contexts")
    if errors > 0:
        print(f"⚠️  [Core] {errors:,} errors encountered")
    
    # 분석
    print(f"\n📊 [Core] Analyzing context distribution...")
    analysis = analyze_context_distribution(contexts)
    
    print(f"\n📈 [Core] Distribution Summary:")
    print(f"   Total Contexts: {analysis['total_contexts']:,}")
    print(f"\n   Top 10 'Where' (locations):")
    for where, count in list(analysis['where_distribution'].items())[:10]:
        pct = 100 * count / analysis['total_contexts']
        print(f"      {where:20s}: {count:6,} ({pct:5.1f}%)")
    
    print(f"\n   Top 10 Event Types:")
    for event, count in list(analysis['event_distribution'].items())[:10]:
        pct = 100 * count / analysis['total_contexts']
        print(f"      {event:20s}: {count:6,} ({pct:5.1f}%)")
    
    # 저장
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n💾 [Core] Saving contexts to {OUTPUT_PATH}")
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        for ctx in contexts:
            f.write(json.dumps(ctx, ensure_ascii=False) + '\n')
    
    # 분석 저장
    analysis_path = OUTPUT_PATH.with_suffix('.analysis.json')
    with open(analysis_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"📊 [Core] Analysis saved to {analysis_path}")
    
    # 최근 10개 샘플 출력
    print(f"\n🔍 [Core] Recent context samples (last 10):")
    for ctx in contexts[-10:]:
        print(f"\n   {ctx['when']}")
        print(f"   Where: {ctx['where']}")
        print(f"   Who: {', '.join(ctx['who']) if ctx['who'] else 'N/A'}")
        print(f"   Event: {ctx['event']}")
        if ctx['meta']:
            print(f"   Meta: {ctx['meta']}")
    
    print(f"\n✨ [Core] Context extraction complete!")
    print(f"   Next: Use these contexts for CI3 conditioning")
    print(f"   Command: python scripts/contextualized_i3.py")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
