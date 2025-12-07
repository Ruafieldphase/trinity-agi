#!/usr/bin/env python3
"""
SCP Execute: Transfer files to Linux VM using Paramiko
"""
import sys
import paramiko
import os

HOST = "192.168.119.128"
USER = "bino"
PASS = "0000"

if len(sys.argv) < 3:
    print("Usage: python scp_exec.py <local_path> <remote_path>")
    sys.exit(1)

local_path = sys.argv[1]
remote_path = sys.argv[2]

try:
    print(f"🔌 Connecting to {HOST}...")
    transport = paramiko.Transport((HOST, 22))
    transport.connect(username=USER, password=PASS)
    sftp = paramiko.SFTPClient.from_transport(transport)
    
    print(f"📤 Uploading {local_path} -> {remote_path}")
    sftp.put(local_path, remote_path)
    
    sftp.close()
    transport.close()
    print("✅ Transfer complete")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
