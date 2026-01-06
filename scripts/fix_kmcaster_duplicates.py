#!/usr/bin/env python3
"""
Kill duplicate KMCaster processes and update launch script to prevent duplicates
"""
import sys
from pathlib import Path
import paramiko

sys.path.insert(0, str(Path(__file__).parent))
from credentials_manager import get_linux_vm_credentials

def fix_kmcaster_duplicates():
    creds = get_linux_vm_credentials()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"Connecting to {creds['host']}...")
        client.connect(creds['host'], username=creds['user'], password=creds['password'])
        
        # Check running KMCaster processes
        print("Checking for KMCaster processes...")
        stdin, stdout, stderr = client.exec_command("pgrep -f kmcaster.jar")
        pids = stdout.read().decode().strip().split('\n')
        pids = [p for p in pids if p]  # Remove empty strings
        
        if len(pids) > 1:
            print(f"⚠️ Found {len(pids)} KMCaster processes running!")
            print(f"PIDs: {pids}")
            
            # Kill all but keep one
            print("Killing duplicate processes...")
            for pid in pids[1:]:  # Keep the first one, kill the rest
                client.exec_command(f"kill {pid}")
            print(f"✅ Killed {len(pids) - 1} duplicate process(es)")
        elif len(pids) == 1:
            print(f"✅ Only one KMCaster process running (PID: {pids[0]})")
        else:
            print("ℹ️ No KMCaster processes currently running")
        
        # Update run_kmcaster.sh to prevent duplicates
        print("\nUpdating run_kmcaster.sh to prevent future duplicates...")
        
        improved_script = """#!/bin/bash
# Check if kmcaster is already running
if pgrep -f "kmcaster.jar" > /dev/null; then
    echo "KMCaster is already running!"
    exit 0
fi

# Start kmcaster
java -jar /home/bino/agi/tools/kmcaster.jar &
echo "KMCaster started!"
"""
        
        cmd = f"cat > /home/bino/agi/run_kmcaster.sh << 'EOF'\n{improved_script}\nEOF"
        stdin, stdout, stderr = client.exec_command(cmd)
        stdout.channel.recv_exit_status()
        
        client.exec_command("chmod +x /home/bino/agi/run_kmcaster.sh")
        
        print("✅ run_kmcaster.sh updated with duplicate prevention!")
        print("\n💡 Now when you run ./agi/run_kmcaster.sh, it will check if KMCaster is already running first.")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_kmcaster_duplicates()
