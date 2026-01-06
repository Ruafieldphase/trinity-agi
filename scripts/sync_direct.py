
import paramiko
import os
import sys

# Add scripts to path to find credentials_manager
sys.path.append("c:/workspace/agi/scripts")
from credentials_manager import get_linux_vm_credentials

def sync_direct(local_path, remote_path):
    creds = get_linux_vm_credentials()
    host = creds['host']
    user = creds['user']
    password = creds['password']

    with open(local_path, "r", encoding='utf-8') as f:
        content = f.read()

    print(f"Connecting to {host} as {user}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)

    print(f"Uploading {len(content)} chars to {remote_path}...")
    
    # Use sftp but correctly this time
    sftp = ssh.open_sftp()
    with sftp.file(remote_path, 'w') as f:
        f.write(content)
    sftp.close()
    
    print("Upload successful. Restarting agi-rhythm service...")
    ssh.exec_command("systemctl --user restart agi-rhythm")
    
    ssh.close()
    print("Sync complete.")

if __name__ == "__main__":
    sync_direct(
        "c:/workspace/agi/scripts/rhythm_think.py",
        "/home/bino/agi/scripts/rhythm_think.py"
    )
