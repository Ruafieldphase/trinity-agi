import time
import subprocess
import sys
import pyautogui
from pathlib import Path
from motor_cortex import MotorCortex
from vision_cortex import VisionCortex

def run_hand_eye_test():
    print("🧠 Initializing Hand-Eye Coordination Test...")
    
    # 1. Initialize Cortexes
    motor = MotorCortex(visual_feedback=True)
    vision = VisionCortex()
    
    # 2. Launch Visual Target
    print("🎯 Launching Visual Target...")
    target_script = Path(__file__).parent / "visual_target.py"
    target_process = subprocess.Popen([sys.executable, str(target_script)])
    time.sleep(2) # Wait for window to appear
    
    # 3. Take a screenshot of the target to look for?
    # Since we don't have a pre-saved image of the red circle, 
    # we will use a simple pixel color search for this MVP.
    # VisionCortex needs a 'find_color' method for this specific test.
    # Let's monkey-patch or assume we'll add it. 
    # Actually, let's use a simpler approach: Screen center check or just look for red pixels.
    
    print("👁️ Searching for RED target...")
    motor.set_overlay_color("#00FFFF") # Cyan (Flow)
    
    try:
        start_time = time.time()
        while time.time() - start_time < 20: # Run for 20 seconds
            if motor.check_user_override():
                break
                
            # Capture screen
            screenshot = vision.capture_screen()
            width, height = screenshot.size
            
            # Naive Color Search (Slow but works for MVP)
            # Look for pure red (255, 0, 0)
            target_pos = None
            
            # Optimization: Only scan the center area where the window likely is
            # or scan with a stride
            for x in range(0, width, 20):
                for y in range(0, height, 20):
                    r, g, b = screenshot.getpixel((x, y))
                    if r > 200 and g < 50 and b < 50: # Red-ish
                        target_pos = (x, y)
                        break
                if target_pos: break
            
            if target_pos:
                print(f"✅ Target Spotted at {target_pos}! Engaging Motor Cortex...")
                motor.move_mouse_smooth(target_pos[0], target_pos[1], duration=0.5)
                motor.click()
                time.sleep(0.5) # Wait for target to move
            else:
                print("❓ Target lost... Saving debug image.")
                screenshot.save("debug_vision.png")
                time.sleep(0.5)
                
    except KeyboardInterrupt:
        print("🛑 Test Interrupted.")
    finally:
        print("🏁 Test Concluded.")
        target_process.terminate()
        motor.set_overlay_color("#0000FF") # Blue (Rest)

if __name__ == "__main__":
    run_hand_eye_test()
