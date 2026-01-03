import os
import sys
from pathlib import Path
from credentials_manager import get_linux_vm_credentials
import paramiko

def inspect_bg_self():
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
        
        # Check agi-background-self.service
        print("\n📄 Inspecting agi-background-self.service...")
        stdin, stdout, stderr = ssh.exec_command("systemctl --user cat agi-background-self.service")
        print(stdout.read().decode())
        
        print("\n📋 Last 20 lines of agi-background-self logs:")
        stdin, stdout, stderr = ssh.exec_command("journalctl --user -u agi-background-self -n 20 --no-pager")
        print(stdout.read().decode())

        # Check agi-body.service
        print("\n📄 Inspecting agi-body.service...")
        stdin, stdout, stderr = ssh.exec_command("systemctl --user cat agi-body.service")
        print(stdout.read().decode())
        
        print("\n📋 Last 20 lines of agi-body logs:")
        stdin, stdout, stderr = ssh.exec_command("journalctl --user -u agi-body -n 20 --no-pager")
        print(stdout.read().decode())
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    inspect_bg_self()
