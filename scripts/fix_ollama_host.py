import paramiko
import sys
import os

LINUX_HOST = "192.168.119.128"
LINUX_USER = "bino"
LINUX_PASSWORD = "0000"

def fix_ollama_host():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(LINUX_HOST, username=LINUX_USER, password=LINUX_PASSWORD)
        
        commands = [
            "sudo mkdir -p /etc/systemd/system/ollama.service.d",
            "sudo bash -c 'echo \"[Service]\" > /etc/systemd/system/ollama.service.d/override.conf'",
            "sudo bash -c 'echo \"Environment=\\\"OLLAMA_HOST=0.0.0.0\\\"\" >> /etc/systemd/system/ollama.service.d/override.conf'",
            "sudo systemctl daemon-reload",
            "sudo systemctl restart ollama"
        ]
        
        for cmd in commands:
            print(f"Exec: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            # Use stdin to provide password if needed, but bino is likely in sudoers with NOPASSWD or we need it
            # Let's assume NOPASSWD for now since it worked before
            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
            if out: print(f"Out: {out}")
            if err: print(f"Err: {err}")
            
        ssh.close()
        print("Done.")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    fix_ollama_host()
