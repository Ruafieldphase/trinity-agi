"""
Install Claude CLI on Linux
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
    
    print("\n========== INSTALLING CLAUDE CLI ==========")
    
    # Check Node.js again
    stdin, stdout, stderr = client.exec_command("node --version")
    node_ver = stdout.read().decode().strip()
    print(f"Node.js: {node_ver}")
    
    # Install Claude Code
    cmd = "echo 0000 | sudo -S npm install -g @anthropic-ai/claude-code"
    print(f"\n🔧 Running: {cmd}")
    print("   (This may take a minute...)")
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    
    if out: print(out)
    if err: print(f"⚠️  {err}")
    
    # Verify installation
    print("\n🔍 Verifying installation...")
    stdin, stdout, stderr = client.exec_command("claude --version")
    ver = stdout.read().decode().strip()
    
    if ver:
        print(f"✅ Claude CLI Installed: {ver}")
    else:
        print("❌ Installation failed or 'claude' not in PATH")
        # Check path
        stdin, stdout, stderr = client.exec_command("ls /usr/local/bin/claude")
        print(f"Path check: {stdout.read().decode().strip()}")
    
    client.close()
    print("\n========== END ==========")
    
except Exception as e:
    print(f"❌ Error: {e}")
