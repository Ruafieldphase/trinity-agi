import time
import random
import pyautogui
import numpy as np
from motor_cortex import MotorCortex

def mouse_playground():
    """
    Free exploration mode: Learn mouse control through play.
    No specific goal - just explore and learn from the environment.
    """
    print("🎮 Mouse Playground - Free Exploration Mode")
    print("   Learning through curiosity and play...")
    
    motor = MotorCortex(visual_feedback=True)
    motor.set_overlay_color("#FFFF00")  # Yellow - Curiosity
    
    screen_width, screen_height = pyautogui.size()
    print(f"   Playground size: {screen_width}x{screen_height}")
    
    # Learning journal
    discoveries = []
    
    # Phase 1: Speed Exploration
    print("\n🏃 Phase 1: Speed Exploration")
    print("   Testing different movement speeds...")
    
    speeds = ["very_slow", "slow", "medium", "fast"]
    for speed in speeds:
        # Random destination
        x = random.randint(100, screen_width - 100)
        y = random.randint(100, screen_height - 100)
        
        print(f"   Moving to ({x}, {y}) at {speed} speed...")
        
        start_time = time.time()
        motor.move_mouse_smooth(x, y, speed=speed)
        duration = time.time() - start_time
        
        discoveries.append(f"{speed}: {duration:.2f}s to move")
        time.sleep(0.5)
    
    # Phase 2: Pattern Exploration
    print("\n🎨 Phase 2: Pattern Exploration")
    print("   Drawing different patterns...")
    
    patterns = ["circle", "square", "zigzag", "spiral"]
    
    for pattern in patterns:
        print(f"   Drawing {pattern}...")
        
        if pattern == "circle":
            # Draw a circle
            center_x = screen_width // 2
            center_y = screen_height // 2
            radius = 200
            
            for angle in range(0, 360, 30):
                rad = np.radians(angle)
                x = int(center_x + radius * np.cos(rad))
                y = int(center_y + radius * np.sin(rad))
                motor.move_mouse_smooth(x, y, speed="fast")
                time.sleep(0.1)
        
        elif pattern == "square":
            # Draw a square
            size = 400
            start_x = (screen_width - size) // 2
            start_y = (screen_height - size) // 2
            
            corners = [
                (start_x, start_y),
                (start_x + size, start_y),
                (start_x + size, start_y + size),
                (start_x, start_y + size),
                (start_x, start_y)
            ]
            
            for x, y in corners:
                motor.move_mouse_smooth(x, y, speed="medium")
                time.sleep(0.2)
        
        elif pattern == "zigzag":
            # Draw zigzag
            y = screen_height // 2
            for i in range(5):
                x1 = 200 + i * 300
                y1 = y - 100 if i % 2 == 0 else y + 100
                motor.move_mouse_smooth(x1, y1, speed="fast")
                time.sleep(0.1)
        
        elif pattern == "spiral":
            # Draw spiral
            center_x = screen_width // 2
            center_y = screen_height // 2
            
            for angle in range(0, 720, 20):
                rad = np.radians(angle)
                radius = angle / 4
                x = int(center_x + radius * np.cos(rad))
                y = int(center_y + radius * np.sin(rad))
                motor.move_mouse_smooth(x, y, speed="fast")
                time.sleep(0.05)
        
        discoveries.append(f"Pattern: {pattern} completed")
        time.sleep(1)
    
    # Phase 3: Click Exploration
    print("\n👆 Phase 3: Click Exploration")
    print("   Testing clicks at different locations...")
    
    motor.set_overlay_color("#00FF00")  # Green - Interaction
    
    # Try clicking at random spots
    for i in range(5):
        x = random.randint(200, screen_width - 200)
        y = random.randint(200, screen_height - 200)
        
        print(f"   Click test {i+1}: ({x}, {y})")
        motor.move_mouse_smooth(x, y, speed="medium")
        time.sleep(0.3)
        
        # Take screenshot before click
        before = pyautogui.screenshot(region=(x-50, y-50, 100, 100))
        
        motor.click()
        time.sleep(0.5)
        
        # Take screenshot after click
        after = pyautogui.screenshot(region=(x-50, y-50, 100, 100))
        
        # Check if anything changed
        before_arr = np.array(before)
        after_arr = np.array(after)
        diff = np.sum(np.abs(before_arr.astype(int) - after_arr.astype(int)))
        
        if diff > 10000:
            print(f"   ✅ Something changed! (diff: {diff})")
            discoveries.append(f"Click at ({x},{y}) caused change")
            motor.set_overlay_color("#00FF00")  # Green - Success
        else:
            print(f"   ⚪ No visible change (diff: {diff})")
            motor.set_overlay_color("#FF0000")  # Red - No effect
        
        time.sleep(0.5)
    
    # Phase 4: Edge Exploration
    print("\n🔍 Phase 4: Edge Exploration")
    print("   Testing screen boundaries...")
    
    motor.set_overlay_color("#FFFF00")  # Yellow - Curiosity
    
    edges = [
        ("top-left", 10, 10),
        ("top-right", screen_width - 10, 10),
        ("bottom-right", screen_width - 10, screen_height - 10),
        ("bottom-left", 10, screen_height - 10),
        ("center", screen_width // 2, screen_height // 2)
    ]
    
    for name, x, y in edges:
        print(f"   Exploring {name} corner: ({x}, {y})")
        motor.move_mouse_smooth(x, y, speed="medium")
        time.sleep(0.5)
    
    # Phase 5: Precision Test
    print("\n🎯 Phase 5: Precision Test")
    print("   Testing fine motor control...")
    
    # Move to center
    center_x = screen_width // 2
    center_y = screen_height // 2
    motor.move_mouse_smooth(center_x, center_y)
    
    # Make tiny movements
    for dx, dy in [(5, 0), (0, 5), (-5, 0), (0, -5), (10, 10), (-10, -10)]:
        new_x = center_x + dx
        new_y = center_y + dy
        print(f"   Micro-movement: ({dx}, {dy})")
        motor.move_mouse_smooth(new_x, new_y, speed="very_slow")
        time.sleep(0.3)
    
    # Summary
    print("\n📊 Learning Summary")
    print("   Discoveries made:")
    for i, discovery in enumerate(discoveries, 1):
        print(f"   {i}. {discovery}")
    
    motor.set_overlay_color("#0000FF")  # Blue - Complete
    time.sleep(2)
    
    print("\n✅ Playground session complete!")
    print("   I've learned about speed, patterns, clicks, edges, and precision.")
    print("   Ready for more directed tasks.")

if __name__ == "__main__":
    mouse_playground()
