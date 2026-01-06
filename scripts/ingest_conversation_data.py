#!/usr/bin/env python3
"""
대화 데이터를 Resonance Ledger로 변환

입력: JSON 또는 CSV 형식의 대화 데이터
출력: resonance_ledger.jsonl (where/who 포함)

사용법:
    python scripts/ingest_conversation_data.py --input conversation.json
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List

def parse_conversation(input_path: Path) -> List[Dict]:
    """
    대화 데이터 파싱
    
    예상 형식:
    {
      "conversations": [
        {
          "timestamp": "2025-11-05T14:30:00Z",
          "speaker": "Binoche_Observer",
          "text": "이게 정말 맞을까?",
          "emotion": {"fear": 0.7, "anxiety": 0.6}
        }
      ]
    }
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get('conversations', [])

def conversation_to_resonance(conv: Dict) -> Dict:
    """대화 → Resonance 이벤트 변환"""
    
    # 감정 추출
    emotion = conv.get('emotion', {})
    fear = emotion.get('fear', 0.0)
    anxiety = emotion.get('anxiety', 0.0)
    confidence = emotion.get('confidence', 0.5)
    
    # Resonance Score 계산 (간단한 공식)
    # Fear ↑ → Score ↓ (압축 증가)
    resonance_score = 1.0 - (fear * 0.5 + anxiety * 0.3)
    
    # where/who 추출
    speaker = conv.get('speaker', 'unknown')
    where = conv.get('location', 'conversation')
    
    return {
        'timestamp': conv.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
        'event_type': f'conversation/{speaker}',
        'where': where,
        'who': speaker,
        'resonance_score': resonance_score,
        'emotion': {
            'fear': fear,
            'anxiety': anxiety,
            'confidence': confidence
        },
        'text': conv.get('text', ''),
        'metadata': {
            'source': 'manual_conversation_ingest'
        }
    }

def append_to_ledger(events: List[Dict], ledger_path: Path):
    """Resonance Ledger에 추가"""
    
    # 부모 디렉토리 생성
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(ledger_path, 'a', encoding='utf-8') as f:
        for event in events:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
    
    print(f"✅ {len(events)} events appended to {ledger_path}")

def main():
    parser = argparse.ArgumentParser(description="Ingest conversation data into Resonance Ledger")
    parser.add_argument('--input', '-i', required=True, help='Input conversation file (JSON)')
    parser.add_argument('--ledger', '-l', 
                       default='fdo_agi_repo/memory/resonance_ledger.jsonl',
                       help='Output ledger path')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        return
    
    # 대화 데이터 로드
    conversations = parse_conversation(input_path)
    print(f"📥 Loaded {len(conversations)} conversations")
    
    # Resonance 이벤트로 변환
    events = [conversation_to_resonance(conv) for conv in conversations]
    
    if args.dry_run:
        print("\n🔍 Preview (first 3 events):")
        for event in events[:3]:
            print(json.dumps(event, indent=2, ensure_ascii=False))
        print(f"\n... ({len(events)} total)")
        return
    
    # Ledger에 추가
    ledger_path = Path(args.ledger)
    append_to_ledger(events, ledger_path)
    
    print(f"\n✅ Done! Now run:")
    print(f"   python scripts/hippocampus_black_white_hole.py --hours 24")

if __name__ == '__main__':
    main()
