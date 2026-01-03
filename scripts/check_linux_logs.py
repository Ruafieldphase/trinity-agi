import os
import sys
from pathlib import Path
from credentials_manager import get_linux_vm_credentials
import paramiko

def check_linux_logs():
    # Get Credentials
    creds = get_linux_vm_credentials()
    if not creds:
        print("❌ Could not find Linux VM credentials.")
        return

    host = creds.get("host")
    user = creds.get("user")
    pw = creds.get("password")

    try:
        # Create SSH Client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=pw)
        
        print(f"✅ Connected to {host} as {user}")
        
        # Check logs
        stdin, stdout, stderr = ssh.exec_command("journalctl --user -u agi-rhythm -n 50 --no-pager")
        print("📋 Last 50 lines of agi-rhythm logs:")
        print(stdout.read().decode())
        
        # Check if background_self_bridge.py is running
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep background_self_bridge")
        print("🕵️ Process Check (alpha_background_self):")
        print(stdout.read().decode())
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_linux_logs()
