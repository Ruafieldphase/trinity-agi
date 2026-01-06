#!/usr/bin/env python3
"""
Verify Vertex AI Connection on Linux
====================================
Runs on Windows, connects to Linux via SSH, and executes a verification script.
"""
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))
from credentials_manager import get_linux_vm_credentials

import paramiko

def verify():
    print("🔍 Verifying Vertex AI on Linux...")
    
    creds = get_linux_vm_credentials()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(creds['host'], username=creds['user'], password=creds['password'])
        
        # Create a simple verification script on Linux
        verify_script = """
import os
from google.cloud import aiplatform

# Set credentials explicitly just in case env var isn't picked up yet
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/bino/agi/config/naeda-genesis-5034a5936036.json"
os.environ["VERTEX_PROJECT_ID"] = "naeda-genesis"
os.environ["VERTEX_LOCATION"] = "us-central1" # Or global

print(f"Checking credentials at: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")

try:
    aiplatform.init(project="naeda-genesis", location="us-central1")
    print("✅ Vertex AI Initialized successfully")
    
    # List models (lightweight check)
    # models = aiplatform.Model.list()
    # print(f"✅ Found {len(models)} models")
    
except Exception as e:
    print(f"❌ Vertex AI Initialization failed: {e}")
"""
        
        # Execute python code directly
        cmd = f"/home/bino/venv/bin/python -c '{verify_script}'"
        stdin, stdout, stderr = client.exec_command(cmd)
        
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        print("\n[Linux Output]")
        print(output)
        
        if error:
            print("\n[Linux Error]")
            print(error)
            
        if "Initialized successfully" in output:
            print("\n✨ Verification PASSED!")
        else:
            print("\n❌ Verification FAILED")

        client.close()

    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    verify()
