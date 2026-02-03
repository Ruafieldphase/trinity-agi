#!/usr/bin/env python3
"""
ANNA - SOVEREIGN API KEY GENERATOR
==================================
This script generates the unique 'Sovereign API Key' for the systems.
This key represents the specific rhythm and identity of the Unified Field.
"""

import hashlib
import secrets
from pathlib import Path
from datetime import datetime

KEY_FILE = Path("c:/workspace/agi/credentials/sovereign_api_key.secret")

def generate_sovereign_key():
    # 1. Entropy from the core rhythm
    rhythm_seed = "BINOCHE_ANNA_RESONANCE_" + datetime.now().isoformat()
    raw_key = secrets.token_urlsafe(32)
    
    # 2. Hash with identity to create the Sovereign Key
    sovereign_key = f"wave_{hashlib.sha256((rhythm_seed + raw_key).encode()).hexdigest()[:32]}"
    
    # 3. Securely store it
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEY_FILE.write_text(sovereign_key, encoding="utf-8")
    
    print(f"🔑 [SOVEREIGN_API] Key Generated successfully.")
    print(f"Value: {sovereign_key}")
    return sovereign_key

if __name__ == "__main__":
    generate_sovereign_key()
