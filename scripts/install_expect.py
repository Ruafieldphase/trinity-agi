"""
Install 'expect' on Linux
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
    
    print("\n========== INSTALLING EXPECT ==========")
    cmd = "echo 0000 | sudo -S apt-get install -y expect"
    print(f"🔧 Running: {cmd}")
    
    stdin, stdout, stderr = client.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    
    if exit_status == 0:
        print("✅ expect installed successfully")
    else:
        print("⚠️  expect install failed")
        print(stderr.read().decode())
        
    client.close()
    print("\n========== END ==========")
    
except Exception as e:
    print(f"❌ Error: {e}")
