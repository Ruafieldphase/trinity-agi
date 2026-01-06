import os
import sys
from pathlib import Path
from credentials_manager import get_linux_vm_credentials
import paramiko

def search_hardcoded_paths():
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
        
        # Search for 'binoche' in agi folder
        print("\n🔍 Searching for hardcoded 'binoche' paths in ~/agi/scripts/...")
        stdin, stdout, stderr = ssh.exec_command("grep -r 'binoche' /home/bino/agi/scripts/ 2>/dev/null")
        print(stdout.read().decode())
        
        # Search for 'alpha_background_self' in agi folder
        print("\n🔍 Searching for 'alpha_background_self' references in ~/agi/scripts/...")
        stdin, stdout, stderr = ssh.exec_command("grep -r 'alpha_background_self' /home/bino/agi/scripts/ 2>/dev/null")
        print(stdout.read().decode())

        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    search_hardcoded_paths()
