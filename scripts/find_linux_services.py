import os
import sys
from pathlib import Path
from credentials_manager import get_linux_vm_credentials
import paramiko

def find_services():
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
        
        # Search for service files
        stdin, stdout, stderr = ssh.exec_command("find ~ -name '*.service' 2>/dev/null")
        print("📄 Found service files:")
        print(stdout.read().decode())
        
        # Also check systemd status for ALL user services
        stdin, stdout, stderr = ssh.exec_command("systemctl --user list-units --type=service")
        print("🔧 Active user services:")
        print(stdout.read().decode())
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    find_services()
