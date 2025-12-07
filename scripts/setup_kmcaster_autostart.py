#!/usr/bin/env python3
"""
Setup KMCaster to auto-start on Linux boot
"""
import sys
from pathlib import Path
import paramiko

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))
from credentials_manager import get_linux_vm_credentials

def setup_autostart():
    creds = get_linux_vm_credentials()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"Connecting to {creds['host']}...")
        client.connect(creds['host'], username=creds['user'], password=creds['password'])
        
        # Create autostart directory if it doesn't exist
        print("Creating autostart directory...")
        client.exec_command("mkdir -p ~/.config/autostart")
        
        # Create .desktop file for autostart
        desktop_file_content = """[Desktop Entry]
Type=Application
Name=KMCaster
Comment=Keyboard and Mouse Event Visualizer
Exec=/usr/bin/java -jar /home/bino/agi/tools/kmcaster.jar
Terminal=false
Hidden=false
X-GNOME-Autostart-enabled=true
"""
        
        print("Creating kmcaster.desktop file...")
        cmd = f"cat > ~/.config/autostart/kmcaster.desktop << 'EOF'\n{desktop_file_content}\nEOF"
        stdin, stdout, stderr = client.exec_command(cmd)
        stdout.channel.recv_exit_status()
        
        # Make it executable
        client.exec_command("chmod +x ~/.config/autostart/kmcaster.desktop")
        
        print("✅ KMCaster autostart setup complete!")
        print("\nKMCaster will now start automatically when you log in to Linux.")
        
        # Check for config file location
        print("\n🔍 Checking KMCaster config location...")
        stdin, stdout, stderr = client.exec_command("find ~/ -name '*kmcaster*' -o -name '.kmcaster*' 2>/dev/null | head -20")
        config_files = stdout.read().decode().strip()
        
        if config_files:
            print("\n📁 KMCaster related files found:")
            print(config_files)
        else:
            print("\n⚠️ No config files found yet. They will be created after you run KMCaster for the first time.")
            print("Config files are typically stored in ~/.config/kmcaster/ or ~/.kmcaster/")
        
        print("\n💡 KMCaster Settings:")
        print("Once KMCaster is running, right-click on its window to access settings.")
        print("You can adjust:")
        print("  - Display position")
        print("  - Size and opacity")
        print("  - Colors and themes")
        print("  - Which keys/mouse buttons to show")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    setup_autostart()
