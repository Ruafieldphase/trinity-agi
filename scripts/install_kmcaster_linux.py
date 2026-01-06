import sys
from pathlib import Path
import paramiko
import time

# Add scripts directory to path to import credentials_manager
sys.path.insert(0, str(Path(__file__).parent))
from credentials_manager import get_linux_vm_credentials

def install_kmcaster():
    creds = get_linux_vm_credentials()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"Connecting to {creds['host']}...")
        client.connect(creds['host'], username=creds['user'], password=creds['password'])
        
        # 1. Install Java
        print("Installing Java (default-jre)...")
        cmd_install_java = f"echo {creds['password']} | sudo -S apt-get update && echo {creds['password']} | sudo -S apt-get install default-jre -y"
        stdin, stdout, stderr = client.exec_command(cmd_install_java, get_pty=True)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            print(f"❌ Java installation failed: {stdout.read().decode()}")
            return
        print("✅ Java installed.")

        # 2. Create tools directory
        print("Creating tools directory...")
        client.exec_command("mkdir -p /home/bino/agi/tools")

        # 3. Download KMCaster JAR
        print("Downloading kmcaster.jar...")
        jar_url = "https://github.com/flathub/com.whitemagicsoftware.kmcaster/releases/download/1.1.0/kmcaster.jar"
        cmd_download = f"wget -O /home/bino/agi/tools/kmcaster.jar {jar_url}"
        stdin, stdout, stderr = client.exec_command(cmd_download)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            print(f"❌ Download failed: {stderr.read().decode()}")
            return
        print("✅ kmcaster.jar downloaded.")

        # 4. Create launch script
        print("Creating launch script...")
        launch_script = """#!/bin/bash
java -jar /home/bino/agi/tools/kmcaster.jar &
"""
        cmd_create_script = f"echo '{launch_script}' > /home/bino/agi/run_kmcaster.sh && chmod +x /home/bino/agi/run_kmcaster.sh"
        client.exec_command(cmd_create_script)
        print("✅ run_kmcaster.sh created.")

        print("\n🎉 Installation Complete!")
        print("To run KMCaster, execute the following command in your Linux terminal:")
        print("./agi/run_kmcaster.sh")

    except Exception as e:
        print(f"Failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    install_kmcaster()
