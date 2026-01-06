import socket
import json
import logging
import time
import os
from typing import Dict, Any, Optional, List
from agi_core.agency.checkin_registry import CheckInRegistry
from services.local_vision_service import analyze_image_locally

class BlenderBridgeService:
    """
    AGI-side TCP Client for communicating with Blender Direct Bridge.
    Protocol: JSON-over-TCP
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 8008):
        self.host = host
        self.port = port
        self.logger = logging.getLogger("BlenderBridge")
        self.logger.setLevel(logging.INFO)
        self.registry = CheckInRegistry()
        self.agent_id = f"agent_{os.getpid()}" # Default ID

    def send_command(self, command: str, params: Dict[str, Any] = {}, verify_checkin: bool = False) -> Dict[str, Any]:
        """Sends a JSON command to Blender and returns the response."""
        
        if verify_checkin:
            # Simple check-in before sensitive commands
            if not self.registry.check_in(self.agent_id, "Modeler", "blender", "3D_VIEWPORT"):
                return {"status": "error", "message": "Resource locked by another agent"}
        
        payload = {
            "command": command,
            "params": params,
            "timestamp": time.time(),
            "agent_id": self.agent_id
        }
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5.0)
                s.connect((self.host, self.port))
                s.sendall(json.dumps(payload).encode('utf-8'))
                
                response_data = s.recv(4096)
                if response_data:
                    return json.loads(response_data.decode('utf-8'))
                return {"status": "success", "message": "Command sent, no response received"}
        except ConnectionRefusedError:
            self.logger.error("Blender Bridge connection refused. Is Blender running with the listener?")
            return {"status": "error", "message": "Connection refused"}
        except socket.timeout:
            self.logger.error("Blender Bridge request timed out.")
            return {"status": "error", "message": "Timed out"}
        except Exception as e:
            self.logger.error(f"Blender Bridge unexpected error: {e}")
            return {"status": "error", "message": str(e)}

    # High-level modeling API
    def clean_scene(self):
        return self.send_command("clean_scene")

    def add_wall(self, name: str, size: tuple, location: tuple, rotation: tuple = (0,0,0), material: str = None):
        return self.send_command("add_box", {
            "name": name,
            "size": size,
            "location": location,
            "rotation": rotation,
            "material": material
        })

    def quick_render(self, filename: str = "temp_verification.png", camera_loc: tuple = (15, -15, 15)):
        """Triggers a render and returns the local path."""
        # Ensure output directory exists
        output_dir = "C:/workspace/agi/outputs/renders"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        full_path = f"{output_dir}/{filename}"
        res = self.send_command("render_scene", {
            "filepath": full_path,
            "camera_location": camera_loc,
            "camera_look_at": (0, 0, 0)
        })
        
        if res.get("status") == "success":
            return full_path
        return None

    def verify_quality(self, render_path: str, prompt: Optional[str] = None):
        """Uses LLaVA to verify the architectural quality of the render."""
        if not render_path or not os.path.exists(render_path):
            return "Error: Render file not found"
        
        if not prompt:
            prompt = """
            Analyze this architectural 3D model render based on a DXF specification:
            1. Does the building have structural details (canopies, stairs, protrusions)?
            2. Does it look like a finished architectural model or just primitive boxes?
            3. Rate the completeness out of 100.
            
            Identify missing elements compared to a standard building.
            """
        
        return analyze_image_locally(render_path, prompt)

    def check_health(self):
        return self.send_command("ping")

    def get_scene_info(self):
        """Retrieves object and material counts from the scene."""
        return self.send_command("get_scene_info")

    def set_atmospheric_mood(self, valence: float, arousal: float, resonance: float):
        """Controls Blender world lighting based on emotional vectors."""
        return self.send_command("set_atmospheric_mood", {
            "valence": valence,
            "arousal": arousal,
            "resonance": resonance
        })

    def move_agent(self, delta_loc=(0,0,0), delta_rot=(0,0,0), name="Rhythm_Agent"):
        """Sends a movement command and returns collision/location data."""
        return self.send_command("move_agent", {
            "name": name,
            "delta_location": delta_loc,
            "delta_rotation": delta_rot
        })

    def create_world(self, complexity: int = 25, seed: str = "random"):
        """Triggers the creation of a new autonomous world."""
        return self.send_command("create_world", {
            "complexity": complexity,
            "seed": seed
        })

    def analyze_viewport(self, prompt: str = "Analyze this architectural space."):
        """Captures a viewport screenshot and analyzes it via local vision."""
        render_path = "C:/workspace/agi/outputs/renders/viewport_now.png"
        res = self.send_command("render_viewport", {"filepath": render_path})
        
        if res.get("status") == "success":
            return self.verify_quality(render_path, prompt)
        return {"status": "error", "message": "Failed to capture viewport"}

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    bridge = BlenderBridgeService()
    print("Pinging Blender...")
    res = bridge.check_health()
    print(f"Response: {res}")
