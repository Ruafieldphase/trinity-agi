
import tkinter as tk
import sys
from pathlib import Path

# Mock or use parts of rubit_aura_pixel
sys.path.insert(0, r"C:\workspace\agi\scripts")
import rubit_aura_pixel

def test_gui():
    print("Starting GUI test...")
    try:
        # Just try to create the root as it would in run_gui
        root = tk.Tk()
        root.overrideredirect(True)
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        t = 2
        print(f"Screen: {sw}x{sh}")
        
        root.geometry(f"{sw}x{sh}+0+0")
        trans_color = "#123456"
        root.config(bg=trans_color)
        root.wm_attributes("-transparentcolor", trans_color)
        
        f_top = tk.Frame(root, bg="#444444", height=t)
        f_top.place(x=0, y=0, width=sw)
        
        print("Success setting up frames. Closing in 2s...")
        root.after(2000, root.destroy)
        root.mainloop()
        print("Mainloop finished.")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gui()
