import paramiko
import sys
from pathlib import Path

# Add scripts to path for credentials
sys.path.insert(0, str(Path(__file__).parent))
from credentials_manager import get_linux_vm_credentials

def check_final_heartbeat():
    creds = get_linux_vm_credentials()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(creds['host'], username=creds['user'], password=creds['password'], timeout=10)
        
        # 1. Check if Cycle succeeded in rhythm.log
        print("--- RHYTHM HEARTBEAT CHECK ---")
        stdin, stdout, stderr = client.exec_command("tail -n 30 /home/bino/agi/logs/rhythm.log")
        log_content = stdout.read().decode('utf-8')
        print(log_content)
        
        if "finished successfully" in log_content or "[Cycle" in log_content:
            print("Heartbeat detected!")
        
        # 2. Check for fresh feeling_latest.json
        print("\n--- EMOTIONAL STATE CHECK ---")
        stdin, stdout, stderr = client.exec_command("ls -l /home/bino/agi/outputs/feeling_latest.json")
        print(stdout.read().decode('utf-8'))
        
        # 3. Final Service Status
        print("\n--- SERVICE STABILITY CHECK ---")
        stdin, stdout, stderr = client.exec_command("systemctl --user status agi-rhythm agi-body agi-collaboration")
        print(stdout.read().decode('utf-8'))
        
        client.close()
    except Exception as e:
        print(f"DIAG FAILURE: {e}")

if __name__ == "__main__":
    check_final_heartbeat()
