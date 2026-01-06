
import os
import json
import requests
import google.auth
from google.auth.transport.requests import Request

def test_rest_api():
    print("--- Vertex AI REST API Diagnostic ---")
    
    # 1. Get Access Token
    try:
        scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        credentials, project = google.auth.default(scopes=scopes)
        credentials.refresh(Request())
        token = credentials.token
        print(f"✅ Authenticated as: {credentials.service_account_email}")
        print(f"✅ Project ID: {project}")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return

    # 2. Define Endpoint
    # User provided: https://aiplatform.googleapis.com/v1/projects/naeda-genesis/locations/global/publishers/google/models/gemini-3-pro-preview:streamGenerateContent
    
    location = "global"
    project_id = "naeda-genesis"
    model_id = "gemini-3-pro-preview"
    
    # Note: Using streamGenerateContent as per user report, but generateContent is usually easier for single request.
    # Let's try generateContent first as it returns a simpler JSON.
    url = f"https://aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model_id}:generateContent"
    
    print(f"\nTarget URL: {url}")
    
    # 3. Prepare Payload
    payload = {
        "contents": [{
            "role": "user",
            "parts": [{"text": "Hello, are you awake?"}]
        }]
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 4. Send Request
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ SUCCESS! Response: {response.json()}")
        else:
            print(f"❌ FAILED. Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_rest_api()
