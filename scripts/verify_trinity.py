import sys
import time
import logging
from pathlib import Path

# Add workspace root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

# Setup logging to console for verification
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("VerifyTrinity")

from agi_core.internal_state import get_internal_state
from scripts.integrated_state_analyzer import IntegratedStateAnalyzer
from scripts.bohm_implicate_explicate_analyzer import run_analysis_now

def verify_trinity():
    print("⚛️ Testing AGI-ARI-ASI Deep Resonance Bridge...")
    state = get_internal_state()
    
    # 0. Initial State
    print(f"\n[Initial State] Consciousness: {state.consciousness:.4f}, Resonance: {state.resonance:.4f}")
    
    # 1. Simulate Sensory Input
    state.input_tempo = 0.8  # High tempo (Flowing)
    state.network_wind = 0.1 # Calm network (Explicate)
    state.active_context = {"process": "blender.exe", "title": "Sculpting Soul"}
    print(f"[Sensory Stimulus] Tempo: {state.input_tempo}, Context: {state.active_context['process']}")

    # 2. Trigger ARI
    print("\n[ARI Bridge] Running IntegratedStateAnalyzer...")
    ari = IntegratedStateAnalyzer().analyze_integrated_state()
    final_conf = ari["integrated"].get("final_confidence", 0.0)
    print(f"-> ARI Result: {ari['integrated']['final_state']} (Conf: {final_conf:.2f})")

    # 3. Trigger ASI
    print("\n[ASI Bridge] Running BohmAnalyzer (run_analysis_now)...")
    asi = run_analysis_now()
    if asi:
        density = asi.get("temporal_geometry", {}).get("temporal_density", 0.0)
        balance = asi.get("interpretation", {}).get("implicate_explicate_balance", "UNKNOWN")
        print(f"-> ASI Result: Balance={balance}, Density={density:.2f}")
    else:
        print("-> ASI Result: No data/Failed")
        density = 0.0

    # 4. Apply Simulated Feedback (Logic from heartbeat_loop.py)
    print("\n[Applying Feedback Loop]...")
    prev_c = state.consciousness
    prev_r = state.resonance
    
    state.consciousness = min(1.0, state.consciousness + (final_conf * 0.05))
    state.resonance = min(1.0, state.resonance + (density * 0.05))
    
    print(f"[Final State] Consciousness: {state.consciousness:.4f} (+{state.consciousness - prev_c:.4f})")
    print(f"              Resonance: {state.resonance:.4f} (+{state.resonance - prev_r:.4f})")

    if state.consciousness > prev_c or state.resonance > prev_r:
        print("\n✅ Trinity Bridge verification SUCCESS. Systems are resonating.")
    else:
        print("\n❌ Trinity Bridge verification FAILED. No state change detected.")

if __name__ == "__main__":
    verify_trinity()
