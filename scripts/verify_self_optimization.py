"""
Verify Self-Optimization (Phase 13)
==================================
Tests the recursive feedback loop between modeling outcomes and rhythm boundaries.
"""

import sys
import json
from pathlib import Path
import time

# Add root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from agi_core.rhythm_boundaries import RhythmBoundaryManager

def simulate_outcome(success=True):
    thought_stream_path = WORKSPACE_ROOT / "outputs" / "thought_stream_latest.json"
    
    # Create dummy performance record
    record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": "ARCH_MODELING_COMPLETE",
        "source": "simulation_test.dxf",
        "status": "SUCCESS" if success else "FAILED",
        "parameters": {"wall_thickness": 200}
    }
    
    with open(thought_stream_path, "w", encoding="utf-8") as f:
        json.dump({"agent": "Simulation", "last_record": record}, f, indent=2)
    
    print(f"🧪 Simulated Outcome: {'SUCCESS' if success else 'FAILED'}")

def test_tuning_loop():
    rbm = RhythmBoundaryManager(WORKSPACE_ROOT)
    
    print(f"📊 Initial Phase Boundary Base: {rbm.phase_boundary.base:.4f}")
    
    # Test 1: Successful modeling should SLIGHTLY lower the threshold (make it easier to expand)
    simulate_outcome(success=True)
    rbm.perform_self_tuning()
    print(f"✅ After Success: {rbm.phase_boundary.base:.4f}")
    
    # Test 2: Another success
    simulate_outcome(success=True)
    rbm.perform_self_tuning()
    print(f"✅ After Success 2: {rbm.phase_boundary.base:.4f}")

    # Note: Failure simulation is more aggressive
    # (Since our current analyzer is simple, failure is handled via logical branches in SelfOptimizer if we mock it correctly)
    # The current self_optimizer.py uses status="SUCCESS" from the event itself primarily.
    
    # Check if state file exists
    state_file = WORKSPACE_ROOT / "outputs" / "governance" / "boundary_phase.json"
    if state_file.exists():
        print(f"💾 Persistence Check: {state_file.name} exists.")
        with open(state_file, "r") as f:
            print(f"   Content: {f.read().strip()}")

if __name__ == "__main__":
    test_tuning_loop()
