import tkinter as tk
import ctypes
import sys
import threading
import math
import time

# Windows API Constants
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
LWA_COLORKEY = 0x00000001
LWA_ALPHA = 0x00000002

<<<<<<< HEAD
# Aura Colors (Full Spectrum)
COLOR_SURVIVAL = "#FF0000"   # Red: Critical Threat / Survival Mode
COLOR_ANXIETY  = "#FF4500"   # Orange: Anxiety / Need / Warning
COLOR_FOCUS    = "#FFD700"   # Yellow: Analysis / Attention / Logic
COLOR_HARMONY  = "#00FF66"   # Green: Harmony / Stable / Healing
COLOR_EXPRESS  = "#00BFFF"   # Blue: Communication / Output / Speaking
COLOR_INSIGHT  = "#4B0082"   # Indigo: Deep Thought / Unconscious / Data Mining
COLOR_EXPLORE  = "#9933FF"   # Purple: Creativity / Exploration / Novelty

=======
>>>>>>> origin/main
class VisualOverlay:
    def __init__(self, initial_color='#00FFFF', thickness=100):
        self.root = tk.Tk()
        self.thickness = thickness
        self.color_mode = "pulse" if initial_color == "#00FFFF" else "static"
        self.current_static_color = initial_color
        
        # Remove window decorations
        self.root.overrideredirect(True)
        self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        self.root.lift()
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "black")
        self.root.wm_attributes("-alpha", 0.3) # Increased to 30% for more visibility
        
        # Create canvas
        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Draw border rectangles (store IDs to update them)
        self.rects = [] # List of lists: [[top, bottom, left, right], ...]
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        
        # Create stepped gradient (Smooth Glow)
        self.steps = 30 # Increased for smoothness
        self.step_size = thickness // self.steps
        if self.step_size < 1: self.step_size = 1
        
        for i in range(self.steps):
            # Calculate coords for this step (moving inwards)
            x1 = i * self.step_size
            y1 = i * self.step_size
            x2 = w - (i * self.step_size)
            y2 = h - (i * self.step_size)
            
            step_rects = []
            # Top
            step_rects.append(self.canvas.create_rectangle(x1, y1, x2, y1 + self.step_size, fill=initial_color, outline=""))
            # Bottom
            step_rects.append(self.canvas.create_rectangle(x1, y2 - self.step_size, x2, y2, fill=initial_color, outline=""))
            # Left
            step_rects.append(self.canvas.create_rectangle(x1, y1, x1 + self.step_size, y2, fill=initial_color, outline=""))
            # Right
            step_rects.append(self.canvas.create_rectangle(x2 - self.step_size, y1, x2, y2, fill=initial_color, outline=""))
            
            self.rects.append(step_rects)

        # Make click-through using Windows API
        self.make_click_through()
        
        # Start pulsing
        self.animate_pulse()

    def make_click_through(self):
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style = style | WS_EX_LAYERED | WS_EX_TRANSPARENT
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        except Exception as e:
            print(f"Error making window click-through: {e}")

    def animate_pulse(self):
        """Pulses the border color with a gradient effect."""
        if self.color_mode == "static":
            # Static color logic (simplified gradient)
            base_color = self.current_static_color
            # Parse hex to rgb
            try:
                r = int(base_color[1:3], 16)
                g = int(base_color[3:5], 16)
                b = int(base_color[5:7], 16)
            except:
                r, g, b = 0, 255, 255 # Fallback

            for i in range(self.steps):
                # Fade out inwards (Non-linear for better glow)
                factor = 1.0 - (i / self.steps)
                factor = factor * factor # Quadratic falloff for smoother glow
                
                ri, gi, bi = int(r * factor), int(g * factor), int(b * factor)
                color = f"#{ri:02x}{gi:02x}{bi:02x}"
                
                for rect_id in self.rects[i]:
                    self.canvas.itemconfig(rect_id, fill=color)
            
            self.root.after(50, self.animate_pulse)
            return

        # Pulse logic (Cyan <-> White)
        r_start, g_start, b_start = 0, 255, 255 # Cyan
        r_end, g_end, b_end = 200, 255, 255     # Lighter Cyan (not full white)
        
        # Simple interpolation
        t = (math.sin(time.time() * 3) + 1) / 2 # 0 to 1
        
        r_base = int(r_start + (r_end - r_start) * t)
        g_base = int(g_start + (g_end - g_start) * t)
        b_base = int(b_start + (b_end - b_start) * t)
        
        for i in range(self.steps):
            # Fade out inwards
            factor = 1.0 - (i / self.steps) 
            factor = factor * factor # Quadratic falloff
            
            ri = int(r_base * factor)
            gi = int(g_base * factor)
            bi = int(b_base * factor)
            
            color = f"#{ri:02x}{gi:02x}{bi:02x}"
            
            for rect_id in self.rects[i]:
                self.canvas.itemconfig(rect_id, fill=color)
        
        self.root.after(50, self.animate_pulse)

    def set_color(self, color_hex):
        """Sets the border color immediately."""
        self.current_static_color = color_hex
        self.color_mode = "static"
        if color_hex == "#00FFFF":
            self.color_mode = "pulse"

    def listen_for_commands(self):
        """Reads commands from stdin."""
        while True:
            try:
                line = sys.stdin.readline()
                if not line: break
                cmd = line.strip()
                if cmd.startswith("color:"):
                    color = cmd.split(":")[1]
                    self.root.after(0, lambda: self.set_color(color))
<<<<<<< HEAD
                elif cmd.startswith("state:"):
                    state = cmd.split(":")[1].strip().lower()
                    if state == "explore":
                        self.root.after(0, lambda: self.set_color(COLOR_EXPLORE))
                    elif state == "anxiety":
                        self.root.after(0, lambda: self.set_color(COLOR_ANXIETY))
                    elif state == "survival":
                        self.root.after(0, lambda: self.set_color(COLOR_SURVIVAL))
                    elif state == "focus":
                        self.root.after(0, lambda: self.set_color(COLOR_FOCUS))
                    elif state == "express":
                        self.root.after(0, lambda: self.set_color(COLOR_EXPRESS))
                    elif state == "insight":
                        self.root.after(0, lambda: self.set_color(COLOR_INSIGHT))
                    else:
                        self.root.after(0, lambda: self.set_color(COLOR_HARMONY))
=======
>>>>>>> origin/main
            except:
                break

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    color = sys.argv[1] if len(sys.argv) > 1 else "#00FFFF" # Cyan default
    overlay = VisualOverlay(initial_color=color)
    
    # Start command listener in background thread
    t = threading.Thread(target=overlay.listen_for_commands, daemon=True)
    t.start()
    
    overlay.run()
