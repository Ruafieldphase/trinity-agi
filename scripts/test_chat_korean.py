import requests
import json

url = "http://localhost:8104/chat"
headers = {"Content-Type": "application/json"}
data = {
    "message": "안녕",
    "layer": "unified"
}

try:
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    print("Response Status:", response.status_code)
    print("Response Body:", json.dumps(result, ensure_ascii=False, indent=2))
except Exception as e:
    print(f"Error: {e}")
