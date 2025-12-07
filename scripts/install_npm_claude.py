"""
Install npm and then Claude CLI
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
    
    print("\n========== INSTALLING NPM ==========")
    cmd = "echo 0000 | sudo -S apt-get install -y npm"
    print(f"🔧 Running: {cmd}")
    
    stdin, stdout, stderr = client.exec_command(cmd)
    # Wait for completion
    exit_status = stdout.channel.recv_exit_status()
    
    if exit_status == 0:
        print("✅ npm installed successfully")
    else:
        print("⚠️  npm install failed (might be already installed or lock issue)")
        print(stderr.read().decode())

    print("\n========== INSTALLING CLAUDE CLI ==========")
    # Now try installing Claude CLI again (User mode)
    cmds = [
        "mkdir -p ~/.npm-global",
        "npm config set prefix '~/.npm-global'",
        "export PATH=~/.npm-global/bin:$PATH && npm install -g @anthropic-ai/claude-code"
    ]
    
    for cmd in cmds:
        print(f"🔧 Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
             print(f"   ⚠️ Error: {stderr.read().decode()[:200]}")

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
