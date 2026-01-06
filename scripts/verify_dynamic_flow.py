import sys
import json
import logging

# Mock Bridge
class MockBridge:
    def send_command(self, cmd, params):
        print(f"[Bridge] CMD: {cmd}, PARAMS: {params}")
        if "impulse" in params:
            print(f"  -> Emotional Tag Detected: {params['impulse']}")
        return {"status": "success"}
    
    def check_health(self): return {"status": "success"}

def test_dynamic_equilibrium_flow():
    print("--- Simulating Dynamic Equilibrium Flow ---")
    bridge = MockBridge()
    
    # 1. Boredom -> Chaos Creation
    print("\n[State: BOREDOM] (Alignment 0.95, Consc 0.1)")
    impulse_type = "boredom"
    complexity = 55
    seed = "State_123_boredom"
    
    print("Action: Creating Chaos...")
    bridge.send_command("create_world", {"complexity": complexity, "seed": seed, "impulse": impulse_type})
    
    # 2. Curiosity -> Exploration
    print("\n[State: CURIOSITY] (Conflict 0.8)")
    impulse_type = "curiosity"
    
    print("Action: Exploring Structure...")
    bridge.send_command("move_agent", {
        "name": "Rhythm_Agent",
        "delta_location": (0.5, 0.5, 0),
        "delta_rotation": (0,0,10),
        "impulse": impulse_type
    })

if __name__ == "__main__":
    test_dynamic_equilibrium_flow()
