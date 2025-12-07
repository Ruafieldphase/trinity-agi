"""
Create Rhythm Daemon on Linux
"""
import paramiko
import time

HOST = "192.168.119.128"
USER = "bino"
PASS = "0000"

daemon_code = r'''#!/usr/bin/env python3
"""
Rhythm Daemon (The Heartbeat)
=============================
Runs rhythm_think.py continuously to maintain the AGI's heartbeat.
"""
import time
import subprocess
import sys
from pathlib import Path

INTERVAL = 60  # Heartbeat every 60 seconds

def run_beat():
    try:
        # Run the thinking process
        result = subprocess.run(
            [sys.executable, "scripts/rhythm_think.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"[{time.strftime('%X')}] 💓 Thump-thump (Success)")
            # Optional: Print summary line if needed
        else:
            print(f"[{time.strftime('%X')}] 💔 Arrhythmia (Error):")
            print(result.stderr)
            
    except Exception as e:
        print(f"[{time.strftime('%X')}] ❌ Critical Failure: {e}")

def main():
    print("========== RHYTHM DAEMON STARTED ==========")
    print(f"Interval: {INTERVAL} seconds")
    
    while True:
        run_beat()
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
'''

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(HOST, username=USER, password=PASS, timeout=5)
    print(f"✅ Connected to Linux Core")
    
    # Write the file
    cmd = f"cat <<'EOF' > ~/agi/scripts/rhythm_daemon.py\n{daemon_code}\nEOF"
    client.exec_command(cmd)
    print("✅ Created scripts/rhythm_daemon.py")
    
    # Start the daemon
    print("🚀 Starting Rhythm Daemon...")
    cmd = "cd ~/agi && nohup python3 scripts/rhythm_daemon.py > outputs/rhythm_daemon.log 2>&1 &"
    client.exec_command(cmd)
    
    # Check status
    time.sleep(2)
    stdin, stdout, stderr = client.exec_command("ps aux | grep rhythm_daemon | grep -v grep")
    out = stdout.read().decode().strip()
    
    if out:
        print("✅ DAEMON IS RUNNING!")
        print(out)
    else:
        print("❌ Failed to start daemon")
        stdin, stdout, stderr = client.exec_command("cat ~/agi/outputs/rhythm_daemon.log")
        print(stdout.read().decode())

    client.close()
    print("\n========== END ==========")
    
except Exception as e:
    print(f"❌ Error: {e}")
