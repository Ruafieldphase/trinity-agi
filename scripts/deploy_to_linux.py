#!/usr/bin/env python3
"""
Deploy code to Linux VM via SFTP
"""
import paramiko
import sys
import os
from pathlib import Path

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

def deploy_code():
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

        # 1. Deploy Scripts
        scripts_to_deploy = [
            "rhythm_daemon.py",
            "shion_auto_responder.py",
            "rhythm_think.py",
            "credentials_manager.py",
            "background_self_bridge.py"
        ]
        
        ensure_remote_dir(f"{REMOTE_BASE}/scripts")
        
        for script in scripts_to_deploy:
            local_path = LOCAL_BASE / "scripts" / script
            remote_path = f"{REMOTE_BASE}/scripts/{script}"
            if local_path.exists():
                print(f"📤 Uploading {script}...")
                sftp.put(str(local_path), remote_path)
            else:
                print(f"⚠️ Local file not found: {local_path}")

        # 2. Deploy Body Module (Recursive)
        local_body_dir = LOCAL_BASE / "body"
        remote_body_dir = f"{REMOTE_BASE}/body"
        
        ensure_remote_dir(remote_body_dir)
        
        for root, dirs, files in os.walk(local_body_dir):
            # Create relative path from body dir
            rel_path = Path(root).relative_to(local_body_dir)
            remote_root = f"{remote_body_dir}/{rel_path.as_posix()}" if str(rel_path) != "." else remote_body_dir
            
            # Ensure subdirectory exists
            if str(rel_path) != ".":
                ensure_remote_dir(remote_root)
            
            for file in files:
                if file == "__pycache__" or file.endswith(".pyc"):
                    continue
                    
                local_file = Path(root) / file
                remote_file = f"{remote_root}/{file}"
                print(f"📤 Uploading body/{rel_path.as_posix()}/{file}..." if str(rel_path) != "." else f"📤 Uploading body/{file}...")
                sftp.put(str(local_file), remote_file)

        # 3. Deploy .env if exists
        local_env = LOCAL_BASE / ".env"
        if local_env.exists():
            print(f"📤 Uploading .env...")
            sftp.put(str(local_env), f"{REMOTE_BASE}/.env")
        else:
            print(f"ℹ️ Local .env not found, skipping.")

        # 4. Deploy requirements.txt
        local_reqs = LOCAL_BASE / "requirements_linux.txt"
        if local_reqs.exists():
            print(f"📤 Uploading requirements_linux.txt as requirements.txt...")
            sftp.put(str(local_reqs), f"{REMOTE_BASE}/requirements.txt")
        else:
            print(f"⚠️ Local requirements_linux.txt not found!")

        sftp.close()
        client.close()
        print("\n✅ Deployment complete!")
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")

if __name__ == "__main__":
    deploy_code()
