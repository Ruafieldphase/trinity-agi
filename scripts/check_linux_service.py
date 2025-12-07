import paramiko
import sys
from pathlib import Path

# Add workspace root to path
sys.path.append("c:\\workspace\\agi\\scripts")
from credentials_manager import get_linux_vm_credentials

def check_service_status():
    creds = get_linux_vm_credentials()
    host = creds['host']
    user = creds['user']
    password = creds['password']
    
    print(f"Connecting to {user}@{host}...")
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=5)
        
        # Check if service file exists
        stdin, stdout, stderr = client.exec_command("ls -l /home/bino/.config/systemd/user/agi-background-self.service")
        print(f"Service File:\n{stdout.read().decode().strip()}{stderr.read().decode().strip()}")
        
        # Check service status
        stdin, stdout, stderr = client.exec_command("systemctl --user status agi-background-self")
        print(f"Service Status:\n{stdout.read().decode().strip()}{stderr.read().decode().strip()}")
        
        # Check logs if failed
        stdin, stdout, stderr = client.exec_command("journalctl --user -u agi-background-self -n 20 --no-pager")
        print(f"Recent Logs:\n{stdout.read().decode().strip()}")
        
        client.close()
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    check_service_status()
