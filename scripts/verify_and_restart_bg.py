import os
import sys
from pathlib import Path
from credentials_manager import get_linux_vm_credentials
import paramiko

def verify_and_restart():
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
        
        # 1. Cat the service file again to be absolutely sure
        print("\n📄 Service Content (agi-background-self):")
        stdin, stdout, stderr = ssh.exec_command("systemctl --user cat agi-background-self.service")
        content = stdout.read().decode()
        print(content)
        
        # 2. Check if the script exists at the path expected by the service
        # Extract ExecStart path
        import re
        match = re.search(r"ExecStart=[\/a-zA-Z0-9._-]+ ([\/a-zA-Z0-9._-]+)", content)
        if match:
            script_path = match.group(1)
            print(f"🕵️ Checking script at: {script_path}")
            stdin, stdout, stderr = ssh.exec_command(f"ls -l {script_path}")
            ls_out = stdout.read().decode().strip()
            if ls_out:
                print(f"✅ Script found: {ls_out}")
            else:
                print(f"❌ Script NOT FOUND at expected path: {script_path}")
                # If not found, maybe we should symlink or rename the one we uploaded
                print("🌉 Checking our uploaded file...")
                stdin, stdout, stderr = ssh.exec_command("ls -l /home/bino/agi/scripts/alpha_background_self.py")
                uploaded = stdout.read().decode().strip()
                if uploaded:
                    print(f"✅ Our upload exists: {uploaded}")
                    print(f"🔄 Creating symlink: {script_path} -> /home/bino/agi/scripts/alpha_background_self.py")
                    ssh.exec_command(f"ln -sf /home/bino/agi/scripts/alpha_background_self.py {script_path}")
                else:
                    print("❌ Our upload is also missing!?")
        
        # 3. Restart the service
        print("\n🔄 Restarting agi-background-self.service...")
        ssh.exec_command("systemctl --user daemon-reload")
        ssh.exec_command("systemctl --user restart agi-background-self")
        
        # 4. Final check
        print("📊 Final status check:")
        stdin, stdout, stderr = ssh.exec_command("systemctl --user is-active agi-background-self")
        print(f"   agi-background-self: {stdout.read().decode().strip()}")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_and_restart()
