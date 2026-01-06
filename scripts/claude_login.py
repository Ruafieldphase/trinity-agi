"""
Get Claude Login URL
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
    
    # Kill stuck processes
    client.exec_command("pkill -f claude")
    time.sleep(1)
    
    print("\n========== CLAUDE LOGIN ==========")
    print("Running 'claude login' to get auth URL...")
    
    # Run login command
    # We need to force TTY allocation or handle the interactive prompt
    # But usually it prints a URL.
    cmd = "export PATH=~/.npm-global/bin:$PATH && claude login"
    
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    
    # Read output for a few seconds
    start_time = time.time()
    while time.time() - start_time < 10:
        if stdout.channel.recv_ready():
            chunk = stdout.channel.recv(1024).decode()
            print(chunk, end="")
            if "https://anthropic.com/login" in chunk or "code=" in chunk:
                print("\n\n✅ URL FOUND! Please open the link above.")
                break
        time.sleep(0.1)
        
    client.close()
    print("\n========== END ==========")
    
except Exception as e:
    print(f"❌ Error: {e}")
