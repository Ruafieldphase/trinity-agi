import tkinter as tk
import random
import time
import threading

class VisualTarget:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Visual Target")
        self.root.geometry("400x400+100+100") # Fixed position (x=100, y=100)
        self.root.attributes('-topmost', True) # Keep on top
        
        self.canvas = tk.Canvas(self.root, width=400, height=400, bg='white')
        self.canvas.pack()
        
        # Draw a distinct Red Circle
        self.target_radius = 20
        self.target = self.canvas.create_oval(0, 0, 0, 0, fill='red', outline='black')
        
        self.running = True
        self.move_target()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def move_target(self):
        if not self.running: return
        
        # Random position within canvas
        x = random.randint(50, 350)
        y = random.randint(50, 350)
        
        x1 = x - self.target_radius
        y1 = y - self.target_radius
        x2 = x + self.target_radius
        y2 = y + self.target_radius
        
        self.canvas.coords(self.target, x1, y1, x2, y2)
        
        # Move every 2 seconds
        self.root.after(2000, self.move_target)

    def on_close(self):
        self.running = False
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    target = VisualTarget()
    target.run()
