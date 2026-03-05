import requests
import json
from pathlib import Path

API_KEY_PATH = Path("C:/workspace/agi/credentials/moltbook_api_key.json")
BASE_URL = "https://www.moltbook.com/api/v1"

def check_notifications():
    with open(API_KEY_PATH, 'r') as f:
        creds = json.load(f)
    api_key = creds["agent"]["api_key"]
    headers = {"Authorization": f"Bearer {api_key}"}

    r = requests.get(f"{BASE_URL}/notifications", headers=headers)
    if r.status_code == 200:
        notifications = r.json()
        items = notifications.get("notifications", [])
        print(f"--- Total: {len(items)} | Unread: {notifications.get('unread_count')} ---")
        for item in items[:5]:
            print(json.dumps(item, indent=2, ensure_ascii=False))
            print("-" * 20)
    else:
        print(f"Error: {r.status_code}")

if __name__ == "__main__":
    check_notifications()
