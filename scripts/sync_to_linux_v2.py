
import paramiko
import os
import sys
import base64
from pathlib import Path

# Add scripts to path to find credentials_manager
sys.path.append("c:/workspace/agi/scripts")
from credentials_manager import get_linux_vm_credentials

def sync_via_b64(local_b64_path, remote_path):
    creds = get_linux_vm_credentials()
    host = creds['host']
    user = creds['user']
    password = creds['password']

    with open(local_b64_path, "r") as f:
        b64_data = f.read().strip()

    print(f"Connecting to {host} as {user}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=user, password=password)
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    print(f"Writing base64 to {remote_path} via SSH...")
    # Use a heredoc to avoid command line length limits
    cmd = f"base64 -d << 'EOF' > {remote_path}\n{b64_data}\nEOF"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    err = stderr.read().decode()
    if err:
        print(f"Error during upload: {err}")
    else:
        print("Upload successful. Restarting agi-rhythm service...")
        ssh.exec_command("systemctl --user restart agi-rhythm")
    
    ssh.close()
    print("Sync complete.")

if __name__ == "__main__":
    sync_via_b64(
        "c:/workspace/agi/scripts/rhythm_think.b64",
        "/home/bino/agi/scripts/rhythm_think.py"
    )
