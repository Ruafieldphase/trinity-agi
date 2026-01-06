#!/usr/bin/env python3
"""
Update agi-body.service configuration on Linux VM
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

def update_service_config():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {USER}@{HOST}...")
        client.connect(HOST, username=USER, password=PASS, timeout=10)
        
        service_file = "/home/bino/.config/systemd/user/agi-body.service"
        
        # 1. Read current content
        print(f"Reading {service_file}...")
        cmd = f"cat {service_file}"
        stdin, stdout, stderr = client.exec_command(cmd)
        content = stdout.read().decode("utf-8")
        
        if "PYTHONPATH=/home/bino/agi" in content:
            print("✅ PYTHONPATH already updated.")
        else:
            print("🔄 Updating PYTHONPATH...")
            # Replace the line
            new_content = content.replace(
                "Environment=\"PYTHONPATH=/home/bino/venv/lib/python3.12/site-packages\"",
                "Environment=\"PYTHONPATH=/home/bino/agi:/home/bino/venv/lib/python3.12/site-packages\""
            )
            
            # Write back using a temporary file and mv
            temp_file = "/tmp/agi-body.service.new"
            sftp = client.open_sftp()
            with sftp.open(temp_file, 'w') as f:
                f.write(new_content)
            sftp.close()
            
            # Move to correct location
            cmd = f"mv {temp_file} {service_file}"
            client.exec_command(cmd)
            print("✅ Service file updated.")
            
            # Reload daemon
            print("🔄 Reloading systemd daemon...")
            client.exec_command("systemctl --user daemon-reload")

        # 2. Restart services
        print("🔄 Restarting services...")
        services = ["agi-rhythm", "agi-body", "agi-collaboration"]
        for svc in services:
            print(f"   Restarting {svc}...")
            client.exec_command(f"systemctl --user restart {svc}")
            
        print("\n⏳ Waiting 5 seconds for initialization...")
        time.sleep(5)
        
        # 3. Check status
        print("\n🔍 Status Check:")
        cmd = "systemctl --user is-active agi-rhythm agi-body agi-collaboration"
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read().decode("utf-8").strip().split('\n')
        
        for svc, status in zip(services, output):
            icon = "✅" if status == "active" else "❌"
            print(f"   {icon} {svc}: {status}")

        client.close()
        
    except Exception as e:
        print(f"\n❌ Update failed: {e}")

if __name__ == "__main__":
    update_service_config()
