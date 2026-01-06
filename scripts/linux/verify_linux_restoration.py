import paramiko
import sys
import time
from pathlib import Path

# Add workspace to path for credentials
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
from credentials_manager import get_linux_vm_credentials

def verify_linux_services():
    creds = get_linux_vm_credentials()
    HOST = creds['host']
    USER = creds['user']
    PASS = creds['password']
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USER, password=PASS, timeout=10)
        
        print("\n--- Linux AGI Service Verification ---")
        services = ['agi-rhythm', 'agi-body', 'agi-background-self']
        for svc in services:
            stdin, stdout, stderr = client.exec_command(f'systemctl --user is-active {svc}')
            status = stdout.read().decode().strip()
            print(f"[{svc}] Status: {status}")
            
        print("\n--- last 5 lines of agi-body.log ---")
        stdin, stdout, stderr = client.exec_command('tail -n 5 /home/bino/agi/logs/body.log')
        print(stdout.read().decode().strip())

        print("\n--- last 5 lines of body.error.log ---")
        stdin, stdout, stderr = client.exec_command('tail -n 5 /home/bino/agi/logs/body.error.log')
        print(stdout.read().decode().strip())
        
        client.close()
    except Exception as e:
        print(f"❌ Verification Error: {e}")

if __name__ == "__main__":
    verify_linux_services()
