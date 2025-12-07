import paramiko
import sys
from pathlib import Path

# Add workspace root to path
sys.path.append("c:\\workspace\\agi\\scripts")
from credentials_manager import get_linux_vm_credentials

def check_uninstall_pip():
    creds = get_linux_vm_credentials()
    host = creds['host']
    user = creds['user']
    password = creds['password']
    
    print(f"Connecting to {user}@{host}...")
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=5)
        
        # Check pip list
        print("Checking pip list for 'antigravity'...")
        stdin, stdout, stderr = client.exec_command("/home/bino/venv/bin/pip list | grep -i antigravity")
        out = stdout.read().decode().strip()
        
        if out:
            print(f"FOUND package: {out}")
            print("Uninstalling...")
            stdin, stdout, stderr = client.exec_command("/home/bino/venv/bin/pip uninstall -y antigravity")
            print(stdout.read().decode())
            print(stderr.read().decode())
        else:
            print("Package 'antigravity' NOT FOUND in venv.")

        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_uninstall_pip()
