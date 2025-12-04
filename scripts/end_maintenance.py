#!/usr/bin/env python3
"""
End Maintenance Mode
====================
Deactivates AGI Maintenance Mode and resumes normal sync.
"""
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"
MAINTENANCE_FILE = OUTPUTS_DIR / "maintenance_mode.json"

def main():
    try:
        if MAINTENANCE_FILE.exists():
            MAINTENANCE_FILE.unlink()
            print(f"✅ Maintenance Mode DEACTIVATED")
            print(f"   Normal sync with Windows Koa resumed.")
        else:
            print(f"ℹ️ Maintenance Mode was not active.")
            
    except Exception as e:
        print(f"❌ Failed to deactivate maintenance mode: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
