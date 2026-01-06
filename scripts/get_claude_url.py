"""
Get Claude Login URL (Robust)
"""
import paramiko
import time
import re

HOST = "192.168.119.128"
USER = "bino"
PASS = "0000"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(HOST, username=USER, password=PASS, timeout=5)
    print(f"✅ Connected to Linux Core")
    
    # Kill stuck processes
    client.exec_command("pkill -f claude")
    time.sleep(1)
    
    print("\n========== CLAUDE LOGIN ==========")
    print("Running 'claude login'...")
    
    # Use script command to fake a TTY and capture output
    cmd = "export PATH=~/.npm-global/bin:$PATH && script -q -c 'claude login' /dev/null"
    
    stdin, stdout, stderr = client.exec_command(cmd)
    
    # Read output loop
    start_time = time.time()
    found_url = False
    
    while time.time() - start_time < 15:
        if stdout.channel.recv_ready():
            chunk = stdout.channel.recv(4096).decode('utf-8', errors='ignore')
            # Look for URL
            match = re.search(r'(https://anthropic\.com/login\S+)', chunk)
            if match:
                print("\n\n🚨🚨🚨 AUTHENTICATION REQUIRED 🚨🚨🚨")
                print("Please open this URL in your browser:")
                print(f"\n👉 {match.group(1)}\n")
                print("🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨")
                found_url = True
                break
            else:
                # Print chunk to see what's happening
                print(chunk, end="")
                
        time.sleep(0.1)
        
    if not found_url:
        print("\n❌ Could not find login URL in output.")
        
    client.close()
    print("\n========== END ==========")
    
except Exception as e:
    print(f"❌ Error: {e}")
