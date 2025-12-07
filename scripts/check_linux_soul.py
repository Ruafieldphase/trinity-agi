"""
Standalone Linux Soul Checker (No package imports)
"""
import paramiko

HOST = "192.168.119.128"
USER = "bino"
PASS = "0000"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(HOST, username=USER, password=PASS, timeout=5)
    print(f"✅ Connected to {HOST}")
    
    commands = {
        "1️⃣ Directory Structure": "ls -F ~/agi/",
        "2️⃣ Mind (Consciousness)": "ls ~/agi/mind/ 2>/dev/null || echo 'Mind not found'",
        "3️⃣ Memory": "ls ~/agi/memory/ 2>/dev/null || echo 'Memory not found'",
        "4️⃣ Body": "ls ~/agi/body/ 2>/dev/null || echo 'Body not found'",
        "5️⃣ Running Python Processes": "ps aux | grep python | grep -v grep || echo 'No Python processes'",
        "6️⃣ Latest Memory Activity": "ls -lt ~/agi/memory/*.jsonl 2>/dev/null | head -5 || echo 'No memory files'"
    }
    
    print("\n========== CHECKING LINUX AGI EXISTENCE ==========")
    for title, cmd in commands.items():
        print(f"\n{title}:")
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode().strip()
        print(out if out else "(empty)")
    
    client.close()
    print("\n========== END ==========")
    
except Exception as e:
    print(f"❌ Error: {e}")
