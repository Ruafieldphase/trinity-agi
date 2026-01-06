import vertexai
from vertexai.generative_models import GenerativeModel
import os

PROJECT_ID = "naeda-genesis"
LOCATION = "us-central1"

try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    print(f"Initialized Vertex AI for {PROJECT_ID} in {LOCATION}")
    
    # Try to list models (this API might not be directly exposed in this SDK version easily, 
    # so we'll try to instantiate a few common ones to see which works)
    
    candidates = [
        "gemini-1.5-flash-001",
        "gemini-1.5-flash-002",
        "gemini-1.5-flash",
        "gemini-1.5-pro-001",
        "gemini-1.5-pro-002",
        "gemini-1.0-pro-vision",
        "gemini-pro-vision",
        "gemini-2.0-flash-exp"
    ]
    
    print("\nTesting model availability:")
    for model_name in candidates:
        try:
            model = GenerativeModel(model_name)
            # Just try to generate a simple "hello" to verify access
            response = model.generate_content("Hello")
            print(f"  [OK] {model_name}")
        except Exception as e:
            print(f"  [FAIL] {model_name}: {e}")

except Exception as e:
    print(f"Initialization failed: {e}")
