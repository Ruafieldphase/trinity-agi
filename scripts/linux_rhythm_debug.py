import paramiko
import time
import base64

host = '192.168.119.128'
user = 'bino'
password = '0000'

# Read Windows file content
with open(r'c:\workspace\agi\scripts\rhythm_think.py', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Local file size: {len(content)} bytes")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=10)

# Upload via base64
encoded = base64.b64encode(content.encode()).decode()
stdin, stdout, stderr = client.exec_command(f'echo "{encoded}" | base64 -d > /home/bino/agi/scripts/rhythm_think.py')
time.sleep(2)

# Verify file size
stdin, stdout, stderr = client.exec_command('wc -c /home/bino/agi/scripts/rhythm_think.py')
print("Remote file size:", stdout.read().decode().strip())

# Syntax check
stdin, stdout, stderr = client.exec_command('/home/bino/venv/bin/python3 -m py_compile /home/bino/agi/scripts/rhythm_think.py 2>&1')
result = stdout.read().decode()
print("Syntax check:", result if result else "OK")

# Kill any existing rhythm process
stdin, stdout, stderr = client.exec_command('pkill -f rhythm_think.py 2>/dev/null; sleep 1')

# Start rhythm daemon
cmd = 'cd /home/bino/agi && nohup /home/bino/venv/bin/python3 scripts/rhythm_think.py >> logs/rhythm_think.log 2>&1 &'
stdin, stdout, stderr = client.exec_command(cmd)
time.sleep(3)

# Check if running
stdin, stdout, stderr = client.exec_command('pgrep -la python | grep rhythm')
print("Process running:", stdout.read().decode().strip() if stdout.read() else "checking...")

# Get process list more reliably
stdin, stdout, stderr = client.exec_command('ps aux | grep rhythm_think | grep -v grep')
print("PS check:", stdout.read().decode().strip())

client.close()
