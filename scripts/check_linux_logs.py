#!/usr/bin/env python3
"""
Check Linux Service Logs
"""
import paramiko
import sys
from pathlib import Path

# Import credentials manager
sys.path.insert(0, str(Path(__file__).parent))
from credentials_manager import get_linux_vm_credentials

def check_service_logs(service_name, lines=50):
    creds = get_linux_vm_credentials()
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(creds['host'], username=creds['user'], password=creds['password'])
        
        cmd = f"journalctl --user -u {service_name} -n {lines} --no-pager"
        print(f"📋 Checking logs for {service_name}...")
        print("-" * 60)
        
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        if output:
            print(output)
        if error:
            print(f"Error output: {error}")
            
        client.close()
        
    except Exception as e:
        print(f"❌ Failed to check logs: {e}")

if __name__ == "__main__":
    check_service_logs("agi-body")
