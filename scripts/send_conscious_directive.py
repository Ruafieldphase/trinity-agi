#!/usr/bin/env python3
"""
Send Conscious Directive
========================
Allows the Conscious Layer (User) to send a directive to the Unconscious (Rhythm System).
This completes the Top-Down Feedback Loop.

Usage:
    python scripts/send_conscious_directive.py "Focus on stability"
"""

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).parent.parent
LEDGER_FILE = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"

def send_directive(message: str, source: str = "user"):
    """Send a directive to the ledger."""
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "command",
        "source": source,
        "target": "rhythm_system",
        "message": message,
        "metadata": {
            "priority": "high",
            "intent": "conscious_bias"
        }
    }
    
    try:
        LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LEDGER_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        print(f"✅ Directive sent: '{message}'")
        print(f"   (The Unconscious will pick this up in the next cycle)")
    except Exception as e:
        print(f"❌ Failed to send directive: {e}")

def main():
    parser = argparse.ArgumentParser(description="Send a Conscious Directive")
    parser.add_argument("message", help="The directive message (e.g., 'Stabilize the system')")
    parser.add_argument("--source", default="user", help="Source of the directive (default: user)")
    
    args = parser.parse_args()
    
    send_directive(args.message, args.source)

if __name__ == "__main__":
    main()
