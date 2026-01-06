import asyncio
import sys
import os
import json
import logging
from pathlib import Path

# Add workspace root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.experience_vault import ExperienceVault
from agi_core.agency.checkin_registry import CheckInRegistry
from services.blender_bridge_service import BlenderBridgeService

async def verify_phase_8():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Phase8Verify")
    
    print("\n--- Phase 8: Verification Start ---")
    
    # 1. Verify CheckInRegistry
    print("\n[1] Verifying Multi-Agent Check-in Registry...")
    reg = CheckInRegistry()
    agent_a = "Agent_A"
    agent_b = "Agent_B"
    
    # Agent A checks in
    success_a = reg.check_in(agent_a, "Architect", "blender", "ZONE_1")
    print(f"Agent A check-in: {success_a}")
    
    # Agent B tries to check in same zone (should fail)
    success_b = reg.check_in(agent_b, "Modeler", "blender", "ZONE_1")
    print(f"Agent B check-in (conflict): {success_b}")
    
    if success_a and not success_b:
        print("✅ Registry Lock Mechanism: OK")
    else:
        print("❌ Registry Lock Mechanism: FAILED")
    
    reg.check_out(agent_a)
    
    # 2. Verify ExperienceVault (Vector Search)
    print("\n[2] Verifying ExperienceVault Vector Search...")
    vault = ExperienceVault()
    if vault.use_vector:
        goal_orig = "Create a standard RC wall with 200mm thickness"
        actions = [{"action": "click", "x": 500, "y": 500, "reason": "Base point"}]
        vault.save_experience(goal_orig, actions)
        
        # Search with similar but different wording
        goal_search = "Generate concrete wall"
        found_actions = vault.find_experience(goal_search)
        
        if found_actions and found_actions[0]['action'] == "click":
            print(f"✅ Vector Similarity Search: OK")
        else:
            print(f"❌ Vector Similarity Search: FAILED (No match found for '{goal_search}')")
    else:
        print("⚠️ Vector search not enabled, skipping test.")

    # 3. Verify BlenderBridgeService Integration
    print("\n[3] Verifying BlenderBridgeService Coordination...")
    bridge = BlenderBridgeService()
    # This will check in and then fail on connection (expected if Blender isn't open)
    res = bridge.send_command("ping", verify_checkin=True)
    print(f"Bridge response: {res}")
    
    # Reload registry to see the check-in from another instance/PID
    reg_reload = CheckInRegistry()
    active_agents = reg_reload.get_active_agents()
    print(f"Active Agents list: {[a.agent_id for a in active_agents]}")
    if any(a.agent_id == bridge.agent_id for a in active_agents):
        print("✅ Bridge-Registry Integration: OK")
    else:
        print("❌ Bridge-Registry Integration: FAILED")
    
    # Clean up
    bridge.registry.check_out(bridge.agent_id)

    print("\n--- Phase 8: Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(verify_phase_8())
