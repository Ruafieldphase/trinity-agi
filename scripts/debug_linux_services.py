#!/usr/bin/env python3
"""
Debug Linux VM services by fetching journalctl logs
"""
import paramiko
import sys
from pathlib import Path

# Import credentials manager
sys.path.insert(0, str(Path(__file__).parent))
from credentials_manager import get_linux_vm_credentials

# Configuration
creds = get_linux_vm_credentials()
HOST = creds['host']
USER = creds['user']
PASS = creds['password']

def debug_services():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {USER}@{HOST}...")
        client.connect(HOST, username=USER, password=PASS, timeout=10)
        
        services = ["agi-rhythm", "agi-body", "agi-collaboration"]
        
        for service in services:
            print(f"\n{'='*60}")
            print(f"🔍 Logs for {service}")
            print(f"{'='*60}")
            
            cmd = f"journalctl --user -u {service} -n 50 --no-pager"
            stdin, stdout, stderr = client.exec_command(cmd)
            
            output = stdout.read().decode("utf-8")
            error = stderr.read().decode("utf-8")
            
            if output:
                print(output)
            if error:
                print(f"STDERR: {error}")
                
        client.close()
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")

if __name__ == "__main__":
    debug_services()
