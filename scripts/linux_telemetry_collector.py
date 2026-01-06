import os
import time
import json
import datetime
import subprocess
import sys

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "telemetry")
os.makedirs(OUTPUT_DIR, exist_ok=True)

PID_FILE = os.path.join(OUTPUT_DIR, "observer_telemetry.pid")

# Check for existing instance
if os.path.exists(PID_FILE):
    try:
        with open(PID_FILE) as f:
            old_pid = int(f.read().strip())
        # Check if process is still running
        os.kill(old_pid, 0)
        print(f"⚠️ Telemetry collector already running (PID: {old_pid})")
        print("   Kill it first or wait for it to finish.")
        sys.exit(1)
    except (OSError, ValueError):
        # Process doesn't exist, remove stale PID file
        os.remove(PID_FILE)
        print("🧹 Removed stale PID file")

# Write our PID
with open(PID_FILE, 'w') as f:
    f.write(str(os.getpid()))
print(f"✅ Telemetry collector started (PID: {os.getpid()})")

def get_output_path():
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    return os.path.join(OUTPUT_DIR, f"stream_observer_{date_str}.jsonl")

def _get_active_window_xprop():
    """Get active window info using xprop (X11)"""
    try:
        # 1. Get Active Window ID
        root_res = subprocess.check_output(
            ["xprop", "-root", "_NET_ACTIVE_WINDOW"], 
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        
        # Parse: _NET_ACTIVE_WINDOW(WINDOW): window id # 0x400000b
        if "window id # " not in root_res:
            return None
        
        window_id = root_res.split("window id # ")[1].strip()
        if window_id == "0x0":
            return None

        # 2. Get Window Title
        title_res = subprocess.check_output(
            ["xprop", "-id", window_id, "_NET_WM_NAME"], 
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        
        # Parse: _NET_WM_NAME(UTF8_STRING) = "Title"
        window_title = "Unknown"
        if " = " in title_res:
            window_title = title_res.split(" = ")[1].strip('"')

        # 3. Get Window Class (Process Name)
        class_res = subprocess.check_output(
            ["xprop", "-id", window_id, "WM_CLASS"], 
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        
        # Parse: WM_CLASS(STRING) = "process_name", "Class Name"
        process_name = "unknown"
        if " = " in class_res:
            parts = class_res.split(" = ")[1].split(",")
            if parts:
                process_name = parts[0].strip().strip('"')

        return {
            "process_name": process_name,
            "window_title": window_title,
            "process_id": 0,  # xprop doesn't give PID easily without -spy or other tools
            "is_vscode": "code" in process_name.lower() or "vscode" in window_title.lower()
        }

    except Exception as e:
        # print(f"xprop error: {e}")
        return None

print(f"[linux_telemetry] Starting collector. Output: {OUTPUT_DIR}")

try:
    while True:
        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            
            # Get active window info using xprop
            window_info = _get_active_window_xprop()
            
            if window_info:
                record = {
                    "ts_utc": now.isoformat().replace("+00:00", "Z"),
                    "process_name": window_info["process_name"],
                    "process_id": window_info["process_id"], # This will be 0 from xprop
                    "window_title": window_info["window_title"],
                    "is_vscode": window_info["is_vscode"],
                    "vscode_file_guess": None
                }
            else:
                # Fallback if xprop fails or is not available
                record = {
                    "ts_utc": now.isoformat().replace("+00:00", "Z"),
                    "process_name": "linux_shell",
                    "process_id": os.getpid(), # This is the PID of the collector script
                    "window_title": "Active Linux Session (xprop unavailable)", 
                    "is_vscode": False,
                    "vscode_file_guess": None
                }
            
            output_path = get_output_path()
            with open(output_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
                
            time.sleep(5)
        except Exception as e:
            print(f"[linux_telemetry] Error: {e}")
            time.sleep(5)

except KeyboardInterrupt:
    print("\n🛑 Telemetry collector stopped")
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
        print("🧹 PID file removed")
