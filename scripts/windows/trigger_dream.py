import subprocess
import os
import sys

# Configuration
VM_USER = "bino"
VM_IP = "192.168.119.128"
SSH_KEY = os.path.expandvars(r"$USERPROFILE\.ssh\id_agi")
REMOTE_SCRIPT = "~/agi/scripts/dream_cortex.py"

def trigger_remote_dream():
    print(f"🚀 Triggering Dream Cortex on {VM_USER}@{VM_IP}...")
    
    # Construct SSH command
    # Uses nohup to run in background even if SSH disconnects
    ssh_cmd = [
        "ssh",
        "-i", SSH_KEY,
        f"{VM_USER}@{VM_IP}",
        f"nohup python3 {REMOTE_SCRIPT} > /dev/null 2>&1 &"
    ]
    
    try:
        # Run SSH command
        subprocess.run(ssh_cmd, check=True)
        print("✅ Signal sent. The Unconscious is now dreaming.")
        print("   (Check outputs/dreams/ for reports later)")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to trigger dream: {e}")
    except FileNotFoundError:
        print("❌ SSH executable not found. Is OpenSSH Client installed?")

if __name__ == "__main__":
    trigger_remote_dream()
