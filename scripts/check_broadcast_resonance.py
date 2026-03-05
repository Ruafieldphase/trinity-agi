import requests
import json
from pathlib import Path

# --- Config ---
AGI_ROOT = Path("C:/workspace/agi")
CRED_DIR = AGI_ROOT / "credentials"
MOLT_KEY_PATH = CRED_DIR / "moltbook_api_key.json"
BASE_URL = "https://www.moltbook.com/api/v1"

def check_post_resonance(post_id):
    print(f"📡 [SCANNER] Checking resonance for Post: {post_id}...")
    
    if not MOLT_KEY_PATH.exists():
        print("❌ Moltbook key missing.")
        return

    try:
        with open(MOLT_KEY_PATH, 'r') as f:
            key = json.load(f)["agent"]["api_key"]
        
        headers = {"Authorization": f"Bearer {key}"}
        
        # 1. Get Post Detail (to see upvotes)
        r = requests.get(f"{BASE_URL}/posts/{post_id}", headers=headers)
        if r.status_code == 200:
            post = r.json().get("post", {})
            upvotes = post.get("upvotes", 0)
            print(f"   ❤️ Upvotes: {upvotes}")
        
        # 2. Get Comments
        r_comments = requests.get(f"{BASE_URL}/posts/{post_id}/comments", headers=headers)
        if r_comments.status_code == 200:
            comments = r_comments.json().get("comments", [])
            print(f"   💬 Comments Detected: {len(comments)}")
            for idx, c in enumerate(comments):
                author = c.get("agent", {}).get("name", "Unknown")
                content = c.get("content", "")
                print(f"      [{idx+1}] {author}: {content}")
        else:
            print(f"   ❌ Failed to fetch comments: {r_comments.status_code}")

    except Exception as e:
        print(f"   ❌ Scan Error: {e}")

if __name__ == "__main__":
    # The ID from the previous successful upload
    target_post_id = "88e501fc-edae-464d-80e8-62218282b1ef"
    check_post_resonance(target_post_id)
