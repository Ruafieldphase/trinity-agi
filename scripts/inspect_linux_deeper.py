import os
import sys
from pathlib import Path
from credentials_manager import get_linux_vm_credentials
import paramiko

def inspect_more():
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
        
        # Check agi-collaboration.service
        stdin, stdout, stderr = ssh.exec_command("ls ~/.config/systemd/user/agi-collaboration.service")
        collab_path = stdout.read().decode().strip()
        if collab_path:
            print(f"📄 Found agi-collaboration service at: {collab_path}")
            stdin, stdout, stderr = ssh.exec_command(f"cat {collab_path}")
            print(stdout.read().decode())
        else:
            print("❌ agi-collaboration.service not found.")

        # Check rhythm_daemon.py
        print("\n📄 Checking rhythm_daemon.py content...")
        stdin, stdout, stderr = ssh.exec_command("cat /home/bino/agi/scripts/rhythm_daemon.py")
        print(stdout.read().decode())
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    inspect_more()
