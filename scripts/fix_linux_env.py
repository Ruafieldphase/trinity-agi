#!/usr/bin/env python3
"""
Fix Linux VM environment: create directories and restart services
"""
import paramiko
import sys
from pathlib import Path
import time

# Import credentials manager
sys.path.insert(0, str(Path(__file__).parent))
from credentials_manager import get_linux_vm_credentials

# Configuration
creds = get_linux_vm_credentials()
HOST = creds['host']
USER = creds['user']
PASS = creds['password']

def fix_environment():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {USER}@{HOST}...")
        client.connect(HOST, username=USER, password=PASS, timeout=10)
        
        # 1. Create directories
        dirs = ["/home/bino/agi/logs", "/home/bino/agi/outputs"]
        for d in dirs:
            print(f"📂 Creating directory: {d}")
            cmd = f"mkdir -p {d}"
            stdin, stdout, stderr = client.exec_command(cmd)
            error = stderr.read().decode("utf-8")
            if error:
                print(f"⚠️ Error creating {d}: {error}")
            else:
                print(f"✅ Created {d}")
                
        # 2. Restart services
        services = ["agi-rhythm", "agi-body", "agi-collaboration"]
        print(f"\n🔄 Restarting services...")
        
        # Reload daemon first just in case
        client.exec_command("systemctl --user daemon-reload")
        
        for service in services:
            print(f"   Restarting {service}...")
            cmd = f"systemctl --user restart {service}"
            stdin, stdout, stderr = client.exec_command(cmd)
            error = stderr.read().decode("utf-8")
            if error:
                print(f"   ❌ Error restarting {service}: {error}")
            else:
                print(f"   ✅ Restart command sent for {service}")
        
        print("\n⏳ Waiting 5 seconds for services to initialize...")
        time.sleep(5)
        
        # 3. Check status immediately
        print(f"\n🔍 Immediate Status Check:")
        cmd = "systemctl --user is-active agi-rhythm agi-body agi-collaboration"
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read().decode("utf-8").strip().split('\n')
        
        for svc, status in zip(services, output):
            icon = "✅" if status == "active" else "❌"
            print(f"   {icon} {svc}: {status}")

        client.close()
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")

if __name__ == "__main__":
    fix_environment()
