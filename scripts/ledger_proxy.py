#!/usr/bin/env python3
"""
Ledger Proxy for Linux VM

Provides read/write access to Resonance Ledger on Linux VM via SSH
Used by Dashboard API to access the real ledger
"""

import sys
import json
import paramiko
from typing import List, Dict, Any

# Linux VM Configuration
LINUX_VM = {
    'host': '192.168.119.128',
    'user': 'bino',
    'password': '0000',
    'ledger_path': '/home/bino/agi/memory/resonance_ledger.jsonl'
}


def read_ledger(limit: int = 50, source: str = None) -> List[Dict[str, Any]]:
    """Read messages from Linux VM's Resonance Ledger"""
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            LINUX_VM['host'],
            username=LINUX_VM['user'],
            password=LINUX_VM['password'],
            timeout=5
        )
        
        # Read ledger file
        stdin, stdout, stderr = client.exec_command(f"cat {LINUX_VM['ledger_path']}")
        content = stdout.read().decode('utf-8')
        client.close()
        
        # Parse JSONL
        lines = content.strip().split('\n')
        messages = []
        
        for line in lines:
            if not line:
                continue
            try:
                msg = json.loads(line)
                
                # Filter by source if specified
                if source and msg.get('source') != source:
                    continue
                    
                messages.append(msg)
            except json.JSONDecodeError:
                continue
        
        # Return latest N messages (reversed)
        return list(reversed(messages[-limit:]))
        
    except Exception as e:
        return {'error': str(e), 'success': False}


def append_ledger(entry: Dict[str, Any]) -> bool:
    """Append a message to Linux VM's Resonance Ledger"""
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            LINUX_VM['host'],
            username=LINUX_VM['user'],
            password=LINUX_VM['password'],
            timeout=5
        )
        
        # Create JSON line
        line = json.dumps(entry, ensure_ascii=False)
        
        # Escape for shell
        escaped_line = line.replace("'", "'\\''")
        
        # Append to ledger
        command = f"echo '{escaped_line}' >> {LINUX_VM['ledger_path']}"
        stdin, stdout, stderr = client.exec_command(command)
        
        # Check for errors
        exit_status = stdout.channel.recv_exit_status()
        client.close()
        
        return exit_status == 0
        
    except Exception as e:
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'No command specified'}))
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'read':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        source = sys.argv[3] if len(sys.argv) > 3 else None
        
        result = read_ledger(limit, source)
        print(json.dumps(result, ensure_ascii=False))
        
    elif command == 'append':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'No entry data'}))
            sys.exit(1)
        
        entry = json.loads(sys.argv[2])
        success = append_ledger(entry)
        print(json.dumps({'success': success}))
        
    else:
        print(json.dumps({'error': f'Unknown command: {command}'}))
        sys.exit(1)
