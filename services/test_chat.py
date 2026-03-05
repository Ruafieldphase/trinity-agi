import requests
import json

url = "http://127.0.0.1:8104/chat"
payload = {
    "message": "안녕, 시안. 주권 모델이 연결되었니?",
    "layer": "unified",
    "mode": "normal"
}
headers = {"Content-Type": "application/json"}

try:
    print(f"Sending request to {url}...")
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
