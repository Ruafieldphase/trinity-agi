import requests
import json
from pathlib import Path

def list_feed_ids():
    cred_path = Path("c:/workspace/agi/credentials/moltbook_api_key.json")
    data = json.load(open(cred_path, encoding="utf-8"))
    api_key = data.get("agent", {}).get("api_key").strip()
    headers = {"Authorization": f"Bearer {api_key}"}

    url = "https://www.moltbook.com/api/v1/feed?sort=hot"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        posts = r.json().get("posts", [])
        for p in posts:
            print(f"ID: {p['id']} | TITLE: {p['title']}")
    else:
        print(f"Error: {r.status_code}")

if __name__ == "__main__":
    list_feed_ids()
