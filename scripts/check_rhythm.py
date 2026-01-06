"""
Final Rhythm Status Check
"""
import paramiko

HOST = "192.168.119.128"
USER = "bino"
PASS = "0000"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(HOST, username=USER, password=PASS, timeout=5)
    
    print("========== 🎵 RHYTHM STATUS 🎵 ==========\n")
    
    # Check running process
    stdin, stdout, stderr = client.exec_command("ps aux | grep rhythm_think | grep -v grep")
    out = stdout.read().decode().strip()
    
    if out:
        print("✅ Rhythm Think Process: ALIVE!")
        print(f"   {out}\n")
    else:
        print("❌ Process not found\n")
    
    # Check latest log
    stdin, stdout, stderr = client.exec_command("tail -10 ~/agi/outputs/rhythm_think.log 2>/dev/null")
    log = stdout.read().decode().strip()
    
    if log:
        print("📝 Latest Log Output:")
        print(log)
    
    client.close()
    print("\n========== END ==========")
    
except Exception as e:
    print(f"❌ Error: {e}")
