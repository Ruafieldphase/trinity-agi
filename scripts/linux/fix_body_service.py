import paramiko
import sys
from pathlib import Path

# Add workspace to path for credentials
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
from credentials_manager import get_linux_vm_credentials

def fix_body_service():
    creds = get_linux_vm_credentials()
    HOST = creds['host']
    USER = creds['user']
    PASS = creds['password']
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USER, password=PASS, timeout=10)
        
        print(f"🔗 Connected to {HOST}")
        
        # 1. Install missing dependencies
        print("📦 Installing slack-bolt and requests...")
        stdin, stdout, stderr = client.exec_command('/home/bino/venv/bin/pip install slack-bolt requests')
        print(stdout.read().decode().strip())
        err = stderr.read().decode().strip()
        if err: print(f"DEBUG ERR: {err}")
        
        # 2. Reset failed states
        print("🔄 Resetting systemd failure states...")
        client.exec_command('systemctl --user reset-failed agi-body')
        
        # 3. Restart service
        print("🚀 Restarting agi-body.service...")
        client.exec_command('systemctl --user daemon-reload')
        client.exec_command('systemctl --user restart agi-body')
        
        import time
        time.sleep(2)
        
        # 4. Final verification
        print("\n--- Final Status Report ---")
        services = ['agi-rhythm', 'agi-body', 'agi-background-self']
        for svc in services:
            stdin, stdout, stderr = client.exec_command(f'systemctl --user is-active {svc}')
            status = stdout.read().decode().strip()
            print(f"[{svc}] Status: {status}")
            
        # Check logs if failed
        stdin, stdout, stderr = client.exec_command('systemctl --user is-active agi-body')
        if stdout.read().decode().strip() != "active":
            print("\n❌ agi-body is still not active. Tail of error log:")
            stdin, stdout, stderr = client.exec_command('tail -n 20 /home/bino/agi/logs/body.error.log')
            print(stdout.read().decode().strip())
        else:
            print("\n✅ All services restored and active.")
            
        client.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_body_service()
