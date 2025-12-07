import paramiko
import sys
from pathlib import Path

# Add workspace root to path
sys.path.append("c:\\workspace\\agi\\scripts")
from credentials_manager import get_linux_vm_credentials

def perform_cleanup():
    creds = get_linux_vm_credentials()
    host = creds['host']
    user = creds['user']
    password = creds['password']
    
    print(f"Connecting to {user}@{host}...")
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=5)
        
        # Delete ~/.antigravity
        path_to_delete = f"/home/{user}/.antigravity"
        print(f"Deleting {path_to_delete}...")
        
        stdin, stdout, stderr = client.exec_command(f"rm -rf {path_to_delete}")
        err = stderr.read().decode().strip()
        
        if err:
            print(f"Error deleting: {err}")
        else:
            print("Deletion successful.")
            
        # Verify
        stdin, stdout, stderr = client.exec_command(f"ls -ld {path_to_delete}")
        out = stdout.read().decode().strip()
        if "No such file" in stderr.read().decode() or not out:
            print("VERIFIED: Directory is gone.")
        else:
            print(f"WARNING: Directory still exists: {out}")

        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    perform_cleanup()
