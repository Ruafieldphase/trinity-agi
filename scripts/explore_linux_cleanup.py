import paramiko
import sys
from pathlib import Path

# Add workspace root to path
sys.path.append("c:\\workspace\\agi\\scripts")
from credentials_manager import get_linux_vm_credentials

def explore_cleanup_candidates():
    creds = get_linux_vm_credentials()
    host = creds['host']
    user = creds['user']
    password = creds['password']
    
    print(f"Connecting to {user}@{host}...")
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=5)
        
        # Check for AntiGravity specific paths
        paths_to_check = [
            "/usr/local/bin/antigravity",
            "/opt/antigravity",
            f"/home/{user}/.antigravity",
            "/etc/systemd/system/antigravity.service",
            f"/home/{user}/.config/systemd/user/antigravity.service"
        ]
        
        print("\nChecking for AntiGravity paths:")
        for path in paths_to_check:
            stdin, stdout, stderr = client.exec_command(f"ls -ld {path}")
            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
            if out:
                print(f"FOUND: {out}")
            else:
                print(f"NOT FOUND: {path}")
                
        # Check service files content to see what they run
        services = ["agi-rhythm", "agi-body", "agi-collaboration"]
        print("\nChecking Service Definitions:")
        for svc in services:
            cmd = f"systemctl --user cat {svc}"
            stdin, stdout, stderr = client.exec_command(cmd)
            content = stdout.read().decode().strip()
            print(f"--- {svc} ---")
            print(content)
            print("----------------")

        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    explore_cleanup_candidates()
