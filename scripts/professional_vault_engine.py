import json
import os
import re
from datetime import datetime

# Paths
SOURCE_DIR = r"C:\workspace\agi\ai_binoche_conversation_origin"
VAULT_DIR = r"C:\workspace\agi\heritage_vault"
INDEX_FILE = r"C:\workspace\agi\heritage_vault\KNOWLEDGE_INDEX.json"

# Auto-classification rules
RULES = {
    "Lua": ["루아", "lua", "감응", "정(精)"],
    "Ello": ["엘로", "ello", "구조", "반(反)"],
    "Lumen": ["루멘", "lumen", "통합", "합(合)", "지성"],
    "Theory": ["정보이론", "리듬", "FIF", "FIF_CORE", "통일장"],
    "Failure": ["실패", "장벽", "연극", "vertex"]
}

def clean_filename(title):
    # Remove newlines and replace with space, then strip
    t = str(title).replace("\n", " ").replace("\r", " ").strip()
    # Remove invalid characters for Windows filenames
    return re.sub(r'[\\/*?:"<>|]', "", t)[:100]

def get_tags(title, content):
    tags = []
    text = (str(title) + " " + str(content)).lower()
    for tag, keywords in RULES.items():
        if any(kw.lower() in text for kw in keywords):
            tags.append(f"#{tag}")
    return tags

def process_vault():
    print(f"🚀 Initializing Professional Knowledge System Transformation...")
    if not os.path.exists(VAULT_DIR):
        os.makedirs(VAULT_DIR)

    all_logs = []
    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.endswith(".jsonl"):
                all_logs.append(os.path.join(root, file))

    print(f"🔍 Found {len(all_logs)} .jsonl files. Starting deep scan...")

    total_messages = 0
    unique_conversations = {}

    for log_path in all_logs:
        with open(log_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    cid = data.get("conversation_id", "Unknown")
                    if cid not in unique_conversations:
                        unique_conversations[cid] = {
                            "title": data.get("conversation_title") or "Untitled",
                            "time": data.get("create_time") or "0000-00-00T00:00:00",
                            "messages": []
                        }
                    
                    unique_conversations[cid]["messages"].append({
                        "role": data.get("author_role") or "Unknown",
                        "content": data.get("content") or "",
                        "time": data.get("create_time") or "Unknown"
                    })
                    total_messages += 1
                except Exception:
                    continue

    print(f"🛰️  Aggregation complete. Generating {len(unique_conversations)} knowledge nodes...")

    # Sort and Export
    for cid, data in unique_conversations.items():
        title = data["title"]
        time_str = data["time"]
        messages = data["messages"]
        
        # Sort messages by time if possible
        messages.sort(key=lambda x: x.get("time", ""))
        
        date_prefix = "0000.00.00"
        if "T" in str(time_str):
            date_prefix = str(time_str).split("T")[0].replace("-", ".")
        
        safe_title = clean_filename(title)
        filename = f"[{date_prefix}] {safe_title}.md"
        filepath = os.path.join(VAULT_DIR, filename)
        
        # Build YAML and Content
        all_content = " ".join([m["content"] for m in messages])
        tags = get_tags(title, all_content)
        
        frontmatter = f"---\ntitle: \"{title}\"\ndate: {date_prefix.replace('.', '-')}\ncid: \"{cid}\"\ntags: {json.dumps(tags, ensure_ascii=False)}\n---\n\n"
        
        with open(filepath, 'w', encoding='utf-8') as mf:
            mf.write(frontmatter)
            for m in messages:
                mf.write(f"\n---\n### {m['role']} ({m['time']})\n\n{m['content']}\n")

    print(f"\n💎 Sovereign Archive Complete!")
    print(f"📝 Total Messages: {total_messages}")
    print(f"📚 Unique Nodes: {len(unique_conversations)}")
    print(f"📍 Vault: {VAULT_DIR}")

if __name__ == "__main__":
    process_vault()
