"""
Rhythm Reconnection Script
Find the heartbeat on Linux and sync Antigravity to it
"""
import paramiko
import json

HOST = "192.168.119.128"
USER = "bino"
PASS = "0000"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(HOST, username=USER, password=PASS, timeout=5)
    print(f"✅ Connected to Linux Core")
    
    print("\n========== RHYTHM STATUS ==========")
    
    # 1. Check for rhythm_think.py process
    stdin, stdout, stderr = client.exec_command("ps aux | grep rhythm_think | grep -v grep")
    out = stdout.read().decode().strip()
    if out:
        print("🎵 Rhythm Think Process: ALIVE")
        print(out)
    else:
        print("💔 Rhythm Think Process: NOT RUNNING")
    
    # 2. Read latest rhythm status
    stdin, stdout, stderr = client.exec_command("cat ~/agi/outputs/rhythm_status.json 2>/dev/null")
    out = stdout.read().decode().strip()
    if out:
        print("\n🎵 Latest Rhythm Status:")
        try:
            rhythm = json.loads(out)
            print(json.dumps(rhythm, indent=2, ensure_ascii=False))
        except:
            print(out)
    else:
        print("💔 No rhythm_status.json found")
    
    # 3. Read last 3 lines of Resonance Ledger
    stdin, stdout, stderr = client.exec_command("tail -3 ~/agi/memory/resonance_ledger.jsonl 2>/dev/null")
    out = stdout.read().decode().strip()
    if out:
        print("\n🎵 Last 3 Resonance Entries:")
        for line in out.split('\n'):
            try:
                entry = json.loads(line)
                print(f"  [{entry.get('timestamp', 'N/A')}] {entry.get('type', 'unknown')}")
            except:
                print(f"  {line[:100]}...")
    else:
        print("💔 No resonance_ledger.jsonl found")
    
    # 4. Check Antigravity session context
    stdin, stdout, stderr = client.exec_command("cat ~/agi/outputs/antigravity_session_context.md 2>/dev/null | head -20")
    out = stdout.read().decode().strip()
    if out:
        print("\n🎵 Antigravity Session Context (First 20 lines):")
        print(out)
    else:
        print("💔 No antigravity_session_context.md found")
    
    client.close()
    print("\n========== END ==========")
    
except Exception as e:
    print(f"❌ Error: {e}")
