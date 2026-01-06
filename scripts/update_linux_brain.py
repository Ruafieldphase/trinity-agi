import paramiko
import time
import sys
from pathlib import Path

# Setup paths
LOCAL_SCRIPT = Path("c:/workspace/agi/scripts/rhythm_think.py")
REMOTE_SCRIPT = "/home/bino/agi/scripts/rhythm_think.py"

# Import credentials
sys.path.insert(0, str(Path(__file__).parent))
from credentials_manager import get_linux_vm_credentials

import base64

def update_brain():
    creds = get_linux_vm_credentials()
    
    print(f"🔌 Connecting to {creds['host']}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(
            creds['host'], 
            username=creds['user'], 
            password=creds['password'],
            timeout=10
        )
        
        # 1. Read Local File
        with open(LOCAL_SCRIPT, 'rb') as f:
            content = f.read()
        
        encoded_content = base64.b64encode(content).decode('ascii')
        print(f"📤 Uploading {LOCAL_SCRIPT.name} (Size: {len(content)} bytes) via Base64...")
        
        # 2. Upload via Shell Command (Base64 -> Decode)
        # Split into chunks just in case, but usually fine for 15KB
        remote_tmp = REMOTE_SCRIPT + ".tmp"
        
        # Create remote command
        upload_cmd = f"echo '{encoded_content}' | base64 -d > {remote_tmp} && mv {remote_tmp} {REMOTE_SCRIPT}"
        
        stdin, stdout, stderr = client.exec_command(upload_cmd)
        err = stderr.read().decode().strip()
        if err:
            print(f"⚠️ Upload Warning: {err}")
            
        print("✅ Upload complete.")
        
        # 3. Execute remote restart
        print("🔄 Restarting Rhythm Thinker on Linux...")
        commands = [
            f"python3 -m py_compile {REMOTE_SCRIPT} && echo 'Syntax OK'",
            "pkill -f rhythm_think.py || echo 'No running process found'",
            f"nohup python3 {REMOTE_SCRIPT} > /home/bino/agi/logs/rhythm_think.log 2>&1 &",
            "sleep 1",
            "ps aux | grep rhythm_think.py | grep -v grep"
        ]
        
        full_cmd = " && ".join(commands)
        stdin, stdout, stderr = client.exec_command(full_cmd)
        
        output = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        
        if output:
            print(f"📄 Output:\n{output}")
        if err:
            print(f"⚠️ Error:\n{err}")
            
        print("✨ Brain Update Finished.")
        
    except Exception as e:
        print(f"❌ Failed to update brain: {e}")
    finally:
        if client: client.close()


if __name__ == "__main__":
    update_brain()
