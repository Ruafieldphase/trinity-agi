import paramiko
import sys
import os
from pathlib import Path

# Add workspace root to path
sys.path.append("c:\\workspace\\agi\\scripts")
from credentials_manager import get_linux_vm_credentials

def deploy_service():
    creds = get_linux_vm_credentials()
    host = creds['host']
    user = creds['user']
    password = creds['password']
    
    local_service_file = "c:\\workspace\\agi\\scripts\\agi-background-self.service"
    remote_service_path = "/home/bino/.config/systemd/user/agi-background-self.service"
    
    print(f"Deploying service to {user}@{host}...")
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=5)
        
        sftp = client.open_sftp()
        
        # Ensure directory exists
        client.exec_command("mkdir -p /home/bino/.config/systemd/user")
        client.exec_command("mkdir -p /home/bino/agi/logs")
        
        # Upload service file
        print(f"Uploading {local_service_file}...")
        sftp.put(local_service_file, remote_service_path)
        
        # Reload daemon and start service
        print("Reloading systemd and starting service...")
        client.exec_command("systemctl --user daemon-reload")
        client.exec_command("systemctl --user enable agi-background-self")
        client.exec_command("systemctl --user restart agi-background-self")
        
        # Verify status
        stdin, stdout, stderr = client.exec_command("systemctl --user status agi-background-self")
        print(f"Service Status:\n{stdout.read().decode().strip()}")
        
        client.close()
        print("✅ Deployment Complete")
    except Exception as e:
        print(f"❌ Deployment Failed: {e}")

if __name__ == "__main__":
    deploy_service()
