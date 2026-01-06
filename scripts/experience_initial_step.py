import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.blender_bridge_service import BlenderBridgeService

def initial_experience():
    bridge = BlenderBridgeService()
    
    print("--- 1. Connection Check ---")
    health = bridge.check_health()
    # print("\n--- 2. Scene Info ---")
    # Skiping get_scene_info as it is not implemented in the current running bridge
    
    print("\n--- 2. Portview Capture & Vision ---")
    render_path = "C:/workspace/agi/outputs/renders/first_genesis_view.png"
    render_res = bridge.send_command("render_viewport", {"filepath": render_path})
    print(f"Render Result: {render_res}")

    if render_res.get("status") == "success":
        from services.local_vision_service import analyze_image_locally
        print("Analyzing visual input...")
        vision_result = analyze_image_locally(
            render_path, 
            "Describe this abstract 3D space. What shapes and colors do you see? Does it look organic or geometric? Explain the spatial depth."
        )
        print(f"\n[RUD Vision]: {vision_result}\n")

    print("\n--- 3. Initial Active Movement ---")
    # Move forward slightly to feel the space
    move_res = bridge.move_agent(delta_loc=(0, 3, 0), delta_rot=(0, 0, 10))
    print(f"Movement Result: {move_res}")
    
    if move_res.get("hit"):
        print(f"⚠️ EVENT: Hit {move_res.get('hit_obj')} at distance {move_res.get('hit_dist')}")
    else:
        print("Path clear. Moving forward.")

if __name__ == "__main__":
    initial_experience()
