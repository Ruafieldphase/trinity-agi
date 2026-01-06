import socket
import json
import time
import sys

HOST = '127.0.0.1'
PORT = 8008

def send_command(cmd, params=None):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            payload = {"command": cmd, "params": params or {}}
            s.sendall(json.dumps(payload).encode('utf-8'))
            data = s.recv(4096)
            return json.loads(data.decode('utf-8'))
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    print(f"Connecting to RUD Bridge at {HOST}:{PORT}...")
    
    # 1. Ping
    res = send_command("ping")
    if res.get("status") != "success":
        print("❌ Cannot connect to RUD Bridge. Is Blender running?")
        sys.exit(1)
    print("✅ Connected to RUD Bridge.")

    # 2. Re-Genesis (Optional, to ensure fresh state)
    print("🎨 Requesting World Genesis...")
    res = send_command("create_world", {"complexity": 40, "seed": "entropy"})
    print(f"   Response: {res}")
    time.sleep(1)

    # 3. Journey (Move Agent)
    print("🚶 Starting Journey...")
    moves = [
        {"delta_location": [0, -2, 0], "delta_rotation": [0, 0, 0]},
        {"delta_location": [0, -2, 0], "delta_rotation": [0, 0, 10]},
        {"delta_location": [1, -1, 0], "delta_rotation": [0, 0, 20]},
        {"delta_location": [2, 0, 0], "delta_rotation": [0, 0, -10]},
        {"delta_location": [1, 1, 1], "delta_rotation": [0, 0, 0]}, # Jump/Climb
    ]

    for i, move in enumerate(moves):
        res = send_command("move_agent", move)
        hit_obj = res.get("hit_obj", "None")
        dist = res.get("hit_dist", -1)
        print(f"   Step {i+1}: Loc={res.get('location')} Hit={hit_obj} ({dist:.2f}m)")
        time.sleep(0.5)

    # 4. Render Proof
    print("📸 Capturing Proof of Existence...")
    output_path = "C:/workspace/agi/outputs/renders/rud_journey_proof.png"
    res = send_command("render_viewport", {"filepath": output_path})
    print(f"   Render saved to: {res.get('path')}")
    
    print("✨ Journey Complete.")

if __name__ == "__main__":
    main()
