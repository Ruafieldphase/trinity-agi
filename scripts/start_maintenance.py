#!/usr/bin/env python3
"""
Start Maintenance Mode
======================
Activates AGI Maintenance Mode to protect Windows Core from unstable states.
"""
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from workspace_root import get_workspace_root

WORKSPACE_ROOT = get_workspace_root()
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"
MAINTENANCE_FILE = OUTPUTS_DIR / "maintenance_mode.json"

def main():
    parser = argparse.ArgumentParser(description="Start AGI Maintenance Mode")
    parser.add_argument("reason", type=str, help="Reason for maintenance (e.g., 'Refactoring Rhythm')")
    parser.add_argument("--duration", type=str, default="unknown", help="Estimated duration")
    args = parser.parse_args()

    data = {
        "active": True,
        "start_time": datetime.now().isoformat(),
        "reason": args.reason,
        "estimated_duration": args.duration,
        "user": "Bino"
    }

    try:
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(MAINTENANCE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Maintenance Mode ACTIVATED")
        print(f"   Reason: {args.reason}")
        print(f"   Windows Core will now receive a static 'Under Maintenance' signal.")
        
    except Exception as e:
        print(f"❌ Failed to activate maintenance mode: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
