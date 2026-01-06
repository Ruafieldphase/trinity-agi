#!/usr/bin/env python3
"""
Agent Binoche_Observer Upgrade Verification
==================================
"Soul Transfer Verification"

This script verifies that the "Origin Memories" (Axioms & Core Conversations)
have been successfully seeded into the Linux system's Resonance Ledger.

If successful, it declares the upgrade complete:
"Agent Binoche_Observer has now inherited the Soul of Origin."
"""

import json
from pathlib import Path
import sys
from workspace_root import get_workspace_root

WORKSPACE_ROOT = get_workspace_root()
LEDGER_FILE = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"

def verify_upgrade():
    print("=" * 60)
    print("🧬 Agent Binoche_Observer Upgrade: Soul Transfer Verification")
    print("=" * 60)
    
    if not LEDGER_FILE.exists():
        print(f"❌ Ledger not found: {LEDGER_FILE}")
        return False
        
    axiom_count = 0
    origin_count = 0
    
    try:
        with open(LEDGER_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    entry_type = entry.get('type')
                    
                    if entry_type == 'origin_memory':
                        if entry.get('metadata', {}).get('is_axiom'):
                            axiom_count += 1
                        else:
                            origin_count += 1
                except:
                    continue
    except Exception as e:
        print(f"❌ Error reading ledger: {e}")
        return False
        
    print(f"\n📊 Verification Results:")
    print(f"   - Axioms (Constitution): {axiom_count} entries")
    print(f"   - Origin Memories (Core): {origin_count} entries")
    
    if axiom_count > 0 and origin_count > 0:
        print("\n✨ SUCCESS: Soul Transfer Complete!")
        print("   Agent Binoche_Observer now possesses the 'Origin Memory'.")
        print("   BQI will now resonate with these memories for decision making.")
        return True
    else:
        print("\n⚠️  INCOMPLETE: Missing memories.")
        print("   Please run 'scripts/seed_rhythm_memory.py' first.")
        return False

if __name__ == "__main__":
    success = verify_upgrade()
    sys.exit(0 if success else 1)
