"""
Install packages with --break-system-packages flag
(Quick solution for shared folder limitation)
"""
import paramiko

HOST = "192.168.119.128"
USER = "bino"
PASS = "0000"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(HOST, username=USER, password=PASS, timeout=5)
    print(f"✅ Connected to Linux Core")
    
    print("\n========== INSTALLING PACKAGES (SYSTEM-WIDE) ==========")
    print("⚠️  Using --break-system-packages due to venv restrictions")
    
    cmd = "cd ~/agi && pip3 install -r requirements.txt --break-system-packages"
    
    print(f"\n🔧 Running: {cmd}")
    print("   (This may take several minutes...)\n")
    
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    
    # Stream output line by line
    for line in stdout:
        print(line.strip())
    
    print("\n✅ Installation complete!")
    
    client.close()
    print("\n========== END ==========")
    
except Exception as e:
    print(f"❌ Error: {e}")
