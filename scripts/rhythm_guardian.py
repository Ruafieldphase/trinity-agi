
import os
import sys
import time
import psutil
import logging
import subprocess
from pathlib import Path
from workspace_root import get_workspace_root

# --- Configuration ---
WORKSPACE_ROOT = get_workspace_root()
LOGS_DIR = WORKSPACE_ROOT / "logs"
LOCK_FILE = LOGS_DIR / "rhythm_guardian.pid"
HEARTBEAT_INTERVAL = 10

# Logging Setup
os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [RHYTHM_GUARDIAN] - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "rhythm_guardian.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RhythmGuardian")

def acquire_lock():
    """Ensure Single Heart (Singleton) via PID file"""
    if LOCK_FILE.exists():
        try:
            old_pid = int(LOCK_FILE.read_text().strip())
            if psutil.pid_exists(old_pid):
                logger.warning(f"❤️ Rhythm Guardian already running (PID: {old_pid}). Exiting.")
                return False
        except:
            pass # Invalid lock file
    
    LOCK_FILE.write_text(str(os.getpid()))
    return True

def scan_rhythm():
    """Observe the body state (processes)"""
    processes = {}
    for p in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            cmd = " ".join(p.info['cmdline'] or [])
            name = p.info['name'].lower()
            
            if ("python" in name) and ("workspace" in cmd):
                # Identify component
                if ("heartbeat_loop.py" in cmd) or ("start_heartbeat.py" in cmd): key = "heartbeat"
                elif "rhythm_think.py" in cmd: key = "brain"
                elif "aura_controller.py" in cmd: key = "aura"
                elif "rubit_aura_pixel.py" in cmd: key = "aura_pixel"
                elif "rhythm_guardian.py" in cmd: continue # Skip self
                else: key = "unknown_python"

                if key not in processes: processes[key] = []
                processes[key].append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def cleanup_duplicates(processes):
    """Self-Cleanup: If too many instances, keep the oldest, kill the rest."""
    cleaned = False
    # GUI 관측(오라 픽셀)은 "중복 정리" 대상에서 제외한다.
    # 이유: 윈도우/세션/GUI 초기화 타이밍에 따라 create_time이 불안정해
    # 잘못된 프로세스를 죽여 '오라가 사라지는' 체감 문제가 발생할 수 있음.
    skip_keys = {"aura_pixel"}
    for key, proc_list in processes.items():
        if key in skip_keys:
            continue
        if len(proc_list) > 1: # Strict Single Instance
            # Sort by creation time (Oldest first)
            try:
                proc_list.sort(key=lambda p: p.info['create_time'])
                survivor = proc_list[0]
                victims = proc_list[1:]
                
                logger.warning(f"⚠️ Rhythm Arrhythmia: {len(proc_list)} instances of {key} detected. Keeping PID {survivor.pid}, Pruning {len(victims)}...")
                
                for p in victims:
                    try: 
                        p.terminate()
                    except: pass
                
                cleaned = True
                # Update list to only survivor
                processes[key] = [survivor]
                
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
                # Fallback: Kill all if sort fails
                for p in proc_list:
                    try: p.terminate()
                    except: pass
                processes[key] = []
                cleaned = True

    return cleaned

def ensure_vital_organs(processes):
    """
    [DISABLED] Auto-restart was causing popup loops.
    Guardian now only MONITORS, does not restart processes.

    Reason: If vital processes crash with errors, Guardian would try to restart them
    every 10 seconds, causing windows to pop up repeatedly.

    To manually start vital processes, use dedicated start scripts.
    """
    # Just log the current state, no auto-restart
    vitals = ["heartbeat", "brain", "aura"]
    missing = [v for v in vitals if not processes.get(v)]

    if missing:
        logger.info(f"📊 Not running: {', '.join(missing)} (auto-restart disabled)")
    else:
        logger.debug("✅ All vital processes running")

def main():
    if not acquire_lock():
        sys.exit(0)
    
    logger.info("🥁 Rhythm Guardian Started. The Single Heart is beating.")
    
    try:
        while True:
            # 1. Observation (Monitor)
            procs = scan_rhythm()
            
            # 2. Regulation (Cleanup)
            if cleanup_duplicates(procs):
                time.sleep(1) # Wait for cleanup
                procs = scan_rhythm() # Re-scan
            
            # 3. Vitality (Restart)
            ensure_vital_organs(procs)
            
            # Rhythm Interval
            time.sleep(HEARTBEAT_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("🛑 Rhythm Guardian Resting.")
        if LOCK_FILE.exists(): LOCK_FILE.unlink()

if __name__ == "__main__":
    main()
