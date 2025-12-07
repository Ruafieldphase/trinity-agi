"""
Install Claude CLI on Linux (User Mode)
"""
import paramiko

HOST = "192.168.119.128"
USER = "bino"
PASS = "0000"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(HOST, username=USER, password=PASS, timeout=5)
    print(f"✅ Connected to Linux Core")
    
    print("\n========== INSTALLING CLAUDE CLI (USER MODE) ==========")
    
    # Configure npm to use local prefix to avoid sudo
    cmds = [
        "mkdir -p ~/.npm-global",
        "npm config set prefix '~/.npm-global'",
        "echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc",
        "export PATH=~/.npm-global/bin:$PATH && npm install -g @anthropic-ai/claude-code"
    ]
    
    for cmd in cmds:
        print(f"🔧 Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if out: print(f"   {out[:200]}...")
        if err: print(f"   ⚠️ {err[:200]}...")
    
    # Verify
    print("\n🔍 Verifying installation...")
    stdin, stdout, stderr = client.exec_command("export PATH=~/.npm-global/bin:$PATH && claude --version")
    ver = stdout.read().decode().strip()
    
    if ver:
        print(f"✅ Claude CLI Installed: {ver}")
    else:
        print("❌ Installation failed")
    
    client.close()
    print("\n========== END ==========")
    
except Exception as e:
    print(f"❌ Error: {e}")
