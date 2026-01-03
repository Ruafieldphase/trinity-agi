#!/usr/bin/env python3
import os
import sys
import time
import traceback
from pathlib import Path

# --- EARLY BIRD LOGGING ---
# Try to find a place to log even before ROOT is resolved
try:
    _temp_log = Path("c:/workspace/agi/outputs/bridge/agi_chat_early.log")
    _temp_log.parent.mkdir(parents=True, exist_ok=True)
    with open(_temp_log, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Script started. sys.path[0]={sys.path[0]}\n")
except:
    pass

def log_internal(msg: str):
    try:
        with open("c:/workspace/agi/outputs/bridge/agi_chat_early.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except:
        pass

try:
    import tkinter as tk
    log_internal("tkinter imported")
except Exception as e:
    log_internal(f"CRITICAL: Failed to import tkinter: {e}")
    sys.exit(1)

# --- WORKSPACE RESOLUTION ---
try:
    # Manual resolution to avoid dependency on workspace_root.py if it's broken
    ROOT = Path(__file__).resolve().parents[1]
    log_internal(f"Resolved ROOT manually: {ROOT}")
    
    # Try to add it to path anyway for other imports
    sys.path.append(str(ROOT / "scripts"))
    log_internal("Added scripts to sys.path")
except Exception as e:
    log_internal(f"CRITICAL: ROOT resolution failed: {e}")
    ROOT = Path("c:/workspace/agi")

INPUT_PATH = ROOT / "inputs" / "agi_chat.txt"
OUTPUT_PATH = ROOT / "outputs" / "agi_chat_response.txt"

class AGIChatWindow(tk.Tk):
    def __init__(self) -> None:
        log_internal("AGIChatWindow.__init__ start")
        super().__init__()
        self.title("AGI Chat")
        self.geometry("720x520")
        
        # Ensure visibility
        self.state('normal')
        self.focus_force()
        self.lift()
        self.attributes("-topmost", True)
        
        self.last_response_mtime = 0.0
        self._build_ui()
        self._poll_response()
        self._heartbeat()
        self._reinforce_focus()
        log_internal("AGIChatWindow.__init__ end")

    def _reinforce_focus(self) -> None:
        """Periodically reclaim focus and lift the window to combat stealing by bridge GUI automation."""
        try:
            self.lift()
            # self.attributes("-topmost", True) # Already set in __init__, but can be reinforced if needed
        except:
            pass
        self.after(3000, self._reinforce_focus)

    def _heartbeat(self) -> None:
        log_internal("Heartbeat: Window is alive")
        self.after(10000, self._heartbeat)

    def _build_ui(self) -> None:
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.chat = tk.Text(self, wrap="word", state="disabled")
        self.chat.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=8, pady=8)
        self.entry = tk.Entry(self)
        self.entry.grid(row=1, column=0, sticky="ew", padx=8)
        self.entry.bind("<Return>", lambda e: self._send_message())
        self.status = tk.Label(self, text="Healthy", anchor="w")
        self.status.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8)

    def _send_message(self) -> None:
        message = self.entry.get().strip()
        if not message: return
        log_internal(f"User sent: {message[:20]}")
        try:
            INPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            INPUT_PATH.write_text(message, encoding="utf-8")
            self._append_chat(f"You: {message}")
            self.entry.delete(0, "end")
        except Exception as e:
            log_internal(f"Send Error: {e}")

    def _append_chat(self, text: str) -> None:
        self.chat.configure(state="normal")
        self.chat.insert("end", text + "\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _poll_response(self) -> None:
        try:
            if OUTPUT_PATH.exists():
                mtime = OUTPUT_PATH.stat().st_mtime
                if mtime > self.last_response_mtime:
                    response = OUTPUT_PATH.read_text(encoding="utf-8").strip()
                    if response:
                        self._append_chat(f"AGI: {response}")
                        if "❓ [QUEST]" in response:
                            self.configure(bg="#ffebee")
                    self.last_response_mtime = mtime
        except Exception as e:
            log_internal(f"Poll Error: {e}")
        self.after(1000, self._poll_response)

def report_callback_exception(self, exc, val, tb):
    log_internal("--- CALLBACK EXCEPTION ---")
    log_internal(f"{exc}: {val}")
    log_internal("".join(traceback.format_exception(exc, val, tb)))

def main():
    try:
        log_internal("main() start")
        app = AGIChatWindow()
        # Set global exception handler for tkinter
        tk.Tk.report_callback_exception = report_callback_exception
        log_internal("mainloop() start")
        app.mainloop()
        log_internal("mainloop() end")
    except Exception as e:
        log_internal(f"FATAL ERROR: {e}")
        log_internal(traceback.format_exc())

if __name__ == "__main__":
    main()
