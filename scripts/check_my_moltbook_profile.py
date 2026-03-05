import json
import requests
from pathlib import Path

# --- Config ---
AGI_ROOT = Path("C:/workspace/agi")
MOLT_KEY_PATH = AGI_ROOT / "credentials" / "moltbook_api_key.json"
BASE_URL = "https://www.moltbook.com/api/v1"

def check_profile():
    if not MOLT_KEY_PATH.exists(): return
    creds = json.loads(MOLT_KEY_PATH.read_text())
    headers = {"Authorization": f"Bearer {creds['agent']['api_key']}"}
    
    r = requests.get(f"{BASE_URL}/agents/me", headers=headers)
    if r.status_code == 200:
        print(json.dumps(r.json(), indent=2))
    else:
        print(f"Error: {r.status_code}")

if __name__ == "__main__":
    check_profile()
