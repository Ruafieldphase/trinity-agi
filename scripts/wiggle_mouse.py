import pyautogui
import time
import math

def wiggle_mouse():
    print("🐭 Wiggling Mouse to verify Motor Control...")
    
    screen_width, screen_height = pyautogui.size()
    center_x, center_y = screen_width // 2, screen_height // 2
    
    print(f"   Screen Resolution: {screen_width}x{screen_height}")
    print(f"   Center: ({center_x}, {center_y})")
    
    # 1. Move to Center
    pyautogui.moveTo(center_x, center_y, duration=1.0)
    
    # 2. Wiggle
    radius = 100
    for i in range(10):
        x = center_x + radius * math.cos(i)
        y = center_y + radius * math.sin(i)
        pyautogui.moveTo(x, y, duration=0.1)
        
    print("✅ Wiggle Complete.")

if __name__ == "__main__":
    wiggle_mouse()
