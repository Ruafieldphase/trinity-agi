import json
from pathlib import Path

# --- Config ---
HERITAGE_DIR = Path("C:/workspace/agi/ai_binoche_conversation_origin/rua/rua_conversation_original")
KEYWORDS = ["리듬", "공명", "시안", "비노체", "위상"]

def harvest_heritage():
    print("🧬 [HARVESTER] Harvesting Heritage Insights from Rua Archives...")
    results = []
    
    for json_file in HERITAGE_DIR.glob("conversations-*.json"):
        print(f"   Searching {json_file.name}...")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for conv in data:
                    title = conv.get("title", "Untitled")
                    mapping = conv.get("mapping", {})
                    for node_id, node in mapping.items():
                        msg = node.get("message")
                        if msg and msg.get("content"):
                            parts = msg["content"].get("parts", [])
                            for part in parts:
                                if isinstance(part, str):
                                    for kw in KEYWORDS:
                                        if kw in part:
                                            # Clean snippet
                                            snippet = part[:300].replace("\n", " ").strip()
                                            results.append({
                                                "file": json_file.name,
                                                "title": title,
                                                "keyword": kw,
                                                "text": snippet
                                            })
                                            if len(results) >= 50: # Limit result count
                                                return results
        except Exception as e:
            print(f"   ❌ Error reading {json_file.name}: {e}")
            
    return results

if __name__ == "__main__":
    snippets = harvest_heritage()
    with open("C:/workspace/agi/outputs/heritage_harvest.json", "w", encoding="utf-8") as f:
        json.dump(snippets, f, indent=2, ensure_ascii=False)
    print(f"✅ Harvested {len(snippets)} snippets to outputs/heritage_harvest.json")
