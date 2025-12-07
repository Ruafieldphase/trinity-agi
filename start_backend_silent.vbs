Set WshShell = CreateObject("WScript.Shell")

' Define paths
CurrentDir = "c:\workspace\agi\services"

' Function to run command hidden
Sub RunHidden(cmd)
    WshShell.Run "cmd /c cd /d " & CurrentDir & " && " & cmd, 0, False
End Sub

' Start Services
RunHidden "python consciousness_api.py"
WScript.Sleep 1000
RunHidden "python unconscious_stream.py"
WScript.Sleep 1000
RunHidden "python background_self_api.py"
WScript.Sleep 1000
RunHidden "python unified_aggregator.py"
WScript.Sleep 1000

' Start Resonance Learning System (Lymphatic)
CurrentDir = "c:\workspace\agi\body"
RunHidden "python lymphatic_system.py"
WScript.Sleep 1000

' Start Slack Interface (Body)
RunHidden "python slack_interface.py"
WScript.Sleep 1000

' Start Conscious Mind (Koa)
CurrentDir = "c:\workspace\agi\mind"
RunHidden "python koa_conscious.py"

' All services started silently - no confirmation needed
