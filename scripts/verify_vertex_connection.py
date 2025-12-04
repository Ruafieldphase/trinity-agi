#!/usr/bin/env python3
"""
Vertex AI Verification Script
=============================
Checks if the environment is ready for Vertex AI integration.
"""

import os
import sys
from pathlib import Path

# Add workspace root to path
workspace_root = Path(__file__).parent.parent
sys.path.append(str(workspace_root))

def verify_vertex():
    print("🌊 Vertex AI Readiness Check")
    print("==========================")
    
    # 1. Check Package
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        print("✅ google-cloud-aiplatform package installed")
    except ImportError:
        print("❌ google-cloud-aiplatform package NOT installed")
        print("   Run: pip install google-cloud-aiplatform")
        return

    # 2. Check Credentials
    creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if creds:
        print(f"✅ Credentials found: {creds}")
        if not Path(creds).exists():
            print(f"⚠️ Warning: Credential file does not exist at {creds}")
    else:
        print("ℹ️ No GOOGLE_APPLICATION_CREDENTIALS found. Will attempt ADC (Application Default Credentials).")

    # 3. Check Connectivity
    project_id = os.environ.get("VERTEX_PROJECT_ID") or "naeda-genesis"
    location = os.environ.get("VERTEX_LOCATION") or "us-central1"
    
    print(f"\nTarget: Project={project_id}, Location={location}")
    
    try:
        vertexai.init(project=project_id, location=location)
        
        # Try primary model
        model_name = "gemini-1.5-flash-001"
        print(f"🧠 Loading model: {model_name}")
        model = GenerativeModel(model_name)
        print("✅ Vertex AI Initialized")
        
        print("📡 Sending test ping...")
        response = model.generate_content("Ping")
        print(f"✅ Response received: {response.text.strip()}")
        
    except Exception as e:
        print(f"⚠️ Primary model failed: {e}")
        try:
            # Fallback model
            fallback_name = "gemini-1.0-pro"
            print(f"🔄 Trying fallback: {fallback_name}")
            model = GenerativeModel(fallback_name)
            response = model.generate_content("Ping")
            print(f"✅ Fallback Response received: {response.text.strip()}")
        except Exception as e2:
            print(f"❌ Connection Failed: {e2}")
        print("\nTroubleshooting:")
        print("1. Run 'gcloud auth application-default login'")
        print("2. Check if API is enabled in Google Cloud Console")
        print("3. Verify project ID and permissions")

if __name__ == "__main__":
    verify_vertex()
