#!/usr/bin/env python3
"""
Inspect systemd service files on Linux VM
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

def inspect_services():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {USER}@{HOST}...")
        client.connect(HOST, username=USER, password=PASS, timeout=10)
        
        service_files = [
            "/home/bino/.config/systemd/user/agi-rhythm.service",
            "/home/bino/.config/systemd/user/agi-collaboration.service",
            "/home/bino/.config/systemd/user/agi-body.service"
        ]
        
        for svc_file in service_files:
            print(f"\n{'='*60}")
            print(f"📄 Content of {svc_file}")
            print(f"{'='*60}")
            
            cmd = f"cat {svc_file}"
            stdin, stdout, stderr = client.exec_command(cmd)
            
            output = stdout.read().decode("utf-8")
            error = stderr.read().decode("utf-8")
            
            if output:
                print(output)
            if error:
                print(f"STDERR: {error}")
                
        # Check if log directory exists
        print(f"\n{'='*60}")
        print(f"📂 Checking log directory existence")
        print(f"{'='*60}")
        
        # We'll infer the log dir from the service files, but let's check common ones
        dirs_to_check = ["/home/bino/agi/logs", "/home/bino/logs"]
        
        for d in dirs_to_check:
            cmd = f"ls -ld {d}"
            stdin, stdout, stderr = client.exec_command(cmd)
            output = stdout.read().decode("utf-8").strip()
            error = stderr.read().decode("utf-8").strip()
            
            if output:
                print(f"✅ {d} exists: {output}")
            else:
                print(f"❌ {d} does not exist or error: {error}")

        client.close()
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")

if __name__ == "__main__":
    inspect_services()
