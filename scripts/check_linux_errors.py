import os
import sys
from pathlib import Path
from credentials_manager import get_linux_vm_credentials
import paramiko

def check_errors():
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
        
        # Check agi-body error log (from service definition)
        print("\n📋 Last 50 lines of agi-body error log:")
        stdin, stdout, stderr = ssh.exec_command("tail -n 50 /home/bino/agi/logs/body.error.log")
        print(stdout.read().decode())
        
        # Check agi-background-self status and logs
        print("\n📋 Status of agi-background-self:")
        stdin, stdout, stderr = ssh.exec_command("systemctl --user status agi-background-self")
        print(stdout.read().decode())
        
        print("\n📋 Last 30 lines of agi-background-self logs:")
        stdin, stdout, stderr = ssh.exec_command("journalctl --user -u agi-background-self -n 30 --no-pager")
        print(stdout.read().decode())
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_errors()
