import json
import os
import glob
from datetime import datetime

base_path = r"C:\workspace\agi\ai_binoche_conversation_origin\rua\rua_conversation_original"
json_files = glob.glob(os.path.join(base_path, "conversations-*.json"))

history_summary = []

for file_path in json_files:
    print(f"Processing {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for conv in data:
                title = conv.get('title', 'Untitled')
                create_time = conv.get('create_time', 0)
                update_time = conv.get('update_time', 0)
                
                # Convert timestamps
                try:
                    c_time_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S') if create_time else "Unknown"
                except:
                    c_time_str = "Unknown"
                
                history_summary.append({
                    "title": title,
                    "created_at": c_time_str,
                    "id": conv.get('conversation_id', ''),
                    "raw_create_time": create_time
                })
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

# Sort by creation time
history_summary.sort(key=lambda x: x['raw_create_time'])

with open('rua_history_timeline.json', 'w', encoding='utf-8') as f:
    json.dump(history_summary, f, ensure_ascii=False, indent=2)

print(f"Successfully extracted {len(history_summary)} conversation titles to rua_history_timeline.json")
