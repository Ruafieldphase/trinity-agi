#!/usr/bin/env python3
"""
Sena Notification Bridge
========================
This script bridges the gap between the 'unconscious' resonance ledger
and the 'conscious' Sena (Claude Desktop App).

It monitors the ledger for new messages from Shion/System targeting Sena,
and displays a clear, copy-pasteable notification for the user to give to Sena.

Usage:
    python scripts/bridge_to_sena.py
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime

LEDGER_PATH = Path("fdo_agi_repo/memory/resonance_ledger.jsonl")
LAST_READ_FILE = Path("outputs/sena/.last_bridge_read")

def get_last_read_time():
    if LAST_READ_FILE.exists():
        return LAST_READ_FILE.read_text().strip()
    return None

def save_last_read_time(timestamp):
    LAST_READ_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_READ_FILE.write_text(timestamp)

def monitor_ledger():
    print("🌉 Sena Notification Bridge Started")
    print("   Monitoring resonance_ledger.jsonl for messages to Sena...")
    print("   (Press Ctrl+C to stop)")
    print("-" * 60)

    last_read = get_last_read_time()
    
    # If first run, start from now to avoid flooding
    if not last_read:
        last_read = datetime.now().isoformat()
        save_last_read_time(last_read)

    try:
        while True:
            if LEDGER_PATH.exists():
                with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                new_messages = []
                for line in lines:
                    try:
                        entry = json.loads(line)
                        timestamp = entry.get('timestamp')
                        
                        if timestamp <= last_read:
                            continue
                            
                        # Filter for messages targeting Sena or relevant system events
                        target = entry.get('target')
                        source = entry.get('source')
                        msg_type = entry.get('type')
                        
                        is_relevant = (
                            target == 'sena' or 
                            target == 'both' or
                            (source == 'antigravity_agent' and msg_type == 'autonomous_response')
                        )
                        
                        if is_relevant:
                            new_messages.append(entry)
                            
                    except json.JSONDecodeError:
                        continue
                
                if new_messages:
                    print(f"\n🔔 New Message for Sena ({len(new_messages)})")
                    print("=" * 60)
                    
                    for msg in new_messages:
                        print(f"From: {msg.get('source')}")
                        print(f"Type: {msg.get('type')}")
                        print(f"Message:\n{msg.get('message')}")
                        print("-" * 60)
                        
                        # Update last read to this message's timestamp
                        last_read = msg.get('timestamp')
                        save_last_read_time(last_read)
                    
                    print("👉 Please copy the above message to Sena (Claude Desktop Window)")
                    print("=" * 60)
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n👋 Bridge stopped")

if __name__ == "__main__":
    monitor_ledger()
