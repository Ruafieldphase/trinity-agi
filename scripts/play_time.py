import time
import random
import pyautogui
import math
from motor_cortex import MotorCortex
from vision_cortex import VisionCortex

def play_time():
    print("🎨 It's Play Time! Letting the imagination flow...")
    
    # 1. Initialize Cortexes
    motor = MotorCortex(visual_feedback=True)
    vision = VisionCortex()
    
    motor.set_overlay_color("#00FFFF") # Cyan (Flow)
    
    # 2. Generate Random Art Parameters
    # Spirograph: x(t) = (R-r)*cos(t) + d*cos((R-r)/r*t)
    R = random.randint(100, 200)
    r = random.randint(30, 100)
    d = random.randint(50, 150)
    
    print(f"🎲 Inspiration: R={R}, r={r}, d={d}")
    
    # 3. Draw (Motor Action)
    # draw_spirograph handles opening paint
    motor.draw_spirograph(R, r, d)
    
    # 4. Admire the Work (Vision Action)
    print("👀 Admiring the masterpiece...")
    time.sleep(2)
    
    # Capture the art
    screen_width, screen_height = pyautogui.size()
    # Center crop
    art_region = (screen_width//2 - 300, screen_height//2 - 300, 600, 600)
    
    timestamp = int(time.time())
    filename = f"art_{timestamp}.png"
    pyautogui.screenshot(filename, region=art_region)
    print(f"🖼️ Saved memory as {filename}")
    
    print("✅ Play Time Complete.")
    motor.set_overlay_color("#0000FF") # Blue (Rest)

if __name__ == "__main__":
    play_time()
