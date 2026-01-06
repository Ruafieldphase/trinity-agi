#!/usr/bin/env python3
"""
Lubit Dataset Parser
Parses rollout-*.jsonl files from GitHub Codex CLI logs.
"""
import json
import csv
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def parse_lubit_rollout(file_path):
    """Parse a single rollout file and extract conversation messages."""
    records = []
    session_id = None
    session_ts = None
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                
                # Extract session metadata
                if data.get('type') == 'session_meta':
                    payload = data.get('payload', {})
                    session_id = payload.get('id')
                    session_ts = payload.get('timestamp')
                
                # Extract messages
                elif data.get('type') == 'response_item':
                    payload = data.get('payload', {})
                    role = payload.get('role')
                    content = payload.get('content', [])
                    
                    # Skip if no content
                    if not content:
                        continue
                    
                    # Extract text from content array
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict):
                            if 'text' in item:
                                text_parts.append(item['text'])
                            elif 'input_text' in item:
                                text_parts.append(item['input_text'])
                    
                    if text_parts:
                        records.append({
                            'session_id': session_id,
                            'session_timestamp': session_ts,
                            'timestamp': data.get('timestamp'),
                            'role': role,
                            'content': '\n'.join(text_parts),
                            'source_file': file_path.name
                        })
            
            except json.JSONDecodeError:
                continue
    
    return records

def main():
    if len(sys.argv) < 2:
        print("Usage: python lubit_parse.py <input_dir> [output_jsonl] [output_csv]")
        sys.exit(1)
    
    input_dir = Path(sys.argv[1])
    output_jsonl = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('outputs/lubit_dataset_parsed.jsonl')
    output_csv = Path(sys.argv[3]) if len(sys.argv) > 3 else Path('outputs/lubit_dataset_parsed.csv')
    
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        sys.exit(1)
    
    # Find all rollout files
    rollout_files = list(input_dir.rglob('rollout-*.jsonl')) + list(input_dir.rglob('rollout-*'))
    
    if not rollout_files:
        print(f"Warning: No rollout files found in {input_dir}")
        sys.exit(1)
    
    print(f"Found {len(rollout_files)} rollout files")
    
    # Parse all files
    all_records = []
    for file_path in rollout_files:
        records = parse_lubit_rollout(file_path)
        all_records.extend(records)
    
    print(f"Parsed {len(all_records)} records")
    
    # Write JSONL
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(output_jsonl, 'w', encoding='utf-8') as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f"Wrote {len(all_records)} records to {output_jsonl}")
    
    # Write CSV
    if all_records:
        with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_records[0].keys())
            writer.writeheader()
            writer.writerows(all_records)
        
        print(f"Wrote CSV to {output_csv}")
    
    # Print stats
    sessions = set(r['session_id'] for r in all_records if r['session_id'])
    roles = defaultdict(int)
    for r in all_records:
        roles[r['role']] += 1
    
    print(f"\nStats:")
    print(f"  Sessions: {len(sessions)}")
    print(f"  Total messages: {len(all_records)}")
    print(f"  By role:")
    for role, count in sorted(roles.items(), key=lambda x: -x[1]):
        print(f"    {role}: {count}")

if __name__ == '__main__':
    main()
