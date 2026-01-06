#!/usr/bin/env python3
"""
Deploy GCP Credentials and Scripts to Linux
===========================================
Transfers GCP credentials and necessary scripts to the Linux VM.
Updates configuration to enable Vertex AI and Ion Mentoring.
"""
import os
import sys
import time
from pathlib import Path
from workspace_root import get_workspace_root

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))
from credentials_manager import get_linux_vm_credentials

import paramiko

# Configuration
WORKSPACE_ROOT = get_workspace_root()
LOCAL_CREDS_PATH = WORKSPACE_ROOT.parent / "original_data" / "Obsidian_Vault" / "Nas_Obsidian_Vault" / "naeda-genesis-5034a5936036.json"
REMOTE_AGI_DIR = "/home/bino/agi"
REMOTE_CONFIG_DIR = f"{REMOTE_AGI_DIR}/config"
REMOTE_SCRIPTS_DIR = f"{REMOTE_AGI_DIR}/scripts"
REMOTE_CREDS_PATH = f"{REMOTE_CONFIG_DIR}/naeda-genesis-5034a5936036.json"

SCRIPTS_TO_DEPLOY = [
    "ion_learner.py",
    "vertex_ai_smart_router.py",
    "compress_dialogue_to_ion.py"
]

def deploy():
    print("🚀 Starting GCP Deployment to Linux...")
    
    creds = get_linux_vm_credentials()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(creds['host'], username=creds['user'], password=creds['password'])
        sftp = client.open_sftp()
        
        # 1. Create Config Directory
        print(f"\n📁 Creating directory: {REMOTE_CONFIG_DIR}")
        client.exec_command(f"mkdir -p {REMOTE_CONFIG_DIR}")
        
        # 2. Transfer Credentials
        print(f"\n🔑 Transferring credentials...")
        if LOCAL_CREDS_PATH.exists():
            sftp.put(str(LOCAL_CREDS_PATH), REMOTE_CREDS_PATH)
            print(f"   ✅ Uploaded to {REMOTE_CREDS_PATH}")
        else:
            print(f"   ❌ Local credentials not found at {LOCAL_CREDS_PATH}")
            return

        # 3. Deploy Scripts
        print(f"\n📜 Deploying scripts...")
        for script in SCRIPTS_TO_DEPLOY:
            local_path = WORKSPACE_ROOT / "scripts" / script
            remote_path = f"{REMOTE_SCRIPTS_DIR}/{script}"
            
            if local_path.exists():
                sftp.put(str(local_path), remote_path)
                # Fix line endings (Windows -> Linux)
                client.exec_command(f"sed -i 's/\\r$//' {remote_path}")
                print(f"   ✅ Deployed {script}")
            else:
                print(f"   ⚠️  Script not found: {script}")

        # 4. Update background_self_bridge.py
        print(f"\n🔧 Updating background_self_bridge.py configuration...")
        
        # Read the remote file
        remote_bridge_path = f"{REMOTE_SCRIPTS_DIR}/linux/background_self_bridge.py"
        try:
            with sftp.open(remote_bridge_path, 'r') as f:
                content = f.read().decode('utf-8')
            
            # Replace the hardcoded Windows path with the Linux path
            # Also handle raw string r"..."
            new_content = content.replace(
                rf'r\"{LOCAL_CREDS_PATH}\"',
                f'"{REMOTE_CREDS_PATH}"'
            ).replace(
                f'\"{LOCAL_CREDS_PATH}\"',
                f'"{REMOTE_CREDS_PATH}"'
            )
            
            # Write back
            with sftp.open(remote_bridge_path, 'w') as f:
                f.write(new_content)
            print("   ✅ Configuration updated")
            
        except Exception as e:
            print(f"   ❌ Failed to update bridge script: {e}")

        # 5. Install Dependencies
        print(f"\n📦 Installing dependencies (google-cloud-aiplatform)...")
        # Use the venv python
        cmd = "/home/bino/venv/bin/pip install google-cloud-aiplatform"
        stdin, stdout, stderr = client.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print("   ✅ Dependencies installed")
        else:
            print(f"   ❌ Installation failed: {stderr.read().decode()}")

        # 6. Restart Services
        print(f"\n🔄 Restarting AGI services...")
        client.exec_command("systemctl --user restart agi-rhythm agi-body agi-collaboration")
        time.sleep(2)
        print("   ✅ Services restarted")

        sftp.close()
        client.close()
        print("\n✨ Deployment Complete!")

    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    deploy()
