#!/usr/bin/env python3
"""
Create desktop shortcuts for Hey Sena
"""
import os
import sys
from pathlib import Path
import winshell
from win32com.client import Dispatch

sys.path.insert(0, str(Path(__file__).parent))
from workspace_utils import find_fdo_root

fdo_root = find_fdo_root(Path(__file__).parent)
desktop = winshell.desktop()

# Create Hey Sena Toggle shortcut
print("Creating shortcuts on desktop...")

try:
    # 1. Hey Sena (Toggle)
    path = os.path.join(desktop, "Hey Sena.lnk")
    target = fdo_root / "toggle_sena.bat"
    icon = (r"C:\Windows\System32\shell32.dll", 14)

    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(path)
    shortcut.Targetpath = str(target)
    shortcut.WorkingDirectory = str(fdo_root)
    shortcut.IconLocation = f"{icon[0]}, {icon[1]}"
    shortcut.Description = "Toggle Hey Sena Voice Assistant"
    shortcut.save()
    print(f"[OK] {path}")

except Exception as e:
    print(f"[ERROR] Toggle shortcut: {e}")

try:
    # 2. Start Hey Sena
    path = os.path.join(desktop, "Start Hey Sena.lnk")
    target = fdo_root / "start_sena.bat"
    icon = (r"C:\Windows\System32\shell32.dll", 166)

    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(path)
    shortcut.Targetpath = str(target)
    shortcut.WorkingDirectory = str(fdo_root)
    shortcut.IconLocation = f"{icon[0]}, {icon[1]}"
    shortcut.Description = "Start Hey Sena Voice Assistant"
    shortcut.save()
    print(f"[OK] {path}")

except Exception as e:
    print(f"[ERROR] Start shortcut: {e}")

try:
    # 3. Stop Hey Sena
    path = os.path.join(desktop, "Stop Hey Sena.lnk")
    target = fdo_root / "stop_sena.bat"
    icon = (r"C:\Windows\System32\shell32.dll", 131)

    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(path)
    shortcut.Targetpath = str(target)
    shortcut.WorkingDirectory = str(fdo_root)
    shortcut.IconLocation = f"{icon[0]}, {icon[1]}"
    shortcut.Description = "Stop Hey Sena Voice Assistant"
    shortcut.save()
    print(f"[OK] {path}")

except Exception as e:
    print(f"[ERROR] Stop shortcut: {e}")

print("\n" + "=" * 60)
print("Desktop shortcuts created!")
print("=" * 60)
print("\nYou can now use:")
print("  [Hey Sena]        - Toggle (On/Off)")
print("  [Start Hey Sena]  - Start only")
print("  [Stop Hey Sena]   - Stop only")
print("\nRecommended: Use 'Hey Sena' for quick toggle!")
