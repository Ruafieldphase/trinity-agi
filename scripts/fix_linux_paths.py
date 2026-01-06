import os
import sys
from pathlib import Path
from credentials_manager import get_linux_vm_credentials
import paramiko

def fix_paths():
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
        
        # 1. Mass replace 'binoche' with 'bino' in the scripts directory
        print("\n🔧 Replacing '/home/bino/' with '/home/bino/' in ~/agi/scripts/...")
        ssh.exec_command("grep -rl '/home/bino/' /home/bino/agi/scripts/ | xargs -r sed -i 's|/home/bino/|/home/bino/|g'")
        
        # 2. Check if there are any remaining 'binoche'
        print("\n🔍 Checking for remaining 'binoche' references...")
        stdin, stdout, stderr = ssh.exec_command("grep -r 'binoche' /home/bino/agi/scripts/ 2>/dev/null")
        print(stdout.read().decode())
        
        # 3. Restart services to be sure
        print("\n🔄 Restarting all agi-related user services...")
        ssh.exec_command("systemctl --user restart agi-rhythm agi-background-self")
        
        ssh.close()
        print("Done.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_paths()
