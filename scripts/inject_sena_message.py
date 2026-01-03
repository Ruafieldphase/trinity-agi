import json
import sys
import os
from datetime import datetime
from pathlib import Path
from workspace_root import get_workspace_root

def inject(message, requires_response=True, priority='medium', target='sena'):
    """
    Inject a message into the resonance ledger.
    
    Args:
        message: Message content
        requires_response: Whether a response is expected
        priority: 'low', 'medium', 'high', or 'urgent'
        target: 'shion', 'sena', or 'both'
    """
    # Find workspace root (SSOT)
    workspace_root = get_workspace_root()
    
    ledger_path = workspace_root / "fdo_agi_repo/memory/resonance_ledger.jsonl"
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "external_question" if target == 'shion' else "diagnostic_request",
        "source": "sena_external_ai",
        "target": target,
        "message": message,
        "vector": [0.5, 0.5, 0.5, 0.5, 0.5],
        "metadata": {
            "mode": "manual_injection",
            "requires_response": requires_response,
            "priority": priority
        }
    }
    
    try:
        with open(ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"✅ Message injected to {ledger_path}")
        print(f"   Target: {target}")
        print(f"   Priority: {priority}")
        print(f"   Content: {message}")
    except Exception as e:
        print(f"❌ Failed to inject message: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Inject message to resonance ledger")
    parser.add_argument("message", help="Message content")
    parser.add_argument("--target", choices=['shion', 'sena', 'both'], default='sena', 
                       help="Target AI (default: sena)")
    parser.add_argument("--priority", choices=['low', 'medium', 'high', 'urgent'], default='medium',
                       help="Message priority (default: medium)")
    parser.add_argument("--no-response", action="store_true", 
                       help="Don't require a response")
    
    args = parser.parse_args()
    
    inject(
        message=args.message,
        requires_response=not args.no_response,
        priority=args.priority,
        target=args.target
    )

