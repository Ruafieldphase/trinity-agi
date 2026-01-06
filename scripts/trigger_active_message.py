import requests
import json
import sys

# Default message
message = "비노체, 지금 시스템 리소스가 안정적이에요. 혹시 새로운 작업을 시작할까요?"

# Allow command line argument override
if len(sys.argv) > 1:
    message = sys.argv[1]

url = "http://localhost:3005/trigger"
headers = {"Content-Type": "application/json"}
data = {
    "sender": "Trinity",
    "message": message,
    "type": "text"
}

try:
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    print(f"✅ Triggered message: {message}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"❌ Failed to trigger message: {e}")
