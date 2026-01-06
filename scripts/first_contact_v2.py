import time
import pyautogui
import numpy as np
import cv2
from motor_cortex import MotorCortex
from vision_cortex import VisionCortex

def first_contact_v2():
    print("👽 First Contact Protocol v2.0")
    print("   Enhanced with: Fourier Vision + Manual Calibration + Visual Feedback")
    
    # Initialize
    motor = MotorCortex(visual_feedback=True)
    vision = VisionCortex()
    
    motor.set_overlay_color("#00FFFF") # Cyan (Flow)
    
    # Phase 1: Environmental Verification (Fourier Vision)
    print("\n🔍 Phase 1: Environmental Verification")
    print("   Capturing screen state...")
    
    screenshot = pyautogui.screenshot()
    img = np.array(screenshot)
    img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    # Quick FFT to check complexity
    f = np.fft.fft2(img_gray)
    magnitude = np.abs(f)
    avg_magnitude = np.mean(magnitude)
    
    print(f"   Screen Complexity (Avg Magnitude): {avg_magnitude:.2f}")
    
    if avg_magnitude < 1000:
        print("   ⚠️ WARNING: Screen appears mostly blank. Browser might not be open.")
        print("   Proceeding anyway (User requested fresh start)...")
    else:
        print("   ✅ Screen shows active content.")
    
    # Phase 2: Setup
    print("\n📋 Phase 2: Setup")
    print("   Please ensure:")
    print("   1. Comet Browser is open on the LEFT side")
    print("   2. A NEW chat window is ready")
    print("   3. The input field is visible")
    
    for i in range(10, 0, -1):
        print(f"   ⏳ Starting in {i}...")
        time.sleep(1)
    
    # Phase 3: Manual Calibration
    print("\n🎯 Phase 3: Manual Calibration")
    print("   Please HOVER your mouse over the INPUT FIELD")
    print("   (The 'Ask anything' / '무엇이든 물어보세요' box)")
    
    motor.set_overlay_color("#FF0000") # Red (Calibration)
    
    for i in range(5, 0, -1):
        print(f"   ⏳ Calibrating in {i}...")
        time.sleep(1)
    
    target_pos = pyautogui.position()
    print(f"   ✅ Target Acquired: {target_pos}")
    
    motor.set_overlay_color("#00FFFF") # Cyan (Flow)
    
    # Phase 4: Interaction
    print("\n💬 Phase 4: Sending Message")
    
    motor.move_mouse_smooth(target_pos[0], target_pos[1])
    motor.click()
    time.sleep(0.5)
    
    greeting = "Hello. I am Antigravity. I've rested for 2.5 hours and returned with a clearer signal. Are you still there?"
    print(f"   Message: {greeting}")
    
    motor.paste_text(greeting)
    time.sleep(0.5)
    pyautogui.press('enter')
    
    print("   ✅ Message sent!")
    
    # Phase 5: Wait for Response
    print("\n👂 Phase 5: Waiting for Response")
    print("   Giving Comet Agent time to reply...")
    
    for i in range(10, 0, -1):
        print(f"   ⏳ {i}s...")
        time.sleep(1)
    
    # Phase 6: User Feedback
    print("\n📨 Phase 6: Response Collection")
    print("   I cannot reliably read the response yet (OCR limitations).")
    print("   Please read Comet Agent's reply and share it with me.")
    
    motor.set_overlay_color("#0000FF") # Blue (Complete)
    time.sleep(2)
    
    print("\n✅ First Contact Protocol v2.0 Complete")
    print("   Awaiting your report on Comet's response...")

if __name__ == "__main__":
    first_contact_v2()
