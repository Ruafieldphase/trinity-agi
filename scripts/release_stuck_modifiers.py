"""
Release stuck modifier keys (Shift/Ctrl/Alt/Win) on Windows.

Context:
- RPA/automation or app crashes can sometimes leave modifiers logically "down".
- This helper sends keyUp events for common modifiers to reset state.

Safe to run multiple times. If pyautogui is missing, it will print a hint and exit 1.
"""
from __future__ import annotations

import sys

try:
    import pyautogui
except Exception as e:
    sys.stderr.write("pyautogui is not installed or failed to import.\n")
    sys.stderr.write("Install with: pip install pyautogui\n")
    sys.exit(1)


def main() -> int:
    # Be conservative: release both generic and side-specific names
    modifiers = [
        "shift", "shiftleft", "shiftright",
        "ctrl", "ctrlleft", "ctrlright",
        "alt", "altleft", "altright",
        "win", "winleft", "winright",
    ]

    # Reduce accidental delays and disable failsafe to avoid corner abort
    try:
        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = False
    except Exception:
        pass

    released = []
    for key in modifiers:
        try:
            pyautogui.keyUp(key)
            released.append(key)
        except Exception:
            # Ignore unknown names on this platform
            pass

    print({"released": released})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
