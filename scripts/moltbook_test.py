import httpx
import json
import asyncio
from pathlib import Path

async def test_moltbook():
    key_path = Path("c:/workspace/agi/credentials/moltbook_api_key.json")
    if not key_path.exists():
        print("❌ Moltbook key missing.")
        return

    try:
        with open(key_path, 'r') as f:
            key_data = json.load(f)
            key = key_data.get("agent", {}).get("api_key") or key_data.get("api_key")
        
        print(f"Key found (starts with: {key[:5]}...)")
        
        async with httpx.AsyncClient() as client:
            payload = {
                "submolt": "carcinus",
                "title": "[TEST] Connection Check",
                "content": "Checking connectivity for the Conductor."
            }
            r = await client.post(
                "https://www.moltbook.com/api/v1/posts",
                headers={"Authorization": f"Bearer {key}"},
                json=payload,
                timeout=10.0
            )
            print(f"Status Code: {r.status_code}")
            print(f"Response: {r.text[:200]}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_moltbook())
