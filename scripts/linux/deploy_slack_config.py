import paramiko
import sys
import json
import io
import os
from pathlib import Path

# Add workspace to path for credentials
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
from credentials_manager import get_linux_vm_credentials

def deploy_slack_config():
    creds = get_linux_vm_credentials()
    HOST = creds['host']
    USER = creds['user']
    PASS = creds['password']
    
    # 1. Define Config - Load from environment variables
    config = {
        "SLACK_BOT_TOKEN": os.environ.get("SLACK_BOT_TOKEN", ""),
        "SLACK_APP_TOKEN": os.environ.get("SLACK_APP_TOKEN", "")
    }
    
    if not config["SLACK_BOT_TOKEN"] or not config["SLACK_APP_TOKEN"]:
        print("⚠️ Warning: SLACK_BOT_TOKEN or SLACK_APP_TOKEN not set in environment")
        return
    
    config_json = json.dumps(config, indent=2)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USER, password=PASS, timeout=10)
        sftp = client.open_sftp()
        
        # Ensure config dir exists
        try:
            sftp.mkdir("agi/config")
        except:
            pass
            
        # Write config
        with sftp.file("agi/config/slack_config.json", "w") as f:
            f.write(config_json)
        print("✅ slack_config.json deployed to VM.")
        
        # 2. Reset and Restart
        client.exec_command("systemctl --user reset-failed agi-body")
        client.exec_command("systemctl --user restart agi-body")
        print("🔄 agi-body service restart triggered.")
        
        sftp.close()
        client.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    deploy_slack_config()
