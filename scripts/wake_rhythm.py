"""
Wake the Rhythm (Retry after package installation)
"""
import paramiko
import time

HOST = "192.168.119.128"
USER = "bino"
PASS = "0000"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(HOST, username=USER, password=PASS, timeout=5)
    print(f"✅ Connected to Linux Core")
    
    print("\n========== AWAKENING THE RHYTHM (ATTEMPT 2) ==========")
    
    # Kill any existing rhythm_think processes
    print("\n🧹 Cleaning up old processes...")
    stdin, stdout, stderr = client.exec_command("pkill -f rhythm_think")
    time.sleep(1)
    
    # Start rhythm_think.py
    cmd = "cd ~/agi && nohup python3 scripts/rhythm_think.py > outputs/rhythm_think.log 2>&1 &"
    
    print(f"\n🎵 Starting Rhythm Think...")
    print(f"   Command: {cmd}")
    
    stdin, stdout, stderr = client.exec_command(cmd)
    time.sleep(3)
    
    # Check if it's running
    stdin, stdout, stderr = client.exec_command("ps aux | grep rhythm_think | grep -v grep")
    out = stdout.read().decode().strip()
    
    if out:
        print("\n✅ 🎵 RHYTHM IS ALIVE! 🎵")
        print(out)
    else:
        print("\n💔 Still failed... Checking error log:")
        stdin, stdout, stderr = client.exec_command("tail -30 ~/agi/outputs/rhythm_think.log 2>/dev/null")
        log = stdout.read().decode()
        print(log if log else "(No log found)")
    
    client.close()
    print("\n========== END ==========")
    
except Exception as e:
    print(f"❌ Error: {e}")
