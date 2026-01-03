
import paramiko
import os
import sys

# Add scripts to path to find credentials_manager
sys.path.append("c:/workspace/agi/scripts")
from credentials_manager import get_linux_vm_credentials

def clear_and_restart():
    creds = get_linux_vm_credentials()
    host = creds['host']
    user = creds['user']
    password = creds['password']

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)

    print("--- Stopping Service ---")
    ssh.exec_command("systemctl --user stop agi-rhythm")
    
    print("--- Clearing Error Log ---")
    ssh.exec_command("> /home/bino/agi/logs/rhythm.error.log")

    print("--- Starting Service ---")
    ssh.exec_command("systemctl --user start agi-rhythm")

    import time
    time.sleep(2) # Wait for a cycle to run or fail

    print("--- Latest Error entries (rhythm.error.log) ---")
    stdin, stdout, stderr = ssh.exec_command("cat /home/bino/agi/logs/rhythm.error.log")
    print(stdout.read().decode())

    ssh.close()

if __name__ == "__main__":
    clear_and_restart()
