#!/usr/bin/env python3
"""
Restart Linux Body Service
"""
import paramiko
import sys
import time
from pathlib import Path

# Import credentials manager
sys.path.insert(0, str(Path(__file__).parent))
from credentials_manager import get_linux_vm_credentials

def restart_body_service():
    creds = get_linux_vm_credentials()
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(creds['host'], username=creds['user'], password=creds['password'])
        
        print("🔄 Restarting agi-body service...")
        stdin, stdout, stderr = client.exec_command("systemctl --user restart agi-body")
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print("✅ Restart command sent successfully.")
            time.sleep(2)
            
            # Check status
            stdin, stdout, stderr = client.exec_command("systemctl --user is-active agi-body")
            status = stdout.read().decode('utf-8').strip()
            print(f"📊 Current Status: {status}")
            
            if status != 'active':
                print("⚠️ Service failed to start. Checking logs...")
                stdin, stdout, stderr = client.exec_command("journalctl --user -u agi-body -n 20 --no-pager")
                print(stdout.read().decode('utf-8'))
        else:
            print(f"❌ Failed to restart: {stderr.read().decode('utf-8')}")
            
        client.close()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    restart_body_service()
