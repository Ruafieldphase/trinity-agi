import os
import sys
from pathlib import Path
from credentials_manager import get_linux_vm_credentials
import paramiko

def inspect_service():
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
        
        # Locate service file
        stdin, stdout, stderr = ssh.exec_command("ls ~/.config/systemd/user/agi-rhythm.service")
        service_path = stdout.read().decode().strip()
        
        if not service_path:
            # Try global user path
            stdin, stdout, stderr = ssh.exec_command("ls /usr/lib/systemd/user/agi-rhythm.service")
            service_path = stdout.read().decode().strip()

        if service_path:
            print(f"📄 Found service file at: {service_path}")
            stdin, stdout, stderr = ssh.exec_command(f"cat {service_path}")
            print("--- Service Content ---")
            print(stdout.read().decode())
            print("-----------------------")
        else:
            print("❌ Could not find agi-rhythm.service file.")
            
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    inspect_service()
