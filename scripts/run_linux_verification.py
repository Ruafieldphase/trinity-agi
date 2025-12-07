#!/usr/bin/env python3
"""
Deploy and Run Verification Script
==================================
"""
import sys
import time
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))
from credentials_manager import get_linux_vm_credentials

import paramiko

def deploy_and_verify():
    print("🔍 Deploying and running verification script...")
    
    creds = get_linux_vm_credentials()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    local_script = Path(__file__).parent / "verify_linux_vertex_local.py"
    remote_script = "/home/bino/agi/scripts/verify_linux_vertex.py"
    
    try:
        client.connect(creds['host'], username=creds['user'], password=creds['password'])
        sftp = client.open_sftp()
        
        # Upload
        sftp.put(str(local_script), remote_script)
        print(f"   ✅ Uploaded verification script to {remote_script}")
        
        # Execute
        cmd = f"/home/bino/venv/bin/python {remote_script}"
        stdin, stdout, stderr = client.exec_command(cmd)
        
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        print("\n[Linux Output]")
        print(output)
        
        if error:
            print("\n[Linux Error]")
            print(error)
            
        if "Initialized successfully" in output:
            print("\n✨ Verification PASSED!")
        else:
            print("\n❌ Verification FAILED")

        sftp.close()
        client.close()

    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    deploy_and_verify()
