"""
Debug numpy installation and install it directly
"""
import paramiko

HOST = "192.168.119.128"
USER = "bino"
PASS = "0000"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(HOST, username=USER, password=PASS, timeout=5)
    print(f"✅ Connected to Linux Core\n")
    
    commands = [
        ("Check Python version", "python3 --version"),
        ("Check pip version", "pip3 --version"),
        ("Check if numpy installed", "python3 -c 'import numpy; print(numpy.__version__)'"),
        ("Install numpy directly", "pip3 install numpy --break-system-packages --user"),
        ("Verify numpy again", "python3 -c 'import numpy; print(\"✅ NumPy\", numpy.__version__)'"),
    ]
    
    for desc, cmd in commands:
        print(f"🔧 {desc}...")
        print(f"   > {cmd}")
        
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        
        if out:
            print(f"   {out}\n")
        if err and ("error" in err.lower() or "traceback" in err.lower()):
            print(f"   ⚠️  {err[:300]}\n")
    
    client.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
