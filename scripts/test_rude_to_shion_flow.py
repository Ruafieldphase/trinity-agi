import sys
import os
import json
import time
from pathlib import Path

# Add workspace root to sys.path
WORKSPACE = Path("c:/workspace/agi")
sys.path.append(str(WORKSPACE))

from agi_core.agency.rude_dispatch import RudeDispatcher
from agi_core.agency.mission_coordinator import MissionCoordinator

def test_rude_to_shion_flow():
    print("\n--- [E2E] Rude-to-Shion Flow Test ---")
    
    dispatcher = RudeDispatcher()
    coordinator = MissionCoordinator()
    
    # 1. Clean up existing tasks
    if coordinator.task_file.exists():
        os.remove(coordinator.task_file)
        print("Cleaned up existing body_task.json")
    
    # 2. Rude dispatches a mission
    task_name = "Blender Box Request"
    actions = [
        {"type": "add_box", "params": {"name": "RudeBox", "location": (1, 1, 1)}},
        {"type": "log", "content": "Rude's request processed by body."}
    ]
    mission_path = dispatcher.send_mission(task_name, actions)
    
    if not mission_path or not mission_path.exists():
        print("✗ Failed to create mission file")
        return

    print(f"✓ Mission created: {mission_path.name}")
    
    # 3. Coordinator runs once to pick up the mission
    print("Running MissionCoordinator...")
    coordinator.run_once()
    
    # 4. Verification
    if coordinator.task_file.exists():
        with open(coordinator.task_file, "r", encoding="utf-8") as f:
            task_data = json.load(f)
        
        print(f"✓ Task file found: {coordinator.task_file.name}")
        print(f"  Actions count: {len(task_data.get('actions', []))}")
        print(f"  Origin: {task_data.get('origin')}")
        
        if task_data.get('origin') == "antigravity_rude":
            print("✨ Rude-to-Shion Flow Verified: Mind commanded the Body.")
        else:
            print("! Origin mismatch")
    else:
        print("✗ Task file was not promoted. Check logs.")

if __name__ == "__main__":
    test_rude_to_shion_flow()
