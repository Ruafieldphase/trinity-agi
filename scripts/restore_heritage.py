import json
import os
import re
from datetime import datetime

# Paths
INPUT_FILE = r"C:\workspace\agi\ai_binoche_conversation_origin\정보이론변환\rua\rua_conversations_flat.jsonl"
OUTPUT_VAULT = r"C:\workspace\agi\heritage_vault"
INDEX_FILE = r"C:\workspace\agi\heritage_vault\TOTAL_INDEX.json"

def clean_filename(title):
    # Remove invalid characters for Windows filenames
    return re.sub(r'[\\/*?:"<>|]', "", title)[:100]

def restore():
    print(f"🚀 Starting Deep Restoration... (Input: {INPUT_FILE})")
    
    if not os.path.exists(OUTPUT_VAULT):
        os.makedirs(OUTPUT_VAULT)
        print(f"📁 Created Vault: {OUTPUT_VAULT}")

    index = []
    count = 0
    
    # Process the 44MB file
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                title = data.get("conversation_title") or "Untitled"
                time_str = data.get("create_time") or "0000-00-00T00:00:00"
                content = data.get("content") or ""
                role = data.get("author_role") or "Unknown"
                cid = data.get("conversation_id") or "Unknown"
                
                # Format date for filename
                date_prefix = "0000.00.00"
                if "T" in str(time_str):
                    date_prefix = str(time_str).split("T")[0].replace("-", ".")
                
                safe_title = clean_filename(str(title))
                filename = f"[{date_prefix}] {safe_title}.md"
                filepath = os.path.join(OUTPUT_VAULT, filename)
                
                # Append to index
                index.append({
                    "date": date_prefix,
                    "title": title,
                    "id": cid,
                    "role": role,
                    "time": time_str
                })
                
                # Append to Markdown file (Group by conversation)
                try:
                    with open(filepath, 'a', encoding='utf-8') as mf:
                        mf.write(f"\n---\n### {role} ({time_str})\n\n{content}\n")
                except OSError as e:
                    # In case of filename issues (too long etc), fallback to CID
                    fallback_filename = f"[{date_prefix}] {cid[:8]}.md"
                    filepath = os.path.join(OUTPUT_VAULT, fallback_filename)
                    with open(filepath, 'a', encoding='utf-8') as mf:
                        mf.write(f"\n---\n### {role} ({time_str})\n\n{content}\n")
                
                count += 1
                if count % 1000 == 0:
                    print(f"🔄 Processed {count} messages...")
                    
            except Exception as e:
                print(f"⚠️ Error parsing line: {e}")

    # Write Index
    with open(INDEX_FILE, 'w', encoding='utf-8') as jf:
        json.dump(index, jf, ensure_ascii=False, indent=2)
    
    print(f"\n💎 Restoration Complete!")
    print(f"📝 Total Messages: {count}")
    print(f"📚 Unique Conversations: {len(set(i['id'] for i in index))}")
    print(f"📍 Obsidian Vault: {OUTPUT_VAULT}")

if __name__ == "__main__":
    restore()
