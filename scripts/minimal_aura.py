
import tkinter as tk
import time

def run():
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    t = 2
    root.geometry(f"{sw}x{sh}+0+0")
    tc = "#123456"
    root.config(bg=tc)
    root.wm_attributes("-transparentcolor", tc)
    
    f1 = tk.Frame(root, bg="red", height=t); f1.place(x=0, y=0, width=sw)
    f2 = tk.Frame(root, bg="red", height=t); f2.place(x=0, y=sh-t, width=sw)
    f3 = tk.Frame(root, bg="red", width=t); f3.place(x=0, y=t, height=sh-2*t)
    f4 = tk.Frame(root, bg="red", width=t); f4.place(x=sw-t, y=t, height=sh-2*t)
    
    def tick():
        print("Tick")
        root.after(1000, tick)
        
    tick()
    root.mainloop()

if __name__ == "__main__":
    run()
