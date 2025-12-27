Set WshShell = CreateObject("WScript.Shell")

' Run the comprehensive backend silent startup script
WshShell.Run "wscript.exe ""c:\workspace\agi\start_backend_silent.vbs""", 0, False

Set WshShell = Nothing
