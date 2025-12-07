import requests
import base64
import json

# Create a simple 1x1 pixel red image
# Base64 for a 1x1 red PNG
red_pixel_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="

payload = {
    "message": "Look at this red pixel",
    "layer": "unified",
    "type": "image",
    "image_data": f"data:image/png;base64,{red_pixel_b64}"
}

try:
    print("Sending request to Unified Aggregator...")
    response = requests.post("http://localhost:8104/chat", json=payload)
    
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    if response.status_code == 200:
        print("\nSUCCESS: Backend processed the request.")
    else:
        print("\nFAILURE: Backend did not return the expected vision response.")
        
except Exception as e:
    print(f"\nERROR: {str(e)}")
