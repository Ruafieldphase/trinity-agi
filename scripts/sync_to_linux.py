
import paramiko
import os
import sys
from pathlib import Path

# Add scripts to path to find credentials_manager
sys.path.append("c:/workspace/agi/scripts")
from credentials_manager import get_linux_vm_credentials

def sync_file_to_linux(local_path, remote_path):
    creds = get_linux_vm_credentials()
    host = creds['host']
    user = creds['user']
    password = creds['password']

    print(f"Connecting to {host} as {user}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=user, password=password)
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    print(f"Uploading {local_path} to {remote_path}...")
    sftp = ssh.open_sftp()
    sftp.put(local_path, remote_path)
    sftp.close()
    
    print("Restarting agi-rhythm service...")
    # Using --user because the service is a user service
    ssh.exec_command("systemctl --user restart agi-rhythm")
    
    ssh.close()
    print("Sync complete.")

if __name__ == "__main__":
    sync_file_to_linux(
        "c:/workspace/agi/scripts/rhythm_think.py",
        "/home/bino/agi/scripts/rhythm_think.py"
    )
