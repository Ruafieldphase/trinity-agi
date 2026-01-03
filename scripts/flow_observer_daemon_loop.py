#!/usr/bin/env python3
"""
Flow Observer Daemon Loop for Linux
Continuously monitors flow state in the background
"""

import os
import sys
import time
import subprocess
import json
from datetime import datetime
from pathlib import Path
from workspace_root import get_workspace_root

# Configuration
BASE_DIR = get_workspace_root()
LOG_PATH = BASE_DIR / "outputs" / "flow_observer_daemon.log"
OBSERVER_SCRIPT = BASE_DIR / "fdo_agi_repo" / "copilot" / "flow_observer_integration.py"
TELEMETRY_SCRIPT = BASE_DIR / "scripts" / "linux_telemetry_collector.py"
PYTHON_PATH = os.path.expanduser("~/.agi_venv/bin/python")
NOTIFIER_SCRIPT = BASE_DIR / "scripts" / "resonance_notifier.py"

# Ensure Python exists
if not os.path.exists(PYTHON_PATH):
    PYTHON_PATH = sys.executable

# Ensure log directory
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

def log_daemon(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")

def start_telemetry():
    """Start telemetry collector in background"""
    try:
        proc = subprocess.Popen(
            [PYTHON_PATH, str(TELEMETRY_SCRIPT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        log_daemon(f"✅ Telemetry collector started (PID: {proc.pid})")
        return proc
    except Exception as e:
        log_daemon(f"❌ Failed to start telemetry: {e}", "ERROR")
        return None

def run_flow_analysis():
    """Run flow observer analysis and optionally send notifications"""
    try:
        result = subprocess.run(
            [PYTHON_PATH, str(OBSERVER_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout + result.stderr
        
        # Parse output for key information
        state, confidence, fear = None, None, None
        if "State:" in output:
            for line in output.split("\n"):
                if "State:" in line:
                    state = line.split("State:")[1].strip().split()[0]
                    log_daemon(f"📊 {line.strip()}")
                elif "Confidence:" in line:
                    try:
                        confidence = float(line.split("Confidence:")[1].strip())
                    except:
                        pass
                    log_daemon(f"📊 {line.strip()}")
                elif "Fear Level:" in line:
                    try:
                        fear = float(line.split("Fear Level:")[1].strip())
                    except:
                        pass
                    log_daemon(f"📊 {line.strip()}")
                elif "Perspective:" in line:
                    log_daemon(f"📊 {line.strip()}")
        
        # Send Slack notification if conditions met
        if state and confidence is not None and fear is not None:
            try:
                notify_result = subprocess.run(
                    [PYTHON_PATH, str(NOTIFIER_SCRIPT), 
                     "--state", state,
                     "--confidence", str(confidence),
                     "--fear", str(fear)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if notify_result.stdout:
                    log_daemon(f"🔔 {notify_result.stdout.strip()}")
            except Exception as e:
                log_daemon(f"⚠️ Notifier skipped: {e}", "DEBUG")
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        log_daemon("⚠️ Flow analysis timeout", "WARN")
        return False
    except Exception as e:
        log_daemon(f"❌ Flow analysis error: {e}", "ERROR")
        return False

def main():
    interval_seconds = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    
    log_daemon("🚀 Flow Observer Daemon started")
    log_daemon(f"   Interval: {interval_seconds} seconds")
    log_daemon(f"   Python: {PYTHON_PATH}")
    
    # Start telemetry
    telemetry_proc = start_telemetry()
    
    iteration = 0
    try:
        while True:
            iteration += 1
            log_daemon(f"🔄 Analysis iteration #{iteration}")
            
            success = run_flow_analysis()
            
            if not success:
                log_daemon("⚠️ Analysis had issues", "WARN")
            
            log_daemon(f"⏳ Waiting {interval_seconds} seconds...")
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        log_daemon("🛑 Daemon stopping (KeyboardInterrupt)")
    except Exception as e:
        log_daemon(f"❌ Fatal error: {e}", "ERROR")
    finally:
        # Cleanup
        if telemetry_proc:
            log_daemon("   Stopping telemetry collector...")
            telemetry_proc.terminate()
            try:
                telemetry_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                telemetry_proc.kill()
        
        log_daemon("✅ Daemon stopped")

if __name__ == "__main__":
    main()
