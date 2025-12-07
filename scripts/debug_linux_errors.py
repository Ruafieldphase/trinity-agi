#!/usr/bin/env python3
"""
Fetch error logs and check script arguments on Linux VM
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

def debug_errors():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {USER}@{HOST}...")
        client.connect(HOST, username=USER, password=PASS, timeout=10)
        
        # 1. Fetch error logs
        log_files = [
            "/home/bino/agi/logs/body.error.log",
            "/home/bino/agi/logs/collaboration.error.log",
            "/home/bino/agi/logs/rhythm.error.log"
        ]
        
        for log_file in log_files:
            print(f"\n{'='*60}")
            print(f"📄 Content of {log_file}")
            print(f"{'='*60}")
            
            cmd = f"tail -n 50 {log_file}"
            stdin, stdout, stderr = client.exec_command(cmd)
            
            output = stdout.read().decode("utf-8")
            error = stderr.read().decode("utf-8")
            
            if output:
                print(output)
            elif error:
                print(f"⚠️ Error reading log (might be empty or missing): {error}")
            else:
                print("(Empty)")

        # 2. Check shion_auto_responder.py help
        print(f"\n{'='*60}")
        print(f"ℹ️ Checking shion_auto_responder.py arguments")
        print(f"{'='*60}")
        cmd = "/home/bino/venv/bin/python /home/bino/agi/scripts/shion_auto_responder.py --help"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode("utf-8"))
        print(stderr.read().decode("utf-8"))

        client.close()
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")

if __name__ == "__main__":
    debug_errors()
