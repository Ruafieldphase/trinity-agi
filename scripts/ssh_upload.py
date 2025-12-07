import paramiko
import sys
import os

def upload_file(local_path, remote_path, hostname, username, password):
    try:
        transport = paramiko.Transport((hostname, 22))
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        print(f"Uploading {local_path} to {remote_path}...")
        sftp.put(local_path, remote_path)
        print("Upload successful.")
        
        sftp.close()
        transport.close()
    except Exception as e:
        print(f"Error uploading file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python ssh_upload.py <local_path> <remote_path>")
        sys.exit(1)
        
    local_path = sys.argv[1]
    remote_path = sys.argv[2]
    
    # Hardcoded credentials for this session
    HOST = "192.168.119.128"
    USER = "bino"
    PASS = "0000"
    
    upload_file(local_path, remote_path, HOST, USER, PASS)
