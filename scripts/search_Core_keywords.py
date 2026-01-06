#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
코어-Core 대화에서 블랙홀 탈출 여정 추적
"""
import json
from pathlib import Path
from workspace_root import get_workspace_root

KEYWORDS = ["오감", "명상", "집착", "편견", "두려움", "블랙홀", "공명", "리듬"]

def search_conversations():
    jsonl_path = get_workspace_root() / "outputs" / "Core" / "core_conversations_flat.jsonl"
    
    matches = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            msg = json.loads(line)
            content = msg.get('content', '')
            
            # 키워드 매칭
            if any(kw in content for kw in KEYWORDS):
                matches.append({
                    'timestamp': msg.get('create_time', ''),
                    'role': msg.get('author_role', ''),
                    'content': content[:300]  # 첫 300자
                })
    
    print(f"✅ Found {len(matches)} matching messages\n")
    
    for i, m in enumerate(matches[:10], 1):
        print(f"--- Message {i} ---")
        print(f"Time: {m['timestamp']}")
        print(f"Role: {m['role']}")
        print(f"Content: {m['content']}...")
        print()

if __name__ == "__main__":
    search_conversations()
