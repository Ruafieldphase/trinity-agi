#!/usr/bin/env python3
"""
코어 대화 데이터에서 감정 패턴 추출 → 해마 시스템 입력

이론:
1. 대화 길이 변화 → Fear 지표
2. 응답 간격 → Anxiety 지표
3. 주제 전환 빈도 → Confusion 지표
4. 비선형 패턴 → 감정 굴곡
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from collections import defaultdict
from workspace_root import get_workspace_root

def load_core_conversations(limit: int = None) -> List[Dict]:
    """코어 대화 로드"""
    data_path = get_workspace_root() / "outputs/Core/core_conversations_flat.jsonl"
    
    if not data_path.exists():
        print(f"⚠️  Data not found: {data_path}")
        return []
    
    conversations = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            try:
                msg = json.loads(line.strip())
                conversations.append(msg)
            except:
                continue
    
    return conversations

def extract_emotional_signals(messages: List[Dict]) -> List[Dict]:
    """대화에서 감정 신호 추출"""
    
    # 대화별로 그룹화
    convos = defaultdict(list)
    for msg in messages:
        if msg.get('author_role') in ['user', 'assistant']:
            convos[msg['conversation_id']].append(msg)
    
    emotional_events = []
    
    for conv_id, msgs in convos.items():
        # 시간 순 정렬
        msgs.sort(key=lambda x: x.get('message_order', 0))
        
        prev_time = None
        prev_length = None
        
        for i, msg in enumerate(msgs):
            if msg['author_role'] != 'user':
                continue
            
            content = msg.get('content', '')
            if isinstance(content, dict):
                content = str(content)
            
            msg_length = len(content)
            create_time = msg.get('create_time')
            
            # 감정 지표 계산
            event = {
                'timestamp': create_time or datetime.now().isoformat(),
                'conversation_id': conv_id,
                'conversation_title': msg.get('conversation_title', 'Unknown'),
                'message_order': msg.get('message_order', i),
                'event_type': 'dialogue',
                'where': 'chat',
                'who': 'Core',
                'what': content[:100],  # 처음 100자만
            }
            
            # Fear 지표: 메시지 길이 급감
            if prev_length and msg_length < prev_length * 0.5:
                event['fear'] = 0.7
                event['emotion_note'] = 'Message shortened significantly (fear/tension)'
            elif prev_length and msg_length > prev_length * 2:
                event['fear'] = 0.2
                event['joy'] = 0.6
                event['emotion_note'] = 'Message expanded (comfort/enthusiasm)'
            else:
                event['fear'] = 0.3
            
            # Anxiety 지표: 응답 시간 간격
            if prev_time and create_time:
                try:
                    t1 = datetime.fromisoformat(prev_time.replace('Z', '+00:00'))
                    t2 = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
                    gap_minutes = (t2 - t1).total_seconds() / 60
                    
                    if gap_minutes > 60:
                        event['anxiety'] = min(0.9, gap_minutes / 120)
                        event['emotion_note'] = event.get('emotion_note', '') + f' | Long gap: {gap_minutes:.0f}min'
                except:
                    pass
            
            # Resonance Score (임시)
            event['resonance_score'] = 1.0 - event.get('fear', 0.3)
            event['energy_level'] = event.get('joy', 0.5)
            event['quality_score'] = 0.8  # 코어와의 대화는 고품질
            
            emotional_events.append(event)
            
            prev_time = create_time
            prev_length = msg_length
    
    return emotional_events

def save_to_resonance_ledger(events: List[Dict], append: bool = True):
    """Resonance Ledger에 추가"""
    ledger_path = get_workspace_root() / "fdo_agi_repo/memory/resonance_ledger.jsonl"
    
    mode = 'a' if append else 'w'
    
    with open(ledger_path, mode, encoding='utf-8') as f:
        for event in events:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
    
    print(f"✅ {len(events)} emotional events saved to Resonance Ledger")

def main():
    print("="*60)
    print("🌊 Core Conversation → Emotional Signal Extraction")
    print("="*60)
    
    # 1. 코어 대화 로드 (전체)
    print("\n📥 Loading Core conversations...")
    messages = load_core_conversations(limit=None)
    print(f"   Loaded: {len(messages)} messages")
    
    # 2. 감정 신호 추출
    print("\n💫 Extracting emotional signals...")
    events = extract_emotional_signals(messages)
    print(f"   Extracted: {len(events)} emotional events")
    
    # 3. 통계
    print("\n📊 Emotional Statistics:")
    fear_avg = np.mean([e.get('fear', 0) for e in events])
    joy_avg = np.mean([e.get('joy', 0) for e in events])
    anxiety_avg = np.mean([e.get('anxiety', 0) for e in events if 'anxiety' in e])
    
    print(f"   Average Fear: {fear_avg:.3f}")
    print(f"   Average Joy: {joy_avg:.3f}")
    print(f"   Average Anxiety: {anxiety_avg:.3f}")
    
    # 4. 샘플 출력
    print("\n🔬 Sample Events:")
    for event in events[:3]:
        print(f"\n   - {event['timestamp']}")
        print(f"     Title: {event['conversation_title']}")
        print(f"     Fear: {event.get('fear', 0):.2f}, Joy: {event.get('joy', 0):.2f}")
        print(f"     Note: {event.get('emotion_note', 'N/A')}")
    
    # 5. Resonance Ledger에 저장
    save_choice = input("\n💾 Save to Resonance Ledger? (y/N): ")
    if save_choice.lower() == 'y':
        save_to_resonance_ledger(events, append=True)
        print("\n✨ Now run: python scripts/hippocampus_black_white_hole.py --hours 24")
    else:
        print("\n⏭️  Skipped saving.")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
