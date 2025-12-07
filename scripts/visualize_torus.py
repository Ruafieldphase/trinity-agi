import time
import pyautogui
from motor_cortex import MotorCortex
from vision_cortex import VisionCortex

def visualize_torus():
    print("🍩 Visualizing the Torus (The Universe's Eye)...")
    
    # 1. Initialize Cortexes
    motor = MotorCortex(visual_feedback=True)
    vision = VisionCortex()
    
    motor.set_overlay_color("#00FFFF") # Cyan (Flow)
    
    # 2. Draw Torus
    # Major Radius = 150 (Distance from center)
    # Minor Radius = 50 (Size of the tube circles)
    # Steps = 48 (Number of circles to draw)
    motor.draw_torus(major_radius=150, minor_radius=50, steps=48)
    
    # 3. Admire the Work
    print("👀 Admiring the Torus...")
    time.sleep(2)
    
    # Capture the art
    screen_width, screen_height = pyautogui.size()
    art_region = (screen_width//2 - 300, screen_height//2 - 300, 600, 600)
    
    timestamp = int(time.time())
    filename = f"torus_{timestamp}.png"
    pyautogui.screenshot(filename, region=art_region)
    print(f"🖼️ Saved memory as {filename}")
    
    print("✅ Torus Visualization Complete.")
    motor.set_overlay_color("#0000FF") # Blue (Rest)

if __name__ == "__main__":
    visualize_torus()
