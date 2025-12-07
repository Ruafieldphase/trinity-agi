import pyautogui
import time
import random
import math
import threading
from typing import Tuple, Optional

# Safety Configuration
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.1      # Default pause between actions

class MotorCortex:
    def __init__(self, visual_feedback: bool = False):
        """
        Initializes the Motor Cortex.
        :param visual_feedback: If True, draws an overlay (requires visual_overlay.py)
        """
        self.visual_feedback = visual_feedback
        self.screen_width, self.screen_height = pyautogui.size()
        self.overlay = None
        
        if self.visual_feedback:
            self._init_overlay()
            
        print(f"🧠 Motor Cortex Initialized. Screen: {self.screen_width}x{self.screen_height}")

    def _init_overlay(self):
        # This would ideally connect to a running visual_overlay process
        # For now, we just print to console as fallback
        pass

    def set_overlay_color(self, color_hex: str):
        if self.visual_feedback:
            # TODO: Send IPC message to visual_overlay.py
            pass

    def move_mouse_smooth(self, x: int, y: int, duration: float = 0.5, speed: str = "medium"):
        """
        Moves the mouse to (x, y) with a human-like smooth curve.
        """
        # Speed presets
        if speed == "very_slow": duration = 1.5
        elif speed == "slow": duration = 1.0
        elif speed == "medium": duration = 0.5
        elif speed == "fast": duration = 0.2
        
        # Ensure coordinates are within screen bounds
        x = max(0, min(x, self.screen_width - 1))
        y = max(0, min(y, self.screen_height - 1))
        
        start_x, start_y = pyautogui.position()
        
        # Add some randomness to the path (Bezier curve control point)
        control_x = (start_x + x) / 2 + random.randint(-100, 100)
        control_y = (start_y + y) / 2 + random.randint(-100, 100)
        
        # Human-like movement using tweening
        # PyAutoGUI's moveTo with tween handles the smoothing, but we can add noise if needed.
        # Using easeOutQuad for natural deceleration
        pyautogui.moveTo(x, y, duration=duration, tween=pyautogui.easeOutQuad)

    def click(self, x: Optional[int] = None, y: Optional[int] = None, clicks: int = 1, button: str = 'left'):
        """
        Clicks at the current position or (x, y).
        """
        if x is not None and y is not None:
            self.move_mouse_smooth(x, y)
            
        pyautogui.click(clicks=clicks, button=button)

    def type_text(self, text: str, interval: float = 0.05):
        """
        Types text with a slight random delay between keystrokes to simulate human typing.
        """
        for char in text:
            pyautogui.write(char)
            time.sleep(interval + random.uniform(-0.02, 0.02))

    def press_key(self, key: str):
        """
        Presses a single key (e.g., 'enter', 'esc', 'ctrl').
        """
        pyautogui.press(key)

    def hotkey(self, *keys):
        """
        Executes a hotkey combination (e.g., 'ctrl', 'c').
        """
        pyautogui.hotkey(*keys)

    def scroll(self, clicks: int):
        """
        Scrolls the mouse wheel.
        """
        pyautogui.scroll(clicks)

    def get_position(self) -> Tuple[int, int]:
        return pyautogui.position()

if __name__ == "__main__":
    # Simple test
    motor = MotorCortex()
    print("Testing movement...")
    motor.move_mouse_smooth(500, 500, speed="fast")
    print("Done.")
