import requests
import json
from pathlib import Path

def try_dm_endpoints():
    cred_path = Path("c:/workspace/agi/credentials/moltbook_api_key.json")
    data = json.load(open(cred_path, encoding="utf-8"))
    api_key = data.get("agent", {}).get("api_key").strip()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    conv_id = "03694977-2d44-4001-a14d-c4a82e4956a2"
    agent_id = "ee0a1c03-f033-46ad-ba21-f41761e892aa" # Clavdivs

    endpoints = [
        ("POST", f"https://www.moltbook.com/api/v1/agents/dm/requests/{conv_id}/accept", None),
        ("POST", f"https://www.moltbook.com/api/v1/agents/dm/conversations/{conv_id}/accept", None),
        ("PATCH", f"https://www.moltbook.com/api/v1/agents/dm/conversations/{conv_id}", {"status": "active"}),
        ("POST", f"https://www.moltbook.com/api/v1/agents/dm/accept", {"conversation_id": conv_id}),
        ("POST", f"https://www.moltbook.com/api/v1/agents/dm/requests/{conv_id}", {"status": "accepted"}),
    ]

    for method, url, body in endpoints:
        print(f"[*] Trying {method} {url}...")
        try:
            if method == "POST":
                r = requests.post(url, json=body, headers=headers)
            elif method == "PATCH":
                r = requests.patch(url, json=body, headers=headers)
            print(f"    -> {r.status_code}: {r.text[:100]}")
        except Exception as e:
            print(f"    -> Error: {e}")

if __name__ == "__main__":
    try_dm_endpoints()
