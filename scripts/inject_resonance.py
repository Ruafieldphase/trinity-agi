#!/usr/bin/env python3
import sys
import json
from pathlib import Path
from workspace_root import get_workspace_root

def inject(amount: float = 30.0):
    """
    ⚡ Resonance Injection
    Directly fuels the Mitochondria with User-provided intention energy.
    """
    workspace = get_workspace_root()
    state_file = workspace / "outputs" / "mitochondria_state.json"
    
    if not state_file.exists():
        print("⚠️ Mitochondria state not found. Heartbeat must start first.")
        return
    
    try:
        state = json.loads(state_file.read_text(encoding='utf-8'))
        old_atp = state.get('atp_level', 50.0)
        new_atp = min(100.0, old_atp + amount)
        
        state['atp_level'] = round(new_atp, 2)
        state['status'] = "RECHARGED"
        state['last_update'] = "Injected by User"
        
        state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')
        print(f"✅ Resonance Injected! ATP: {old_atp:.1f} -> {new_atp:.1f}")
        
    except Exception as e:
        print(f"❌ Injection failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            val = float(sys.argv[1])
            inject(val)
        except:
            inject()
    else:
        inject()
