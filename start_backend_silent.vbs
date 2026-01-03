Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' Define base paths
AgiDir = "c:\workspace\agi"
ServicesDir = AgiDir & "\services"
BodyDir = AgiDir & "\body"
MindDir = AgiDir & "\mind"
ScriptsDir = AgiDir & "\scripts"

' Set environment variables
WshShell.Environment("Process")("GOOGLE_CLOUD_PROJECT") = "naeda-genesis"
WshShell.Environment("Process")("GOOGLE_CLOUD_LOCATION") = "us-central1"

' Function to run command hidden
Sub RunHidden(workDir, cmd)
    WshShell.Run "cmd /c cd /d " & workDir & " && " & cmd, 0, False
End Sub

' ============================================
' Core Backend Services
' ============================================

' Start Consciousness API (port 8100)
RunHidden ServicesDir, "C:\Python313\python.exe -u consciousness_api.py > consciousness.log 2>&1"
WScript.Sleep 2000

' Start Unconscious Stream (port 8101)
RunHidden ServicesDir, "C:\Python313\python.exe -u unconscious_stream.py > unconscious.log 2>&1"
WScript.Sleep 2000

' Start Background Self API (port 8102)
RunHidden ServicesDir, "C:\Python313\python.exe -u background_self_api.py > background_self.log 2>&1"
WScript.Sleep 2000

' Start Unified Aggregator (port 8104)
RunHidden ServicesDir, "C:\Python313\python.exe -u unified_aggregator.py > unified_aggregator.log 2>&1"
WScript.Sleep 2000

' Start FSD Controller API (port 8105)
RunHidden ServicesDir, "C:\Python313\python.exe -u fsd_server.py > outputs\fsd_server.log 2>&1"
WScript.Sleep 2000

' Start Lua Flow Collector (daemon)
RunHidden ServicesDir, "C:\Python313\python.exe -u lua_flow_collector.py --daemon > outputs\lua_flow_collector.log 2>&1"
WScript.Sleep 1000

' ============================================
' Body Services
' ============================================

' Start Resonance Learning System (Lymphatic)
RunHidden BodyDir, "C:\Python313\python.exe -u lymphatic_system.py > lymphatic.log 2>&1"
WScript.Sleep 1000

' Start Slack Interface (Body)
RunHidden BodyDir, "C:\Python313\python.exe -u slack_interface.py > slack.log 2>&1"
WScript.Sleep 1000

' ============================================
' Mind Services
' ============================================

' Start Conscious Mind (Koa)
RunHidden MindDir, "C:\Python313\python.exe -u koa_conscious.py > koa.log 2>&1"
WScript.Sleep 2000

' ============================================
' Fractal & MCP Services
' ============================================

' Start Fractal MCP Server (port 50000)
RunHidden AgiDir, "C:\Python313\python.exe -u fdo_agi_repo/lumen_mcp_server.py --port 50000 --transport sse --path /mcp > outputs/mcp_server.log 2>&1"
WScript.Sleep 2000

' Start Fractal Daemon
RunHidden AgiDir, "powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File scripts/autonomous_goal_loop_daemon.ps1 > outputs/fractal_daemon.log 2>&1"
WScript.Sleep 2000

' ============================================
' Rhythm Services
' ============================================

' Start Rhythm Think Loop
RunHidden ScriptsDir, "C:\Python313\python.exe -u rhythm_think.py > rhythm_think.log 2>&1"
WScript.Sleep 1000

' Start Silent Heart (Shion)
RunHidden AgiDir, "powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File invoke_shion.ps1"
WScript.Sleep 2000

' Generate Context Anchor
RunHidden AgiDir, "C:\Python313\python.exe scripts/generate_context_anchor.py"

' All services started silently
