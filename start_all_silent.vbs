Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c start_all.bat", 0, False
Set WshShell = Nothing
