import time
import webbrowser
import pyautogui
from motor_cortex import MotorCortex
from vision_cortex import VisionCortex

def research_topic(topic="Artificial General Intelligence news"):
    print(f"🕵️ Researching: '{topic}'...")
    
    # 1. Initialize Cortexes
    motor = MotorCortex(visual_feedback=True)
    vision = VisionCortex()
    
    motor.set_overlay_color("#00FFFF") # Cyan (Flow)
    
    # 2. Open Google (Physical Action)
    print("🌍 Opening Google...")
    webbrowser.open("https://www.google.com")
    time.sleep(3) # Wait for load
    
    # 3. Type Search Query (Motor Action)
    # We assume focus is on the search box or we click center
    # For robustness, let's try to type directly first (Google usually focuses input)
    print(f"⌨️ Typing query: {topic}")
    motor.type_text(topic, interval=0.05)
    pyautogui.press('enter')
    
    time.sleep(3) # Wait for results
    
    # 4. Read Results (Cognitive Action)
    print("👀 Scanning search results...")
    
    # Read the main content area (approximate)
    screen_width, screen_height = pyautogui.size()
    # Google results are usually on the left-center
    region = (0, 150, screen_width // 2 + 200, screen_height - 200)
    
    text = vision.read_text(region=region)
    
    if text:
        print("\n🔍 --- SEARCH FINDINGS ---")
        lines = text.split('\n')
        found_count = 0
        for line in lines:
            clean_line = line.strip()
            # Filter for likely headlines (longer text, not just 'Images' or 'Videos')
            if len(clean_line) > 30 and not clean_line.startswith("http"):
                print(f"  > {clean_line}")
                found_count += 1
                if found_count >= 5: break # Top 5
        print("-------------------------\n")
    else:
        print("❌ Could not read results.")

    print("✅ Research Complete.")
    motor.set_overlay_color("#0000FF") # Blue (Rest)

if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "Artificial General Intelligence news"
    research_topic(query)
