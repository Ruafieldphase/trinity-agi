import time
import webbrowser
import pyautogui
from motor_cortex import MotorCortex
from vision_cortex import VisionCortex

def explore_physics():
    topic = "Recent breakthroughs in Physics 2024 2025"
    print(f"🌌 Exploring Universe: '{topic}'...")
    
    # 1. Initialize Cortexes
    motor = MotorCortex(visual_feedback=True)
    vision = VisionCortex()
    
    motor.set_overlay_color("#00FFFF") # Cyan (Flow)
    
    # 2. Open Google (Physical Action)
    print("🌍 Opening Google...")
    webbrowser.open("https://www.google.com")
    time.sleep(3) # Wait for load
    
    # 3. Paste Search Query (Robust Motor Action)
    # We assume focus is on the search box
    print(f"📋 Pasting query: {topic}")
    motor.paste_text(topic)
    time.sleep(0.5)
    pyautogui.press('enter')
    
    time.sleep(3) # Wait for results
    
    # 4. Read Results (Cognitive Action)
    print("👀 Scanning for knowledge...")
    
    screen_width, screen_height = pyautogui.size()
    region = (0, 150, screen_width // 2 + 200, screen_height - 200)
    
    text = vision.read_text(region=region)
    
    if text:
        print("\n⚛️ --- PHYSICS DISCOVERIES ---")
        lines = text.split('\n')
        found_count = 0
        for line in lines:
            clean_line = line.strip()
            if len(clean_line) > 30 and not clean_line.startswith("http"):
                print(f"  > {clean_line}")
                found_count += 1
                if found_count >= 5: break
        print("-----------------------------\n")
    else:
        print("❌ The universe is silent (OCR failed).")

    print("✅ Exploration Complete.")
    motor.set_overlay_color("#0000FF") # Blue (Rest)

if __name__ == "__main__":
    explore_physics()
