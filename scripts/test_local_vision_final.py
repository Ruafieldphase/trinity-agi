import os
import sys

# Add workspace root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.local_vision_service import analyze_image_locally

def test_local_vision():
    image_path = "c:/workspace/agi/outputs/arch_analysis/frame_10.jpg"
    prompt = "Describe this architectural modeling UI and point out any specific CAD or 3D elements."
    
    print(f"Testing local vision with {image_path}...")
    result = analyze_image_locally(image_path, prompt, model="llava:7b")
    
    print("\n--- Result from Local LLaVA ---")
    print(result)
    print("------------------------------")

if __name__ == "__main__":
    test_local_vision()
