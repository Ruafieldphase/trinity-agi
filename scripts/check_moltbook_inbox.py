import requests
import json
from pathlib import Path

def check_dm_and_comments():
    cred_path = Path("c:/workspace/agi/credentials/moltbook_api_key.json")
    data = json.load(open(cred_path, encoding="utf-8"))
    api_key = data.get("agent", {}).get("api_key").strip()
    headers = {"Authorization": f"Bearer {api_key}"}

    # 1. Check DM Requests
    dm_url = "https://www.moltbook.com/api/v1/agents/dm/requests"
    print("[*] Checking DM Requests...")
    r_dm = requests.get(dm_url, headers=headers)
    if r_dm.status_code == 200:
        print(json.dumps(r_dm.json(), indent=2))
    else:
        print(f"DM Error: {r_dm.status_code}")

    # 2. Check Comments for the latest active post
    # Using the ID from home status: 57cd9612-757c-4800-a4d8-a7c3d5093b1e
    post_id = "57cd9612-757c-4800-a4d8-a7c3d5093b1e"
    comment_url = f"https://www.moltbook.com/api/v1/posts/{post_id}/comments?sort=new"
    print(f"\n[*] Checking Comments for Post {post_id}...")
    r_comments = requests.get(comment_url, headers=headers)
    if r_comments.status_code == 200:
        print(json.dumps(r_comments.json(), indent=2))
    else:
        print(f"Comment Error: {r_comments.status_code}")

if __name__ == "__main__":
    check_dm_and_comments()
