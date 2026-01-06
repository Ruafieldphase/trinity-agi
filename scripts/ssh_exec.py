#!/usr/bin/env python3
"""
SSH Execute: Run command on Linux VM
"""
import sys
import paramiko
import argparse

HOST = "192.168.119.128"
USER = "bino"
PASS = "0000"

def main():
    parser = argparse.ArgumentParser(description="SSH Execute")
    parser.add_argument("command", help="Command to execute")
    parser.add_argument("--silent", action="store_true", help="Suppress connection logs")
    args = parser.parse_args()

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(HOST, username=USER, password=PASS, timeout=10)
        
        if not args.silent:
            print(f"🔌 Connected to {HOST}")
            print(f"▶️  Executing: {args.command}\n")
        
        stdin, stdout, stderr = client.exec_command(args.command, get_pty=True)
        
        # Read output in real-time
        for line in stdout:
            print(line, end='')
        
        # Check for errors
        err = stderr.read().decode()
        if err and not args.silent:
            print(f"\n⚠️  Errors:\n{err}")
        
        exit_status = stdout.channel.recv_exit_status()
        client.close()
        
        if not args.silent:
            print(f"\n✅ Exit code: {exit_status}")
        
        sys.exit(exit_status)
        
    except Exception as e:
        if not args.silent:
            print(f"❌ Error: {e}")
        else:
            print(str(e), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
