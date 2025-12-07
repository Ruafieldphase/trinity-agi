import paramiko
import sys
import os

def deploy_file_content(local_path, remote_path, hostname, username, password):
    try:
        # Read local file content
        with open(local_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print(f"Read {len(content)} bytes from {local_path}")

        # Connect via SSH
        transport = paramiko.Transport((hostname, 22))
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        print(f"Writing content to {remote_path}...")
        
        # Write directly to remote file
        with sftp.open(remote_path, 'w') as remote_file:
            remote_file.write(content)
            
        print("Deployment successful.")
        
        sftp.close()
        transport.close()
    except Exception as e:
        print(f"Error deploying file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python ssh_deploy_direct.py <local_path> <remote_path>")
        sys.exit(1)
        
    local_path = sys.argv[1]
    remote_path = sys.argv[2]
    
    # Hardcoded credentials
    HOST = "192.168.119.128"
    USER = "bino"
    PASS = "0000"
    
    deploy_file_content(local_path, remote_path, HOST, USER, PASS)
