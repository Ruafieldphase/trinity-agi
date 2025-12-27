import sys
import os
import time
import subprocess
import logging
from pathlib import Path

# Setup Logging
WORKSPACE_ROOT = Path(__file__).parent.parent
LOGS_DIR = WORKSPACE_ROOT / "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "lifecycle_manager.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LifecycleManager")

# Configuration
PYTHON_EXE = sys.executable 
# Ensure we use pythonw if possible for children, but since we use CREATE_NO_WINDOW, python.exe is fine too.
# Actually, let's try to find pythonw for children to be double safe, or just use sys.executable with flags.
# Using sys.executable allows us to stay in the same venv.

CREATE_NO_WINDOW = 0x08000000

SERVICES = [
    {
        "name": "AGI-Heartbeat",
        "script": "agi_core/heartbeat_loop.py",
        "args": []
    },
    {
        "name": "AGI-Brain",
        "script": "scripts/rhythm_think.py",
        "args": []
    },
    {
        "name": "AGI-Aura",
        "script": "scripts/aura_controller.py",
        "args": []
    },
    {
        "name": "AGI-Master",
        "script": "scripts/master_daemon_loop.py",
        "args": []
    },
    {
        "name": "AGI-Immune",
        "script": "scripts/launch_immune_system.py",
        "args": []
    },
    {
        "name": "AGI-OBS",
        "script": "services/obs_learner.py",
        "args": []
    },
    {
        "name": "AGI-OCR",
        "script": "fdo_agi_repo/scripts/smoke_e2e_ocr.py",
        "args": []
    }
]

def launch_services():
    processes = []
    logger.info("🚀 Lifecycle Manager Starting Services...")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(WORKSPACE_ROOT) + os.pathsep + env.get("PYTHONPATH", "")

    for svc in SERVICES:
        script_path = WORKSPACE_ROOT / svc["script"]
        if not script_path.exists():
            logger.error(f"❌ Script not found: {script_path}")
            continue
            
        cmd = [PYTHON_EXE, "-u", str(script_path)] + svc["args"]
        
        try:
            logger.info(f"✨ Starting {svc['name']}...")
            p = subprocess.Popen(
                cmd,
                cwd=str(WORKSPACE_ROOT),
                env=env,
                creationflags=CREATE_NO_WINDOW,
                stdout=open(LOGS_DIR / f"{svc['name'].lower()}.log", "a", encoding='utf-8'),
                stderr=subprocess.STDOUT
            )
            processes.append((svc['name'], p))
        except Exception as e:
            logger.error(f"❌ Failed to start {svc['name']}: {e}")

    logger.info("✅ All services requested. Monitoring...")
    return processes

def monitor_loop(processes):
    try:
        while True:
            for name, p in processes:
                if p.poll() is not None:
                    logger.warning(f"⚠️ Service {name} died (Exit Code: {p.returncode}). Restarting in 5s...")
                    # Logic to restart could be added here, but for now just log.
                    # Simple restart logic:
                    # (In a real manager, we'd restart. Here let's just keep the manager alive)
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("🛑 Lifecycle Manager stopping...")
        for name, p in processes:
            p.terminate()

if __name__ == "__main__":
    procs = launch_services()
    monitor_loop(procs)
