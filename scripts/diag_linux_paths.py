import os
import sys
from pathlib import Path
from credentials_manager import get_linux_vm_credentials
import paramiko

def diag_linux():
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
        
        # Check remote environment
        stdin, stdout, stderr = ssh.exec_command("whoami; pwd; ls -d /home/*/agi/scripts 2>/dev/null")
        output = stdout.read().decode().strip().split('\n')
        print(f"🔍 Remote Info: {output}")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    diag_linux()
