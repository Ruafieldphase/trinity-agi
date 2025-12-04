#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create Desktop Shortcuts for Hey Sena v4.1
"""
import os
import sys
from pathlib import Path

def create_desktop_shortcuts():
    """Create shortcuts on Windows desktop"""
    try:
        import winshell
        from win32com.client import Dispatch
    except ImportError:
        print("[ERROR] Missing dependencies!")
        print("Please install: pip install winshell pywin32")
        return False

    # Get desktop path
    desktop = winshell.desktop()
    print(f"[INFO] Desktop path: {desktop}")

    # Current directory
    current_dir = Path(__file__).parent.absolute()
    print(f"[INFO] Project path: {current_dir}")

    # Shortcuts to create
    shortcuts = [
        {
            "name": "Hey Sena v4.1 (Cached)",
            "target": str(current_dir / "start_sena_v4.1.bat"),
            "description": "Start Hey Sena v4.1 with performance caching",
            "icon": (r"C:\Windows\System32\shell32.dll", 166),  # Play icon
        },
        {
            "name": "Hey Sena v4 (LLM)",
            "target": str(current_dir / "start_sena_v4.bat"),
            "description": "Start Hey Sena v4 with LLM capabilities",
            "icon": (r"C:\Windows\System32\shell32.dll", 166),
        },
        {
            "name": "Toggle Hey Sena v4",
            "target": str(current_dir / "toggle_sena_v4.bat"),
            "description": "Toggle Hey Sena v4 on/off",
            "icon": (r"C:\Windows\System32\shell32.dll", 14),  # Speaker icon
        },
        {
            "name": "Stop Hey Sena",
            "target": str(current_dir / "stop_sena.bat"),
            "description": "Stop all Hey Sena instances",
            "icon": (r"C:\Windows\System32\shell32.dll", 240),  # Stop icon
        },
    ]

    created = 0

    for shortcut_info in shortcuts:
        try:
            shortcut_path = os.path.join(desktop, shortcut_info["name"] + ".lnk")

            # Create shortcut
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.TargetPath = shortcut_info["target"]
            shortcut.WorkingDirectory = str(current_dir)
            shortcut.Description = shortcut_info["description"]

            # Set icon
            if shortcut_info["icon"]:
                icon_path, icon_index = shortcut_info["icon"]
                shortcut.IconLocation = f"{icon_path},{icon_index}"

            shortcut.save()

            print(f"[OK] Created: {shortcut_info['name']}")
            created += 1

        except Exception as e:
            print(f"[FAIL] Failed to create '{shortcut_info['name']}': {e}")

    print(f"\n[DONE] Created {created}/{len(shortcuts)} shortcuts on desktop")
    return created == len(shortcuts)

def main():
    print("\n" + "=" * 60)
    print("Hey Sena v4.1 - Desktop Shortcuts Creator")
    print("=" * 60)
    print()

    success = create_desktop_shortcuts()

    if success:
        print("\n[SUCCESS] All shortcuts created successfully!")
        print("\nYou can now:")
        print("  - Double-click 'Hey Sena v4.1 (Cached)' to start v4.1")
        print("  - Double-click 'Hey Sena v4 (LLM)' to start v4")
        print("  - Double-click 'Toggle Hey Sena v4' to start/stop")
        print("  - Double-click 'Stop Hey Sena' to stop all versions")
    else:
        print("\n[WARNING] Some shortcuts failed to create.")
        print("Please check the errors above.")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
