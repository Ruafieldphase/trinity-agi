Set WshShell = CreateObject("WScript.Shell")
' Run the Python script with pythonw (no window)
' 0 = Hide window
WshShell.Run "pythonw c:\workspace\agi\scripts\run_fractal_daemon.py", 0, False
