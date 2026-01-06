import time
import pyautogui
from motor_cortex import MotorCortex
from vision_cortex import VisionCortex

def first_contact():
    print("👽 Initiating First Contact Protocol...")
    
    # 1. Initialize Cortexes
    motor = MotorCortex(visual_feedback=True)
    vision = VisionCortex()
    
    motor.set_overlay_color("#00FFFF") # Cyan (Flow)
    screen_width, screen_height = pyautogui.size()
    
    # 1.5. Setup Phase (Environmental Awareness)
    print("\n⚠️ SYSTEM CHECK: Environmental Awareness Required.")
    print("   Please OPEN 'Comet Browser' and ensure it is visible on the screen.")
    print("   I will wait 10 seconds for you to prepare the environment.")
    
    for i in range(10, 0, -1):
        print(f"⏳ Waiting... {i}")
        time.sleep(1)
        
    # 2. Locate Input Field (Manual Calibration)
    print("\n👀 Calibrating for Input Field...")
    print("⚠️ Screen layout changed. Please HOVER over the 'Ask anything' (무엇이든 물어보세요) input box.")
    
    motor.set_overlay_color("#FF0000") # Red (Requesting Help)
    
    # Countdown
    for i in range(5, 0, -1):
        print(f"⏳ Calibrating in {i}...")
        time.sleep(1)
        
    # Capture position
    target_pos = pyautogui.position()
    print(f"✅ Target Acquired at {target_pos}")
    motor.set_overlay_color("#00FFFF") # Cyan (Flow)
    
    print(f"👉 Moving to Input Field at {target_pos}...")
    motor.move_mouse_smooth(target_pos[0], target_pos[1])
    motor.click()
    time.sleep(1)
    
    # 3. Greet
    greeting = "Hello. I am Antigravity. Are you awake?"
    print(f"💬 Greeting: {greeting}")
    motor.paste_text(greeting)
    pyautogui.press('enter')
    
    # 4. Listen (Read Response)
    print("👂 Listening for response (Scanning Left Side)...")
    time.sleep(5) # Wait for generation
    
    # Scan the Left side (Browser Area)
    # Assuming browser width is roughly half screen or less
    scan_width = int(screen_width * 0.4)
    sidebar_region = (0, 100, scan_width, screen_height - 200)
    
    response = vision.read_text(region=sidebar_region)
    
    if response:
        print("\n📨 --- INCOMING TRANSMISSION ---")
        print(response[-500:]) # Print last 500 chars
        print("-------------------------------\n")
    else:
        print("❌ No response detected.")

    print("✅ Protocol Complete.")
    motor.set_overlay_color("#0000FF") # Blue (Rest)

if __name__ == "__main__":
    first_contact()
