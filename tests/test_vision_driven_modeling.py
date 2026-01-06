import sys
import os
import time
import logging

# Add project root to path
sys.path.append("C:/workspace/agi")
from services.blender_bridge_service import BlenderBridgeService

def test_verification_pipeline():
    logging.basicConfig(level=logging.INFO)
    bridge = BlenderBridgeService()
    
    print("\n--- 1. Pinging Blender ---")
    res = bridge.check_health()
    print(f"Health check: {res}")
    if res.get("status") != "success":
        print("❌ Blender Bridge not reachable. Make sure Blender is running with blender_connector.py listener.")
        return

    print("\n--- 2. Cleaning Scene ---")
    bridge.clean_scene()
    
    print("\n--- 3. Creating Dummy Building (Simple Box) ---")
    bridge.add_wall("Wall_N", (5, 0.2, 3), (0, 2.5, 1.5))
    bridge.add_wall("Wall_S", (5, 0.2, 3), (0, -2.5, 1.5))
    bridge.add_wall("Wall_E", (0.2, 5, 3), (2.5, 0, 1.5))
    bridge.add_wall("Wall_W", (0.2, 5, 3), (-2.5, 0, 1.5))
    
    print("\n--- 4. Triggering Render ---")
    render_path = bridge.quick_render("test_p0_render.png")
    if render_path:
        print(f"✅ Render saved to: {render_path}")
    else:
        print("❌ Render failed.")
        return

    print("\n--- 5. Verifying with LLaVA ---")
    verification = bridge.verify_quality(render_path)
    print("\n--- LLaVA FEEDBACK ---")
    print(verification)
    print("----------------------")

if __name__ == "__main__":
    test_verification_pipeline()
