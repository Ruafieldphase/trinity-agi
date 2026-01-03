import os
import sys
from pathlib import Path
from credentials_manager import get_linux_vm_credentials
import paramiko

def list_unit_files():
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
        
        # List unit files
        stdin, stdout, stderr = ssh.exec_command("systemctl --user list-unit-files | grep agi")
        print("🔧 Service Unit Files:")
        print(stdout.read().decode())
        
        # Check active status
        stdin, stdout, stderr = ssh.exec_command("systemctl --user is-active agi-rhythm agi-body agi-collaboration")
        status = stdout.read().decode().strip().split('\n')
        print(f"📊 Active Status: {status}")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    list_unit_files()
