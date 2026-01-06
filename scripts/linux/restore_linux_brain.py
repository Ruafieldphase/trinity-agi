import paramiko
import os
import sys
import time
from pathlib import Path

# Add workspace to path for credentials
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
from credentials_manager import get_linux_vm_credentials

def restore_linux():
    creds = get_linux_vm_credentials()
    HOST = creds['host']
    USER = creds['user']
    PASS = creds['password']
    
    # Files to sync: (Local Path, Remote Path)
    # Note: Using absolute paths for local, relative to /home/bino/ for remote
    files_to_sync = [
        # 1. Hippocampus fix (Update)
        (WORKSPACE_ROOT / "hippocampus.py", "agi/fdo_agi_repo/copilot/hippocampus.py"),
        
        # 2. Alpha Background Self (Missing)
        (WORKSPACE_ROOT / "alpha_background_self.py", "agi/scripts/alpha_background_self.py"),
        
        # 3. Slack Interface (Mapped from chatgpt_slack_listener.py)
        (WORKSPACE_ROOT / "scripts" / "chatgpt_slack_listener.py", "agi/body/slack_interface.py"),
        
        # 4. Lymphatic System (Mapped from adaptive_glymphatic_system.py)
        (WORKSPACE_ROOT / "fdo_agi_repo" / "orchestrator" / "adaptive_glymphatic_system.py", "agi/body/lymphatic_system.py"),

        # 5. Missing Package Init
        (WORKSPACE_ROOT / "body_init.py", "agi/body/__init__.py"),

        # 6. Service Configuration Updates
        (WORKSPACE_ROOT / "scripts" / "linux" / "systemd" / "agi-background-self.service", ".config/systemd/user/agi-background-self.service"),
        (WORKSPACE_ROOT / "scripts" / "linux" / "systemd" / "agi-body.service", ".config/systemd/user/agi-body.service"),
    ]
    
    print(f"🚀 Starting Linux Brain Restoration on {HOST}...")
    print(f"DEBUG: WORKSPACE_ROOT={WORKSPACE_ROOT}")
    
    # Check local files existence
    for local_path, _ in files_to_sync:
        if not local_path.exists():
            print(f"❌ Local file missing: {local_path}")
        else:
            print(f"✅ Local file exists: {local_path}")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USER, password=PASS, timeout=10)
        sftp = client.open_sftp()
        
        # 1. Stop services to unlock files
        print("🛑 Stopping Linux AGI services...")
        client.exec_command("systemctl --user stop agi-rhythm agi-body agi-collaboration agi-background-self")
        time.sleep(2) # Give it a moment
        
        for local_path, remote_path in files_to_sync:
            print(f"📤 Syncing: {os.path.basename(local_path)} -> {remote_path}")
            
            # Ensure remote directory exists
            remote_dir = os.path.dirname(remote_path)
            if remote_dir:
                # Build directory tree
                parts = remote_dir.split('/')
                current = ""
                for part in parts:
                    if current:
                        current += "/" + part
                    else:
                        current = part
                    try:
                        sftp.mkdir(current)
                    except:
                        pass # Already exists or couldn't create
            
            # Try to remove if exists to break locks
            try:
                sftp.remove(f"/home/bino/{remote_path}")
            except:
                pass
            
            try:
                with open(local_path, "rb") as fl:
                    sftp.putfo(fl, f"/home/bino/{remote_path}")
                print(f"✅ Synced: {os.path.basename(local_path)}")
            except Exception as fe:
                print(f"❌ Failed to sync {os.path.basename(local_path)}: {fe}")
                raise fe
            
        # 2. Restart services
        print("🔄 Restarting Linux AGI services...")
        client.exec_command("systemctl --user daemon-reload")
        client.exec_command("systemctl --user start agi-rhythm")
        client.exec_command("systemctl --user start agi-body")
        client.exec_command("systemctl --user start agi-collaboration")
        client.exec_command("systemctl --user start agi-background-self")
        
        print("✅ Restoration sequence completed.")
        
        sftp.close()
        client.close()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    restore_linux()
