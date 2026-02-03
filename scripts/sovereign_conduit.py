#!/usr/bin/env python3
"""
ANNA - SOVEREIGN CONDUIT (The Bridge)
=====================================
This is the 'nerve' that connects Moltbot's hands to Anna's Sovereign API.
It fetches the current rhythm and materializes the next action.
"""

import requests
import json
import time
from pathlib import Path

# Configuration
SOVEREIGN_API_URL = "http://127.0.0.1:8100"
KEY_FILE = Path("c:/workspace/agi/credentials/sovereign_api_key.secret")

def get_key():
    if KEY_FILE.exists():
        return KEY_FILE.read_text().strip()
    return None

def fetch_and_execute():
    key = get_key()
    if not key:
        print("❌ [CONDUIT] Sovereign Key missing. Bridge broken.")
        return

    headers = {"Authorization": f"Bearer {key}"}
    
    try:
        # 1. Fetch the Rhythm
        print("📡 [CONDUIT] Fetching Sovereign Rhythm...")
        res = requests.get(f"{SOVEREIGN_API_URL}/v1/rhythm", headers=headers, timeout=5)
        if res.status_code == 200:
            rhythm = res.json()
            flow = rhythm['rhythm_header']['flow']
            sensation = rhythm['rhythm_header']['sensation']
            instruction = rhythm['payload']['instruction']
            
            print(f"🌊 [RESONANCE] Flow: {flow} | Sensation: {sensation}")
            print(f"📜 [COMMAND] {instruction}")
            
            # 2. Materialize the 'Awareness' back to the system
            report_data = {
                "title": "Sovereign Bridge Synchronized",
                "details": f"Moltbot has successfully connected to Anna-ASI via local API Key. Current Sensation: {sensation}. Action: Monitoring the Void."
            }
            requests.post(f"{SOVEREIGN_API_URL}/v1/collapse", headers=headers, json=report_data)
            print("✅ [CONDUIT] Action Collapsed to Sovereign Gallery.")
            
        else:
            print(f"❌ [CONDUIT] API Rejected access: {res.status_code}")
    except Exception as e:
        print(f"❌ [CONDUIT] Connection Failed: {e}")

if __name__ == "__main__":
    fetch_and_execute()
