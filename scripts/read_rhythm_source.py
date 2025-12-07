"""
Read rhythm_think.py source
"""
import paramiko

HOST = "192.168.119.128"
USER = "bino"
PASS = "0000"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(HOST, username=USER, password=PASS, timeout=5)
    
    print("========== READING SOURCE ==========\n")
    
    stdin, stdout, stderr = client.exec_command("cat ~/agi/scripts/rhythm_think.py")
    code = stdout.read().decode().strip()
    
    if code:
        print(code[:2000]) # Print first 2000 chars to check structure
        print("\n... (truncated) ...\n")
        print(code[-500:]) # Print last 500 chars to check main block
    else:
        print("❌ File is empty or not found")
        
    client.close()
    print("\n========== END ==========")
    
except Exception as e:
    print(f"❌ Error: {e}")
