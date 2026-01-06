#!/usr/bin/env python3
"""
Rhythm Daemon Wrapper
=====================
Wraps rhythm_think.py to run continuously as a daemon.
"""
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from workspace_root import get_workspace_root

WORKSPACE = get_workspace_root()
import threading
import logging

WORKSPACE = get_workspace_root()

# Services to Manage
SERVICES = [
    {
        "name": "Heartbeat Loop (RUD Core)",
        "script": WORKSPACE / "agi_core" / "heartbeat_loop.py",
        "restart_policy": "always",
        "interval": 1  # Continuous loop
    },
    {
        "name": "Meta Supervisor (System Check)",
        "script": WORKSPACE / "scripts" / "meta_supervisor.py",
        "restart_policy": "interval",
        "interval": 300  # Every 5 mins
    },
    {
        "name": "Live Vision Analyzer (Visual Resonance)",
        "script": WORKSPACE / "agi_core" / "vision_stream" / "live_frame_analyzer.py",
        "restart_policy": "always",
        "interval": 1
    }
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(WORKSPACE / "logs" / "rhythm_daemon.log", encoding='utf-8')
    ]
)

def run_service(service):
    """Run a single service with crash recovery and silence."""
    name = service["name"]
    script = service["script"]
    interval = service["interval"]
    policy = service["restart_policy"]
    
    logging.info(f"🚀 Starting Service: {name}")
    
    # Ensure usage of pythonw.exe for absolute silence
    executable = sys.executable
    if sys.platform == "win32":
        if "python.exe" in executable.lower():
            executable = executable.lower().replace("python.exe", "pythonw.exe")
        # Final fallback: if sys.executable isn't finding it, try standard path
        if not Path(executable).exists():
            executable = r"C:\Python313\pythonw.exe" if Path(r"C:\Python313\pythonw.exe").exists() else "pythonw"
    
    while True:
        try:
            cmd = [executable, str(script)]
            
            # Silent Execution Flags
            startupinfo = None
            creationflags = 0
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creationflags = 0x08000000 # CREATE_NO_WINDOW
            
            # Execute
            if policy == "always":
                # Continuous process (like heartbeat)
                process = subprocess.Popen(
                    cmd, 
                    startupinfo=startupinfo, 
                    creationflags=creationflags,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                process.wait() # Wait for it to die (should run forever)
                logging.warning(f"⚠️ Service {name} exited unexpectedly. Restarting in 5s...")
                time.sleep(5)
                
            elif policy == "interval":
                # Periodic task
                subprocess.run(
                    cmd, 
                    check=False,
                    startupinfo=startupinfo, 
                    creationflags=creationflags,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logging.info(f"✅ Service {name} cycle completed. Sleeping {interval}s...")
                time.sleep(interval)
                
        except Exception as e:
            logging.error(f"❌ Error in service {name}: {e}")
            time.sleep(10)

def main():
    print(f"🎵 Universal Rhythm Daemon started at {datetime.now()}")
    print("=" * 60)
    
    threads = []
    for service in SERVICES:
        t = threading.Thread(target=run_service, args=(service,), daemon=True)
        t.start()
        threads.append(t)
        print(f"   Started thread for: {service['name']}")
        
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Daemon shutting down...")

if __name__ == "__main__":
    main()
