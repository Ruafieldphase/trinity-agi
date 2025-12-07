"""
Create Virtual Environment and Install Dependencies on Linux
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
    
    print("\n========== CREATING VIRTUAL ENVIRONMENT ==========")
    
    commands = [
        ("Checking for venv", "python3 -m venv --help > /dev/null 2>&1 && echo 'venv available' || echo 'venv missing'"),
        ("Creating venv in ~/agi/.venv", "cd ~/agi && python3 -m venv .venv"),
        ("Installing pip in venv", "cd ~/agi && .venv/bin/pip install --upgrade pip"),
        ("Installing requirements", "cd ~/agi && .venv/bin/pip install -r requirements.txt"),
    ]
    
    for desc, cmd in commands:
        print(f"\n🔧 {desc}...")
        print(f"   Command: {cmd}")
        
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        
        # Show output
        out = stdout.read().decode()
        err = stderr.read().decode()
        
        if out and len(out) < 500:
            print(f"   Output: {out.strip()}")
        elif out:
            print(f"   Output: {out[:500]}... (truncated)")
            
        if err and "error" in err.lower():
            print(f"   ⚠️  Stderr: {err[:200]}")
    
    print("\n✅ Virtual environment setup complete!")
    print("   Rhythm Think should now be able to run via:")
    print("   cd ~/agi && .venv/bin/python3 scripts/rhythm_think.py")
    
    client.close()
    print("\n========== END ==========")
    
except Exception as e:
    print(f"❌ Error: {e}")
