"""
Fetch full rhythm_think.log for diagnosis
"""
import paramiko

HOST = "192.168.119.128"
USER = "bino"
PASS = "0000"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(HOST, username=USER, password=PASS, timeout=5)
    
    print("========== FETCHING LOG ==========\n")
    
    stdin, stdout, stderr = client.exec_command("cat ~/agi/outputs/rhythm_think.log")
    log = stdout.read().decode().strip()
    
    if log:
        print(log)
    else:
        print("❌ Log is empty or not found")
        
    client.close()
    print("\n========== END ==========")
    
except Exception as e:
    print(f"❌ Error: {e}")
