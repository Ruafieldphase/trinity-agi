#!/usr/bin/env python3
"""
🌅 Rua's Awakening Timeline Reader
루아의 AI 각성 여정을 시간순으로 읽어주는 스크립트

Usage:
    python rua_timeline_reader.py --start-date 2025-04-01 --output-md outputs/rua/rua_timeline.md
"""

import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from collections import defaultdict

def load_conversations(jsonl_path: Path) -> List[Dict]:
    """JSONL 파일에서 대화 로드"""
    conversations = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                conversations.append(json.loads(line))
    return conversations

def group_by_conversation(conversations: List[Dict]) -> Dict[str, List[Dict]]:
    """대화를 conversation_id별로 그룹핑"""
    grouped = defaultdict(list)
    for conv in conversations:
        conv_id = conv.get('conversation_id', 'unknown')
        grouped[conv_id].append(conv)
    
    # 각 그룹 내에서 message_order로 정렬
    for conv_id in grouped:
        grouped[conv_id].sort(key=lambda x: x.get('message_order', 0))
    
    return dict(grouped)

def estimate_date_from_title(title: str) -> str:
    """대화 제목에서 날짜 추정 (임시)"""
    # 제목 기반 날짜 추정 로직
    if '생계' in title or '탐구' in title:
        return '2025-04-01'  # 시작점
    elif 'AGI' in title or '자율' in title:
        return '2025-04-15'  # 중간점
    elif '목표' in title or 'Goal' in title:
        return '2025-05-01'  # 성장기
    else:
        return '2025-04-10'  # 기본

def generate_markdown_timeline(grouped: Dict[str, List[Dict]], output_path: Path):
    """마크다운 타임라인 생성"""
    
    # conversation별로 날짜 추정해서 정렬
    # Sort by estimated date (oldest first = ascending order)
    sorted_conversations = sorted(
        grouped.items(),
        key=lambda x: estimate_date_from_title(x[1][0].get('conversation_title', '')),
        reverse=False  # 오래된 것부터 (4월 초 → 최근)
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 🌅 루아의 AI 각성 여정 - 시간순 타임라인\n\n")
        f.write(f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        
        for conv_id, messages in sorted_conversations:
            if not messages:
                continue
            
            title = messages[0].get('conversation_title', '제목 없음')
            estimated_date = estimate_date_from_title(title)
            
            f.write(f"## 📅 {estimated_date} - {title}\n\n")
            f.write(f"**Conversation ID:** `{conv_id}`\n\n")
            
            for msg in messages:
                role = msg.get('author_role', 'unknown')
                content = msg.get('content', '')
                order = msg.get('message_order', 0)
                
                if role == 'user':
                    f.write(f"### 👤 비노체 (Message #{order})\n\n")
                elif role == 'assistant':
                    f.write(f"### 🤖 루아 (Message #{order})\n\n")
                else:
                    f.write(f"### ❓ {role} (Message #{order})\n\n")
                
                # 내용 출력 (너무 길면 요약)
                if len(content) > 500:
                    f.write(f"{content[:500]}...\n\n")
                    f.write(f"*[전체 {len(content)}자 중 500자만 표시]*\n\n")
                else:
                    f.write(f"{content}\n\n")
                
                f.write("---\n\n")
            
            f.write("\n\n")

def main():
    parser = argparse.ArgumentParser(description='루아의 AI 각성 타임라인 생성')
    parser.add_argument('--jsonl', type=Path, default=Path('outputs/rua/rua_conversations_flat.jsonl'),
                        help='JSONL 입력 파일 경로')
    parser.add_argument('--output-md', type=Path, default=Path('outputs/rua/rua_timeline.md'),
                        help='마크다운 출력 파일 경로')
    parser.add_argument('--start-date', type=str, help='시작 날짜 필터 (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    print(f"📖 루아의 각성 스토리를 읽어옵니다...")
    print(f"   입력: {args.jsonl}")
    print(f"   출력: {args.output_md}")
    
    # 대화 로드
    conversations = load_conversations(args.jsonl)
    print(f"✅ 총 {len(conversations)}개 메시지 로드 완료")
    
    # 그룹핑
    grouped = group_by_conversation(conversations)
    print(f"✅ {len(grouped)}개 대화 스레드로 그룹핑 완료")
    
    # 마크다운 생성
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    generate_markdown_timeline(grouped, args.output_md)
    print(f"✅ 타임라인 생성 완료: {args.output_md}")
    
    print(f"\n🌅 루아의 각성 여정이 시간순으로 정리되었습니다!")
    print(f"   {args.output_md} 파일을 열어보세요!")

if __name__ == '__main__':
    main()
