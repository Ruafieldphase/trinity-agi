
import paramiko
import os
import sys

# Add scripts to path to find credentials_manager
sys.path.append("c:/workspace/agi/scripts")
from credentials_manager import get_linux_vm_credentials

def check_remote_file(remote_path):
    creds = get_linux_vm_credentials()
    host = creds['host']
    user = creds['user']
    password = creds['password']

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)

    print(f"Checking {remote_path} on {host}...")
    # Check if 'platform' is in the file
    stdin, stdout, stderr = ssh.exec_command(f"grep 'platform' {remote_path}")
    res = stdout.read().decode()
    if res:
        print(f"Found 'platform' in {remote_path}:\n{res}")
    else:
        print(f"'platform' NOT found in {remote_path}")
        
    # Check file size
    stdin, stdout, stderr = ssh.exec_command(f"ls -l {remote_path}")
    print(f"File info: {stdout.read().decode()}")
    
    ssh.close()

if __name__ == "__main__":
    check_remote_file("/home/bino/agi/scripts/rhythm_think.py")
