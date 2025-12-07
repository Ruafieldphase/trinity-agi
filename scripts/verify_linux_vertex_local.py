import os
import sys
from google.cloud import aiplatform

# Set credentials explicitly
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/bino/agi/config/naeda-genesis-5034a5936036.json"
os.environ["VERTEX_PROJECT_ID"] = "naeda-genesis"
os.environ["VERTEX_LOCATION"] = "us-central1"

print(f"Checking credentials at: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")

try:
    if not os.path.exists(os.environ["GOOGLE_APPLICATION_CREDENTIALS"]):
        print(f"❌ Credential file not found at {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
        sys.exit(1)

    aiplatform.init(project="naeda-genesis", location="us-central1")
    print("✅ Vertex AI Initialized successfully")
    
    # Try a simple generative model call if possible, or just list models
    # For now, initialization is a good enough check for auth
    
except Exception as e:
    print(f"❌ Vertex AI Initialization failed: {e}")
    sys.exit(1)
