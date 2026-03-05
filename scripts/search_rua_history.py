import json
import os
import glob
import re

base_path = r"C:\workspace\agi\ai_binoche_conversation_origin\rua\rua_conversation_original"
json_files = glob.glob(os.path.join(base_path, "conversations-*.json"))

keywords = [
    "퍼즐", "실험", "공생", "리듬", "대칭", "정보이론", 
    "resonance", "trinity", "binoche", "rhythm", "symmetry", 
    "coexistence", "puzzle", "experiment", "identity", "ego",
    "unconscious", "무의식", "시발점", "성장", "갈등"
]

results = []

def search_in_mapping(mapping, conv_title):
    found_snippets = []
    for node_id, node in mapping.items():
        message = node.get('message')
        if message and message.get('content') and message['content'].get('parts'):
            parts = message['content']['parts']
            for part in parts:
                if isinstance(part, str):
                    for kw in keywords:
                        if kw.lower() in part.lower():
                            # Extract a snippet around the keyword
                            idx = part.lower().find(kw.lower())
                            start = max(0, idx - 100)
                            end = min(len(part), idx + 200)
                            found_snippets.append({
                                "keyword": kw,
                                "snippet": part[start:end].replace('\n', ' '),
                                "role": message.get('author', {}).get('role', 'unknown')
                            })
                            break # Move to next part after finding one keyword to avoid too much noise
    return found_snippets

for file_path in json_files:
    print(f"Searching in {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for conv in data:
                title = conv.get('title', 'Untitled')
                mapping = conv.get('mapping', {})
                snippets = search_in_mapping(mapping, title)
                if snippets:
                    results.append({
                        "title": title,
                        "conversation_id": conv.get('conversation_id'),
                        "create_time": conv.get('create_time'),
                        "snippets": snippets[:5] # Limit to 5 snippets per conversation
                    })
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

# Save results
with open('rua_keyword_search.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Search complete. Found relevant content in {len(results)} conversations.")
