#!/usr/bin/env python3
"""
List files in /home/bino/agi on Linux VM
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

def list_files():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {USER}@{HOST}...")
        client.connect(HOST, username=USER, password=PASS, timeout=10)
        
        cmd = "find /home/bino/agi -maxdepth 3 -not -path '*/.*'"
        stdin, stdout, stderr = client.exec_command(cmd)
        
        output = stdout.read().decode("utf-8")
        print(output)
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")

if __name__ == "__main__":
    list_files()
