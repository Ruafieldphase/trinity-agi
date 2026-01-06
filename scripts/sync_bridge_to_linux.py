import os
import sys
from pathlib import Path
from credentials_manager import CredentialsManager
import paramiko

def sync_bridge():
    # Paths
    WORKSPACE_ROOT = Path(__file__).parent.parent.absolute()
    sys.path.append(str(WORKSPACE_ROOT))
    
    local_path = WORKSPACE_ROOT / "scripts" / "background_self_bridge.py"
    remote_path = "/home/bino/agi/scripts/alpha_background_self.py"
    
    print(f"🌉 Syncing Bridge: {local_path} -> {remote_path}")
    
    # Get Credentials
    from credentials_manager import get_linux_vm_credentials
    creds = get_linux_vm_credentials()
    if not creds:
        print("❌ Could not find Linux VM credentials.")
        return

    host = creds.get("host")
    user = creds.get("user")
    pw = creds.get("password")

    try:
        # Create SSH Client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=pw)
        
        # SFTP Upload
        sftp = ssh.open_sftp()
        sftp.put(str(local_path), remote_path)
        sftp.close()
        print("✅ Upload successful.")
        
        # Restart Service (agi-collaboration or agi-rhythm might depend on it)
        # Assuming there is an agi-rhythm service that might need a restart or just ensure it's running
        print("🔄 Restarting agi-rhythm service on Linux...")
        ssh.exec_command("systemctl --user restart agi-rhythm")
        
        ssh.close()
        print("Done.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    sync_bridge()
