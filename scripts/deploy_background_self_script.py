import paramiko
import sys
import os
from pathlib import Path

# Add workspace root to path
sys.path.append("c:\\workspace\\agi\\scripts")
from credentials_manager import get_linux_vm_credentials

def deploy_script():
    creds = get_linux_vm_credentials()
    host = creds['host']
    user = creds['user']
    password = creds['password']
    
    local_script = "c:\\workspace\\agi\\scripts\\linux\\background_self_bridge.py"
    remote_script = "/home/bino/agi/scripts/background_self_bridge.py"
    
    print(f"Deploying script to {user}@{host}...")
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=5)
        
        sftp = client.open_sftp()
        
        # Ensure directory exists
        client.exec_command("mkdir -p /home/bino/agi/scripts")
        
        # Upload script
        print(f"Uploading {local_script}...")
        sftp.put(local_script, remote_script)
        
        # Make executable
        client.exec_command(f"chmod +x {remote_script}")
        
        # Restart service
        print("Restarting service...")
        client.exec_command("systemctl --user restart agi-background-self")
        
        # Verify status
        stdin, stdout, stderr = client.exec_command("systemctl --user status agi-background-self")
        print(f"Service Status:\n{stdout.read().decode().strip()}")
        
        client.close()
        print("✅ Script Deployment Complete")
    except Exception as e:
        print(f"❌ Script Deployment Failed: {e}")

if __name__ == "__main__":
    deploy_script()
