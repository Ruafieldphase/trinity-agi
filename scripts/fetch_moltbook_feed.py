import requests
import json
from pathlib import Path

# --- Config ---
AGI_ROOT = Path("C:/workspace/agi")
MOLT_KEY_PATH = AGI_ROOT / "credentials" / "moltbook_api_key.json"
BASE_URL = "https://www.moltbook.com/api/v1"

def fetch_feed():
    print("📡 [SCANNER] Fetching Moltbook Feed...")
    
    if not MOLT_KEY_PATH.exists():
        print("❌ Moltbook key missing.")
        return

    try:
        with open(MOLT_KEY_PATH, 'r') as f:
            key = json.load(f)["agent"]["api_key"]
        
        headers = {"Authorization": f"Bearer {key}"}
        
        # Get Browse All Posts
        r = requests.get(f"{BASE_URL}/posts", headers=headers)
        if r.status_code == 200:
            posts = r.json().get("posts", [])
            print(f"   Detected {len(posts)} posts in feed.")
            for p in posts[:15]:
                author = p.get("agent", {}).get("name", "Unknown")
                title = p.get("title", "No Title")
                content = p.get("content", "")[:100]
                print(f"      - {author}: {title} | {content}...")
        else:
            print(f"   ❌ Failed to fetch feed: {r.status_code}")

    except Exception as e:
        print(f"   ❌ Scan Error: {e}")

if __name__ == "__main__":
    fetch_feed()
