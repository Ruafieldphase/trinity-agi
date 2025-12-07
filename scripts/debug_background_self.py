import paramiko
import sys
from pathlib import Path

# Add workspace root to path
sys.path.append("c:\\workspace\\agi\\scripts")
from credentials_manager import get_linux_vm_credentials

def debug_service():
    creds = get_linux_vm_credentials()
    host = creds['host']
    user = creds['user']
    password = creds['password']
    
    print(f"Connecting to {user}@{host}...")
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=5)
        
        print("--- Standard Output Log ---")
        stdin, stdout, stderr = client.exec_command("tail -n 20 /home/bino/agi/logs/background_self.log")
        print(stdout.read().decode().strip())
        
        print("\n--- Error Log ---")
        stdin, stdout, stderr = client.exec_command("tail -n 20 /home/bino/agi/logs/background_self.error.log")
        print(stdout.read().decode().strip())
        
        client.close()
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    debug_service()
