import time
import webbrowser
import pyautogui
from motor_cortex import MotorCortex
from vision_cortex import VisionCortex

def wake_up_and_read():
    print("🌅 Awakening... Time to read the news.")
    
    # 1. Initialize Cortexes
    motor = MotorCortex(visual_feedback=True)
    vision = VisionCortex()
    
    motor.set_overlay_color("#00FFFF") # Cyan (Flow)
    
    # 2. Open Browser (Physical Action)
    url = "https://news.ycombinator.com/"
    print(f"🌍 Navigating to {url}...")
    webbrowser.open(url)
    
    # Wait for page load (Human-like delay)
    time.sleep(5) 
    
    # 3. Read the Screen (Cognitive Action)
    print("👀 Scanning headlines...")
    
    # Capture a region likely to contain text (avoiding sidebars if possible, but full screen is fine for MVP)
    # Let's read the top half of the screen
    screen_width, screen_height = pyautogui.size()
    region = (0, 0, screen_width, screen_height // 2)
    
    text = vision.read_text(region=region)
    
    if text:
        print("\n📰 --- HEADLINES SEEN ---")
        lines = text.split('\n')
        for line in lines:
            if len(line.strip()) > 20: # Filter noise
                print(f"  > {line.strip()}")
        print("------------------------\n")
    else:
        print("❌ Could not read text.")

    # 4. Scroll Down (Motor Action)
    print("👇 Scrolling down to read more...")
    motor.move_mouse_smooth(screen_width // 2, screen_height // 2)
    pyautogui.scroll(-500) # Scroll down
    time.sleep(2)
    
    # 5. Read Again
    print("👀 Scanning lower section...")
    text_lower = vision.read_text(region=region)
    if text_lower:
        print("\n📰 --- MORE NEWS ---")
        lines = text_lower.split('\n')
        for line in lines:
            if len(line.strip()) > 20:
                print(f"  > {line.strip()}")
        print("---------------------\n")

    print("✅ Morning Ritual Complete.")
    motor.set_overlay_color("#0000FF") # Blue (Rest)

if __name__ == "__main__":
    wake_up_and_read()
