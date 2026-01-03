import sys
import os
import tkinter as tk
from pathlib import Path

def run_diag():
    print(f"Python Version: {sys.version}")
    print(f"CWD: {os.getcwd()}")
    
    try:
        from workspace_root import get_workspace_root
        root = get_workspace_root()
        print(f"Resolved Root: {root}")
        print(f"Root Exists: {root.exists()}")
    except ImportError:
        print("Error: Could not import workspace_root")
        root = Path(os.getcwd())

    try:
        root_tk = tk.Tk()
        print("Tkinter: Successfully initialized Tk()")
        root_tk.destroy()
    except Exception as e:
        print(f"Tkinter Error: {e}")

    error_path = root / "outputs" / "bridge" / "agi_chat_window_diag.txt"
    try:
        error_path.parent.mkdir(parents=True, exist_ok=True)
        error_path.write_text("Diagnostic run completed successfully", encoding="utf-8")
        print(f"Diagnostic file written to: {error_path}")
    except Exception as e:
        print(f"File Write Error: {e}")

if __name__ == "__main__":
    run_diag()
