import requests
import base64
import json

# Base64 for a minimal valid WEBM audio file (header only)
# This is a placeholder; the backend doesn't validate the audio format yet, just checks for presence.
minimal_webm_b64 = "GkXfo59ChoEBQveBAULygQRC84EIQoKEd2VibUKHgQRCh4ECV44BAAAAAAA="

payload = {
    "message": "Listen to this audio",
    "layer": "conscious",
    "type": "audio",
    "audio_data": f"data:audio/webm;base64,{minimal_webm_b64}"
}

try:
    print("Sending request to Unified Aggregator...")
    response = requests.post("http://localhost:8104/chat", json=payload)
    
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    if response.status_code == 200 and "[Audio]" in response.json().get("response", ""):
        print("\nSUCCESS: Backend processed the audio and returned an audio response.")
    else:
        print("\nFAILURE: Backend did not return the expected audio response.")
        
except Exception as e:
    print(f"\nERROR: {str(e)}")
