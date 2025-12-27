#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Delegate to fdo_agi_repo/orchestrator/full_stack_orchestrator.py
# If missing, use internal stub.

def main():
    root = Path(__file__).resolve().parents[1]
    target_mod = root / "fdo_agi_repo" / "orchestrator" / "full_stack_orchestrator.py"
    
    if target_mod.exists():
        # Add to path and import
        sys.path.append(str(target_mod.parent.parent.parent))
        try:
            from fdo_agi_repo.orchestrator.full_stack_orchestrator import main as real_main
            real_main()
            return
        except Exception as e:
            print(f"Delegation failed: {e}")
            pass

    # Fallback Stub
    print("Orchestrator Wrapper: Target not found or failed. Running fallback stub.")

if __name__ == "__main__":
    main()
