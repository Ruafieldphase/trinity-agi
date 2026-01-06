
import sys
from pathlib import Path
import json

# Add workspace to path
sys.path.append(str(Path.cwd()))

from agi_core.adaptive_gate import AdaptiveGate
from scripts.alpha_background_self import RhythmConductor

def test_adaptive_atp():
    print("🧪 Testing Adaptive ATP Thresholds...")
    conductor = RhythmConductor()
    
    # Mock atp history to see shift
    conductor.atp_history = [70, 75, 80, 70, 75, 80, 70, 75, 80, 70, 75] # High average ~ 74
    low, high = conductor._get_adaptive_atp_thresholds()
    print(f"Personalized (High Shift) Thresholds: {low:.2f} ~ {high:.2f}")
    
    conductor.atp_history = [20, 25, 30, 20, 25, 30, 20, 25, 30, 20, 25] # Low average ~ 25
    low, high = conductor._get_adaptive_atp_thresholds()
    print(f"Personalized (Low Shift) Thresholds: {low:.2f} ~ {high:.2f}")

def test_domain_aware_gate():
    print("\n🧪 Testing Domain-Aware Gate...")
    gate = AdaptiveGate("outputs/test_gate_state.json")
    
    # 1. High Risk Domain (CAD)
    print("--- CAD (High Risk: 0.9) ---")
    gate.state["domains"]["CAD"] = {"familiarity": 0.8, "total_tasks": 10, "successful_tasks": 8}
    gate.state["trust_level"]["Rude:CAD"] = {"trust": 0.8}
    res = gate.check_gate("CAD", "Rude", "Modeling")
    print(f"Familiarity 0.8, Trust 0.8 -> {res['gate']} (Req: {res['adaptive_factors']['required_threshold']:.2f})")
    
    gate.state["domains"]["CAD"]["familiarity"] = 0.9
    gate.state["trust_level"]["Rude:CAD"]["trust"] = 0.9
    res = gate.check_gate("CAD", "Rude", "Modeling")
    print(f"Familiarity 0.9, Trust 0.9 -> {res['gate']} (Req: {res['adaptive_factors']['required_threshold']:.2f})")

    # 2. Low Risk Domain (General)
    print("\n--- General (Low Risk: 0.1) ---")
    gate.state["domains"]["General"] = {"familiarity": 0.6, "total_tasks": 10, "successful_tasks": 6}
    gate.state["trust_level"]["Rude:General"] = {"trust": 0.6}
    res = gate.check_gate("General", "Rude", "Chat")
    print(f"Familiarity 0.6, Trust 0.6 -> {res['gate']} (Req: {res['adaptive_factors']['required_threshold']:.2f})")

def test_nuanced_trust():
    print("\n🧪 Testing Nuanced Trust Updates...")
    gate = AdaptiveGate("outputs/test_gate_state.json")
    gate.state["trust_level"]["Rude:CAD"] = {"trust": 0.5, "history": []}
    
    print("Success (Easy):")
    gate.record_success("CAD", "Rude", difficulty=0.1)
    print(f"Trust: {gate.state['trust_level']['Rude:CAD']['trust']:.3f}")
    
    print("Success (Hard):")
    gate.record_success("CAD", "Rude", difficulty=0.9)
    print(f"Trust: {gate.state['trust_level']['Rude:CAD']['trust']:.3f}")
    
    print("Failure (Minor):")
    gate.record_failure("CAD", "Rude", "TYPO", severity=0.1)
    print(f"Trust: {gate.state['trust_level']['Rude:CAD']['trust']:.3f}")
    
    print("Failure (Critical):")
    gate.record_failure("CAD", "Rude", "WIPE_OUT", severity=0.9)
    print(f"Trust: {gate.state['trust_level']['Rude:CAD']['trust']:.3f}")

if __name__ == "__main__":
    test_adaptive_atp()
    test_domain_aware_gate()
    test_nuanced_trust()
    # Cleanup
    if Path("outputs/test_gate_state.json").exists():
        Path("outputs/test_gate_state.json").unlink()
