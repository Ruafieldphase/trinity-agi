"""
Install Python Dependencies on Linux VM
"""
import paramiko
import time

HOST = "192.168.119.128"
USER = "bino"
PASS = "0000"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(HOST, username=USER, password=PASS, timeout=5)
    print(f"✅ Connected to Linux Core")
    
    print("\n========== INSTALLING PYTHON DEPENDENCIES ==========")
    
    # Check if requirements.txt exists
    stdin, stdout, stderr = client.exec_command("ls ~/agi/requirements.txt")
    out = stdout.read().decode().strip()
    
    if "No such file" in out or not out:
        print("⚠️  No requirements.txt found. Installing critical packages manually...")
        packages = ["numpy", "google-generativeai", "slack_bolt", "paramiko", "python-dotenv", "sentence-transformers"]
    else:
        print(f"✅ Found requirements.txt")
        packages = None
    
    # Install packages
    if packages:
        cmd = f"pip3 install {' '.join(packages)}"
    else:
        cmd = "cd ~/agi && pip3 install -r requirements.txt"
    
    print(f"\n🔧 Running: {cmd}")
    print("   (This may take a few minutes...)")
    
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    
    # Stream output
    while True:
        line = stdout.readline()
        if not line:
            break
        print(line.strip())
    
    print("\n✅ Installation complete!")
    
    client.close()
    print("\n========== END ==========")
    
except Exception as e:
    print(f"❌ Error: {e}")
