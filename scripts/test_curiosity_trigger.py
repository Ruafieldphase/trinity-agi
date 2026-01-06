import sys
import os
import random
import time

# Mocking
class MockState:
    def __init__(self, heartbeat, consciousness):
        self.heartbeat_count = heartbeat
        self.consciousness = consciousness

class MockLogger:
    def info(self, msg): print(f"[INFO] {msg}")
    def error(self, msg): print(f"[ERROR] {msg}")

logger = MockLogger()
WORKSPACE_ROOT = "c:/workspace/agi"

def simulate_curiosity_trigger():
    print("--- Simulating RUD Curiosity & Boredom Trigger ---")
    
    # Scene 1: Boredom (Stagnation)
    print("\n[Scenario 1] High Alignment + Low Consciousness (Boredom)")
    alignment = 0.90
    conflict = 0.1
    state = MockState(heartbeat=100, consciousness=0.1) # Sleepy but harmonious
    
    cycle_count = 30
    impulse_type = None
    
    if alignment > 0.85 and state.consciousness < 0.3:
        impulse_type = "boredom"
        logger.info("🥱 [Impulse] Stagnation Detected. Triggering Creative Chaos.")
    elif conflict > 0.6:
        impulse_type = "curiosity"
    
    if impulse_type == "boredom":
        complexity = random.randint(30, 60)
        print(f"Action: create_world(complexity={complexity}, seed='State_100_boredom')")
        print("Note: RUD creates CHAOS to break monotony.")

    # Scene 2: Curiosity (Conflict)
    print("\n[Scenario 2] High Conflict (Confusion/Curiosity)")
    alignment = 0.4
    conflict = 0.8 # Very confused
    state = MockState(heartbeat=200, consciousness=0.8) # Awake and troubled
    
    impulse_type = None
    if alignment > 0.85 and state.consciousness < 0.3:
        impulse_type = "boredom"
    elif conflict > 0.6:
        impulse_type = "curiosity"
        logger.info("🤔 [Impulse] Internal Conflict Detected. Triggering Structural Expression.")
        
    if impulse_type == "curiosity":
        print("Action: move_agent(...)")
        print("Note: RUD explores to resolve conflict.")

if __name__ == "__main__":
    simulate_curiosity_trigger()
