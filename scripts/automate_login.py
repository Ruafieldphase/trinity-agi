"""
Automate Claude Login with Expect
"""
import paramiko
import time

HOST = "192.168.119.128"
USER = "bino"
PASS = "0000"

expect_script = r'''#!/usr/bin/expect

set timeout 20
spawn bash -c "export PATH=~/.npm-global/bin:\$PATH && claude login"

# Handle Theme Selection
expect {
    "Dark mode" { send "\r"; exp_continue }
    "Light mode" { send "\r"; exp_continue }
    "Select a theme" { send "\r"; exp_continue }
    "https://anthropic.com/login" { 
        puts "\n\nFOUND_URL: $expect_out(0,string)\n"
        exit 0
    }
    timeout { puts "TIMEOUT waiting for prompt"; exit 1 }
}

# Handle other prompts if any
expect {
    "https://anthropic.com/login" { 
        puts "\n\nFOUND_URL: $expect_out(0,string)\n"
        exit 0
    }
    timeout { puts "TIMEOUT waiting for URL"; exit 1 }
}
'''

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(HOST, username=USER, password=PASS, timeout=5)
    print(f"✅ Connected to Linux Core")
    
    # Write expect script
    cmd = f"cat <<'EOF' > ~/agi/scripts/login_claude.exp\n{expect_script}\nEOF"
    client.exec_command(cmd)
    client.exec_command("chmod +x ~/agi/scripts/login_claude.exp")
    
    print("\n========== RUNNING EXPECT SCRIPT ==========")
    print("Waiting for URL...")
    
    stdin, stdout, stderr = client.exec_command("~/agi/scripts/login_claude.exp")
    
    out = stdout.read().decode()
    print(out)
    
    if "FOUND_URL" in out:
        print("\n✅ SUCCESS! URL Captured.")
    else:
        print("\n❌ Failed to capture URL.")
        print("Stderr:", stderr.read().decode())

    client.close()
    print("\n========== END ==========")
    
except Exception as e:
    print(f"❌ Error: {e}")
