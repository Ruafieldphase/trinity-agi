"""
Kill the stuck claude process
"""
import paramiko

HOST = "192.168.119.128"
USER = "bino"
PASS = "0000"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(HOST, username=USER, password=PASS, timeout=5)
    
    # Kill claude processes
    stdin, stdout, stderr = client.exec_command("pkill -f claude")
    print("✅ Killed stuck Claude processes")
    
    client.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
