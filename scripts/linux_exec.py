import paramiko
import sys
import os

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from services.config import LINUX_HOST, LINUX_USER, LINUX_PASSWORD
except ImportError:
    LINUX_HOST = "192.168.119.128"
    LINUX_USER = "bino"
    LINUX_PASSWORD = "0000"

def exec_linux(command):
    print(f"Executing on {LINUX_HOST}: {command}")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(LINUX_HOST, username=LINUX_USER, password=LINUX_PASSWORD)
        stdin, stdout, stderr = ssh.exec_command(command)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if out: print(out)
        if err: print(f"Error: {err}")
        ssh.close()
        return out, err
    except Exception as e:
        print(f"Exception: {e}")
        return None, str(e)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        exec_linux(" ".join(sys.argv[1:]))
    else:
        exec_linux("ollama list")
