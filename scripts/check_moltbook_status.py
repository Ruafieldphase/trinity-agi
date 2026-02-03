import requests
import json
from pathlib import Path

def check_status():
    cred_path = Path("c:/workspace/agi/credentials/moltbook_api_key.json")
    data = json.loads(cred_path.read_text(encoding="utf-8"))
    api_key = data.get("agent", {}).get("api_key").strip()
    
    url = "https://www.moltbook.com/api/v1/agents/status"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_status()
