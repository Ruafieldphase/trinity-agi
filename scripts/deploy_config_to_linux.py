#!/usr/bin/env python3
"""
Deploy config module to Linux VM via SFTP
"""
import paramiko
import sys
import os
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

LOCAL_BASE = Path(r"c:\workspace\agi")
REMOTE_BASE = "/home/bino/agi"

def deploy_config():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {USER}@{HOST}...")
        client.connect(HOST, username=USER, password=PASS, timeout=10)
        sftp = client.open_sftp()
        
        # Helper to ensure remote dir exists
        def ensure_remote_dir(remote_path):
            dirs = remote_path.split('/')
            path = ""
            for d in dirs:
                if not d: continue
                path += "/" + d
                try:
                    sftp.stat(path)
                except FileNotFoundError:
                    print(f"Creating remote dir: {path}")
                    sftp.mkdir(path)

        # Deploy Config Module (Recursive)
        local_conf_dir = LOCAL_BASE / "config"
        remote_conf_dir = f"{REMOTE_BASE}/config"
        
        ensure_remote_dir(remote_conf_dir)
        
        print(f"📂 Deploying config module from {local_conf_dir} to {remote_conf_dir}...")
        
        for root, dirs, files in os.walk(local_conf_dir):
            # Create relative path from config dir
            rel_path = Path(root).relative_to(local_conf_dir)
            remote_root = f"{remote_conf_dir}/{rel_path.as_posix()}" if str(rel_path) != "." else remote_conf_dir
            
            # Ensure subdirectory exists
            if str(rel_path) != ".":
                ensure_remote_dir(remote_root)
            
            for file in files:
                if file == "__pycache__" or file.endswith(".pyc"):
                    continue
                    
                local_file = Path(root) / file
                remote_file = f"{remote_root}/{file}"
                print(f"📤 Uploading config/{rel_path.as_posix()}/{file}..." if str(rel_path) != "." else f"📤 Uploading config/{file}...")
                sftp.put(str(local_file), remote_file)

        sftp.close()
        
        # Restart services
        print("\n🔄 Restarting services...")
        services = ["agi-rhythm", "agi-body", "agi-collaboration"]
        for svc in services:
            print(f"   Restarting {svc}...")
            client.exec_command(f"systemctl --user restart {svc}")
            
        print("\n⏳ Waiting 5 seconds for initialization...")
        time.sleep(5)
        
        # Check status
        print("\n🔍 Status Check:")
        cmd = "systemctl --user is-active agi-rhythm agi-body agi-collaboration"
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read().decode("utf-8").strip().split('\n')
        
        for svc, status in zip(services, output):
            icon = "✅" if status == "active" else "❌"
            print(f"   {icon} {svc}: {status}")

        client.close()
        print("\n✅ Deployment and restart complete!")
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")

if __name__ == "__main__":
    deploy_config()
