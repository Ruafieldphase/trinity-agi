#!/usr/bin/env python3
"""
Check Linux VM file status and sync health
"""
import paramiko
import json
from pathlib import Path
from datetime import datetime
import sys

# Import credentials manager
sys.path.insert(0, str(Path(__file__).parent))
from credentials_manager import get_linux_vm_credentials

# Configuration
creds = get_linux_vm_credentials()
HOST = creds['host']
USER = creds['user']
PASS = creds['password']
REMOTE_DIR = "/home/bino/agi/outputs"

def check_linux_files():
    """Check the status of files on Linux VM"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USER, password=PASS, timeout=10)
        sftp = client.open_sftp()
        
        print("=" * 60)
        print("🔍 Linux VM File Status Check")
        print("=" * 60)
        
        # Check thought_stream_latest.json
        try:
            stat = sftp.stat(f"{REMOTE_DIR}/thought_stream_latest.json")
            mtime = datetime.fromtimestamp(stat.st_mtime)
            print(f"\n✅ thought_stream_latest.json")
            print(f"   Size: {stat.st_size} bytes")
            print(f"   Last Modified: {mtime}")
        except FileNotFoundError:
            print(f"\n❌ thought_stream_latest.json NOT FOUND")
        
        # Check feeling_latest.json
        try:
            stat = sftp.stat(f"{REMOTE_DIR}/feeling_latest.json")
            mtime = datetime.fromtimestamp(stat.st_mtime)
            print(f"\n✅ feeling_latest.json")
            print(f"   Size: {stat.st_size} bytes")
            print(f"   Last Modified: {mtime}")
            
            # Read content
            with sftp.open(f"{REMOTE_DIR}/feeling_latest.json", "r") as f:
                content = f.read().decode("utf-8")
                data = json.loads(content)
                print(f"   Timestamp in file: {data.get('timestamp', 'N/A')}")
                
        except FileNotFoundError:
            print(f"\n❌ feeling_latest.json NOT FOUND")
        except Exception as e:
            print(f"\n⚠️ Error reading feeling_latest.json: {e}")
        
        # Check rhythm service logs
        print(f"\n📋 Recent Rhythm Log (last 20 lines):")
        print("-" * 60)
        try:
            stdin, stdout, stderr = client.exec_command("tail -n 20 /home/bino/agi/logs/rhythm.log")
            log_output = stdout.read().decode("utf-8")
            print(log_output)
        except Exception as e:
            print(f"⚠️ Could not read rhythm.log: {e}")
        
        # Check systemd service status
        print(f"\n🔧 Systemd Service Status:")
        print("-" * 60)
        try:
            stdin, stdout, stderr = client.exec_command("systemctl --user is-active agi-rhythm agi-body agi-collaboration")
            status_output = stdout.read().decode("utf-8")
            services = ["agi-rhythm", "agi-body", "agi-collaboration"]
            statuses = status_output.strip().split("\n")
            for svc, stat in zip(services, statuses):
                icon = "✅" if stat == "active" else "❌"
                print(f"   {icon} {svc}: {stat}")
        except Exception as e:
            print(f"⚠️ Could not check service status: {e}")
        
        sftp.close()
        client.close()
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_linux_files()
