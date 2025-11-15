#!/usr/bin/env python3
"""빠르게 루아님 대화 핵심 정보만 추출"""
import json
from pathlib import Path
from collections import Counter

jsonl_path = Path("C:/workspace/agi/outputs/rua/rua_conversations_flat.jsonl")

print("📖 루아님 대화 빠른 요약\n")

# 1. 가장 긴 대화 Top 10
conversations = []
with open(jsonl_path, 'r', encoding='utf-8') as f:
    for line in f:
        conv = json.loads(line)
        conversations.append({
            'id': conv['conversation_id'],
            'title': conv['title'],
            'turns': len(conv['messages']),
            'date': conv['create_time'][:10]
        })

# 길이순 정렬
conversations.sort(key=lambda x: x['turns'], reverse=True)

print("🏆 가장 깊은 대화 Top 10:")
print("-" * 80)
for i, conv in enumerate(conversations[:10], 1):
    print(f"{i:2d}. [{conv['turns']:4d}턴] {conv['date']} | {conv['title'][:50]}")

print("\n" + "="*80)

# 2. 키워드별 대화 찾기
keywords = ['리듬', '감응', '생계', '각성', '감성', '천천히', '울림', 'Zone']
print("\n🔍 키워드별 대화 개수:")
print("-" * 80)
for kw in keywords:
    count = sum(1 for c in conversations if kw in c['title'])
    if count > 0:
        print(f"'{kw}': {count}개")
        # 예시 몇 개
        examples = [c for c in conversations if kw in c['title']][:3]
        for ex in examples:
            print(f"  - [{ex['turns']:3d}턴] {ex['title'][:60]}")

print("\n✅ 완료!")
