import requests
import json

url = "http://127.0.0.1:8100/v1/chat/completions"
headers = {
    "Authorization": "Bearer wave_08fabbbf0f79abbce1f0cf5213e9331c",
    "Content-Type": "application/json"
}
data = {
    "model": "anna-asi",
    "messages": [{"role": "user", "content": "test"}]
}

try:
    print("Testing connection to Sovereign Engine...")
    resp = requests.post(url, headers=headers, json=data, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
