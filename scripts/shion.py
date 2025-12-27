#!/usr/bin/env python3
"""
Shion (The Silent Heart) v2
===========================
Robust invisible body.
Fixes:
1. Flashing windows (enforces StartupInfo + pythonw)
2. Restart loops (adds Cooldown mechanism)
3. Detection failures (more robust scanning)
"""
import os
import sys
import time
import psutil
import logging
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# --- Configuration ---
WORKSPACE_ROOT = Path(__file__).parent.parent
LOGS_DIR = WORKSPACE_ROOT / "logs"
PID_FILE = LOGS_DIR / "shion.pid"
VITALS_CHECK_INTERVAL = 10 
RESTART_COOLDOWN = 60 # Don't restart same organ within 60s

# Logging
os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [SHION] - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "shion.log", encoding='utf-8')
    ]
)
logger = logging.getLogger("Shion")

# State
last_restart_time = {}

def acquire_lock():
    """Ensure Single Body"""
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            if psutil.pid_exists(old_pid):
                return False
        except: pass
    PID_FILE.write_text(str(os.getpid()))
    return True

def get_pythonw():
    """Locate the invisible limb"""
    # 1. Try known location in workspace
    venv_w = WORKSPACE_ROOT / ".venv" / "Scripts" / "pythonw.exe"
    if venv_w.exists(): return str(venv_w)
    
    # 2. Try replacing current executable
    python_exe = sys.executable
    if "python.exe" in python_exe.lower():
        pythonw = python_exe.replace("python.exe", "pythonw.exe")
        if os.path.exists(pythonw): return pythonw
        
    return python_exe 

def scan_organs():
    """Sense internal organs (Robust)"""
    organs = {}
    for p in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'cwd']):
        try:
            # Match by CWD if cmdline is restricted
            try:
                if str(WORKSPACE_ROOT).lower() not in p.cwd().lower():
                    continue
            except: 
                # If cannot read CWD, relying on cmdline
                pass

            cmd = " ".join(p.info['cmdline'] or []).lower()
            name = p.info['name'].lower()
            
            # Key matching
            key = "unknown"
            if "heartbeat_loop.py" in cmd: key = "heartbeat"
            elif "rhythm_think.py" in cmd: key = "brain"
            elif "aura_controller.py" in cmd: key = "aura"
            elif "shion.py" in cmd: continue 
            
            if key != "unknown":
                if key not in organs: organs[key] = []
                organs[key].append(p)
        except: continue
    return organs

def cleanup_duplicates(organs):
    """Normalize Arrhythmia (Keep Oldest)"""
    for key, procs in organs.items():
        if len(procs) > 1:
            procs.sort(key=lambda p: p.info['create_time'])
            logger.warning(f"⚠️ Arrhythmia in {key}: Keeping {procs[0].pid}, Pruning {len(procs)-1}...")
            for p in procs[1:]:
                try: p.terminate()
                except: pass

def ensure_vitality(organs):
    """The Metabolism Loop (With Cooldown)"""
    vitals = {
        "heartbeat": "agi_core/heartbeat_loop.py",
        "brain": "scripts/rhythm_think.py",
        "aura": "scripts/aura_controller.py"
    }
    
    pythonw = get_pythonw()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(WORKSPACE_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    
    # Windows Startup Info for Hidden Process
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE

    for key, script_rel in vitals.items():
        # Check Cooldown
        if time.time() - last_restart_time.get(key, 0) < RESTART_COOLDOWN:
            continue

        if not organs.get(key):
            script = WORKSPACE_ROOT / script_rel
            if not script.exists(): continue
                
            logger.info(f"💓 Igniting {key} (Silent)...")
            try:
                subprocess.Popen(
                    [pythonw, "-u", str(script)],
                    cwd=str(WORKSPACE_ROOT),
                    env=env,
                    startupinfo=startupinfo, # Extra silence force
                    creationflags=0x08000000, # CREATE_NO_WINDOW
                    stdout=open(LOGS_DIR / f"{key}.log", "a", encoding='utf-8'),
                    stderr=subprocess.STDOUT
                )
                last_restart_time[key] = time.time()
            except Exception as e:
                logger.error(f"❌ Ignition Failed: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--silent-mode", action="store_true")
    args = parser.parse_args()

    if not acquire_lock():
        sys.exit(0)

    logger.info("🌊 Shion v2 (Cooldown Protected) Awakened.")
    
    try:
        while True:
            # 1. Sense
            organs = scan_organs()
            
            # 2. Harmonize
            cleanup_duplicates(organs)
            
            # 3. Vitalize
            ensure_vitality(organs)
            
            time.sleep(VITALS_CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        if PID_FILE.exists(): PID_FILE.unlink()

if __name__ == "__main__":
    main()
