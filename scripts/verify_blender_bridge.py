import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.blender_bridge_service import BlenderBridgeService
import logging

def verify_bridge():
    logging.basicConfig(level=logging.INFO)
    bridge = BlenderBridgeService()
    
    print("--- Blender Bridge Verification ---")
    print("Pre-requisite: Blender must be running with blender_connector.py executed.")
    
    print("\n1. Pinging Blender...")
    res = bridge.check_health()
    if res.get("status") == "success":
        print(f"✅ Connection SUCCESS: {res.get('message')}")
        
        print("\n2. Testing scene cleaning...")
        clean_res = bridge.clean_scene()
        print(f"Result: {clean_res}")
        
        print("\n3. Testing object creation (Semantic Wall)...")
        wall_res = bridge.add_wall("Test_Wall", (2, 0.2, 3), (0,0,1.5))
        print(f"Result: {wall_res}")
        
        print("\nVerification Complete.")
    else:
        print(f"❌ Connection FAILED: {res.get('message')}")
        print("Please ensure Blender is running and you have run the script.")

if __name__ == "__main__":
    verify_bridge()
