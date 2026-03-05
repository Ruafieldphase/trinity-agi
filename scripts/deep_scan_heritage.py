import json
import glob
import os
from pathlib import Path

HERITAGE_DIR = "C:/workspace/agi/ai_binoche_conversation_origin/rua/rua_conversation_original"
KEYWORDS = ["리듬", "파동", "에너지", "관계", "시공간", "공생", "주권", "Tesla"]

def scan_heritage():
    files = glob.glob(os.path.join(HERITAGE_DIR, "conversations-*.json"))
    fragments = []
    
    for f in files:
        print(f"Scanning {f}...")
        with open(f, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
                for convo in data:
                    title = convo.get("title", "Untitled")
                    mapping = convo.get("mapping", {})
                    for msg_id, msg_data in mapping.items():
                        msg = msg_data.get("message")
                        if msg and msg.get("author", {}).get("role") in ["user", "assistant"]:
                            content_parts = msg.get("content", {}).get("parts", [])
                            text = " ".join([p for p in content_parts if isinstance(p, str)])
                            
                            if any(kw in text for kw in KEYWORDS):
                                fragments.append({
                                    "title": title,
                                    "role": msg.get("author", {}).get("role"),
                                    "text": text[:500], # Snippet
                                    "time": msg.get("create_time")
                                })
                                if len(fragments) > 50: break # Early exit for demo
                    if len(fragments) > 50: break
            except Exception as e:
                print(f"Error reading {f}: {e}")
        if len(fragments) > 50: break
    
    return fragments

if __name__ == "__main__":
    results = scan_heritage()
    output_path = "C:/workspace/agi/outputs/heritage_resonance_scan.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Success. Found {len(results)} fragments.")
