#!/usr/bin/env python3
"""
Trinity Dataset Integration for BQI Learning
Rua + Lubi 데이터를 BQI 학습 포맷으로 변환
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_rua_data(jsonl_path: Path) -> List[Dict[str, Any]]:
    """Load and filter Rua dataset"""
    conversations = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            msg = json.loads(line)
            # Filter: user-assistant pairs only
            if msg['author_role'] in ['user', 'assistant'] and msg.get('content'):
                conversations.append({
                    'source': 'rua',
                    'conversation_id': msg['conversation_id'],
                    'role': msg['author_role'],
                    'content': msg['content'],
                    'timestamp': msg.get('create_time', ''),
                    'message_id': msg['message_id']
                })
    return conversations

def load_lubi_data(jsonl_path: Path) -> List[Dict[str, Any]]:
    """Load and filter Lubi dataset"""
    conversations = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            msg = json.loads(line)
            # Filter: meaningful user/assistant content
            role = msg.get('role', '')
            content = msg.get('content', '')
            if role in ['user', 'assistant'] and content and len(content) > 50:
                conversations.append({
                    'source': 'lubit',
                    'session_id': msg['session_id'],
                    'role': role,
                    'content': content,
                    'timestamp': msg.get('timestamp', ''),
                    'session_timestamp': msg.get('session_timestamp', '')
                })
    return conversations

def convert_to_bqi_format(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert to BQI learning format (task-result pairs)"""
    bqi_entries = []
    
    # Group by conversation/session
    from collections import defaultdict
    conversations = defaultdict(list)
    
    for msg in data:
        conv_id = msg.get('conversation_id') or msg.get('session_id', 'unknown')
        conversations[conv_id].append(msg)
    
    # Extract task-result pairs
    for conv_id, messages in conversations.items():
        messages.sort(key=lambda x: x.get('timestamp') or '')
        
        for i in range(len(messages) - 1):
            if messages[i]['role'] == 'user' and messages[i+1]['role'] == 'assistant':
                task = messages[i]['content']
                result = messages[i+1]['content']
                
                # Skip if too short or empty
                if len(task) < 10 or len(result) < 10:
                    continue
                
                bqi_entries.append({
                    'task': task,
                    'result': result,
                    'source': messages[i]['source'],
                    'conversation_id': conv_id,
                    'timestamp': messages[i].get('timestamp', ''),
                    'task_length': len(task),
                    'result_length': len(result)
                })
    
    return bqi_entries

def main():
    workspace = Path(__file__).parent.parent.parent
    outputs_dir = workspace / 'outputs'
    
    # Load datasets
    print("Loading Rua dataset...")
    rua_path = outputs_dir / 'rua_dataset_parsed.jsonl'
    rua_data = load_rua_data(rua_path)
    print(f"  Loaded {len(rua_data)} Rua messages")
    
    print("Loading Lubi dataset...")
    lubi_path = outputs_dir / 'lubit_dataset_parsed.jsonl'
    lubi_data = load_lubi_data(lubi_path)
    print(f"  Loaded {len(lubi_data)} Lubi messages")
    
    # Combine
    all_data = rua_data + lubi_data
    print(f"\nTotal messages: {len(all_data)}")
    
    # Convert to BQI format
    print("\nConverting to BQI format...")
    bqi_entries = convert_to_bqi_format(all_data)
    print(f"  Generated {len(bqi_entries)} task-result pairs")
    
    # Save
    output_path = outputs_dir / 'trinity_bqi_training_data.jsonl'
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in bqi_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"\nSaved to: {output_path}")
    
    # Statistics
    rua_count = sum(1 for e in bqi_entries if e['source'] == 'rua')
    lubi_count = sum(1 for e in bqi_entries if e['source'] == 'lubit')
    
    stats = {
        'total_pairs': len(bqi_entries),
        'rua_pairs': rua_count,
        'lubi_pairs': lubi_count,
        'avg_task_length': sum(e['task_length'] for e in bqi_entries) / len(bqi_entries),
        'avg_result_length': sum(e['result_length'] for e in bqi_entries) / len(bqi_entries),
        'generated_at': datetime.now().isoformat()
    }
    
    stats_path = outputs_dir / 'trinity_bqi_stats.json'
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"\nStats saved to: {stats_path}")
    print(f"\nBreakdown:")
    print(f"  Rua pairs: {rua_count}")
    print(f"  Lubi pairs: {lubi_count}")
    print(f"  Avg task length: {stats['avg_task_length']:.0f} chars")
    print(f"  Avg result length: {stats['avg_result_length']:.0f} chars")

if __name__ == '__main__':
    main()
