import os
import time
import json
import pyautogui
import vertexai
from pathlib import Path
try:
    from vertexai.generative_models import GenerativeModel, Part, Image
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from motor_cortex import MotorCortex

# Configuration
PROJECT_ID = "naeda-genesis"
LOCATION = "us-central1"
MODEL_NAME = "gemini-2.0-flash-exp"
TEMP_SCREENSHOT = Path("temp_vision_bridge.png")

class VisionMotorBridge:
    def __init__(self):
        print("👁️✋ Initializing Vision-Motor Bridge...")
        
        self.backend = "none"
        self.model = None
        self.motor = MotorCortex()

        # 1. Try Free-Tier AI Studio first
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if GENAI_AVAILABLE and api_key:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel(MODEL_NAME)
                self.backend = "genai"
                # print("✅ Bridge Ready (AI Studio - FREE TIER)")
                return
            except Exception as e:
                print(f"⚠️ GenAI init failed: {e}")

        # 2. Fallback to Paid-Tier Vertex AI
        if VERTEX_AVAILABLE:
            try:
                vertexai.init(project=PROJECT_ID, location=LOCATION)
                from vertexai.generative_models import GenerativeModel as VertexModel
                self.model = VertexModel(MODEL_NAME)
                self.backend = "vertex"
                print(f"⚠️ [COST_WARNING] Bridge Ready (Vertex AI - PAID TIER)")
                return
            except Exception as e:
                print(f"❌ Vertex init failed: {e}")

        raise RuntimeError("No usable AI backend found for VisionMotorBridge.")

    def execute_intent(self, intent: str):
        """
        Executes a high-level intent by looking at the screen and moving the mouse.
        """
        print(f"🤖 Processing Intent: '{intent}'")
        
        # 1. Capture Screen
        screenshot = pyautogui.screenshot()
        screenshot.save(TEMP_SCREENSHOT)
        
        # 2. Analyze with Gemini
        target_coords = self._find_target_on_screen(intent)
        
        # 3. Execute Motor Action
        if target_coords:
            x, y = target_coords
            print(f"📍 Target found at ({x}, {y}). Moving mouse...")
            self.motor.move_mouse_smooth(x, y, speed="medium")
            
            # Heuristic: If intent implies clicking, click.
            if "click" in intent.lower() or "select" in intent.lower() or "open" in intent.lower():
                self.motor.click()
                print("👆 Clicked.")
        else:
            print("❌ Could not find target on screen.")

        # Cleanup
        if TEMP_SCREENSHOT.exists():
            TEMP_SCREENSHOT.unlink()

    def _find_target_on_screen(self, intent: str):
        """
        Asks Gemini to find the coordinates of the target element.
        """
        prompt = f"""
        You are a UI Automation Agent.
        User Intent: "{intent}"
        
        Look at the screenshot. Identify the UI element that the user wants to interact with.
        Return the center coordinates (x, y) of that element.
        
        Output Format (JSON only):
        {{"x": 123, "y": 456, "confidence": 0.9}}
        
        If you cannot find the element, return null for x and y.
        """
        
        try:
            with open(TEMP_SCREENSHOT, "rb") as f:
                image_data = f.read()
            
            if self.backend == "genai":
                # AI Studio Part format
                image_part = {"mime_type": "image/png", "data": image_data}
                response = self.model.generate_content([prompt, image_part])
            else:
                # Vertex AI Part format
                from vertexai.generative_models import Part as VertexPart
                image_part = VertexPart.from_data(data=image_data, mime_type="image/png")
                response = self.model.generate_content([image_part, prompt])

            text = response.text.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(text)
            if data.get("x") is not None and data.get("y") is not None:
                return int(data["x"]), int(data["y"])
            return None
            
        except Exception as e:
            print(f"Error in vision analysis: {e}")
            return None

if __name__ == "__main__":
    import sys
    bridge = VisionMotorBridge()
    
    if len(sys.argv) > 1:
        intent = " ".join(sys.argv[1:])
        bridge.execute_intent(intent)
    else:
        print("Usage: python vision_motor_bridge.py <intent>")
        print("Example: python vision_motor_bridge.py Click the Start Button")
