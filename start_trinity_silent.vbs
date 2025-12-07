' Trinity AGI - Silent Auto-Start Script
' Starts all services without visible windows
' ============================================

Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' Base directory
BaseDir = "c:\workspace\agi"

' Log file for debugging
LogFile = BaseDir & "\logs\autostart.log"

' Create logs directory if not exists
If Not FSO.FolderExists(BaseDir & "\logs") Then
    FSO.CreateFolder(BaseDir & "\logs")
End If

' Function to log messages
Sub LogMsg(msg)
    Set f = FSO.OpenTextFile(LogFile, 8, True)
    f.WriteLine Now() & " - " & msg
    f.Close
End Sub

' Function to run command hidden
Sub RunHidden(workDir, cmd)
    On Error Resume Next
    WshShell.Run "cmd /c cd /d """ & workDir & """ && " & cmd, 0, False
    If Err.Number <> 0 Then
        LogMsg "ERROR: " & cmd & " - " & Err.Description
        Err.Clear
    Else
        LogMsg "Started: " & cmd
    End If
    On Error GoTo 0
End Sub

LogMsg "=== Trinity AGI Auto-Start Beginning ==="

' ====================================
' 1. Start Frontend (Next.js Dashboard)
' ====================================
LogMsg "Starting Frontend..."
RunHidden BaseDir & "\dashboard", "npm run dev"
WScript.Sleep 3000

' ====================================
' 2. Start Backend Services
' ====================================
LogMsg "Starting Backend Services..."

' Main aggregator (port 8104)
RunHidden BaseDir & "\services", "python unified_aggregator.py"
WScript.Sleep 2000

' Consciousness API
RunHidden BaseDir & "\services", "python consciousness_api.py"
WScript.Sleep 1000

' Unconscious Stream
RunHidden BaseDir & "\services", "python unconscious_stream.py"
WScript.Sleep 1000

' Background Self API
RunHidden BaseDir & "\services", "python background_self_api.py"
WScript.Sleep 1000

' ====================================
' 3. Optional: Body Layer Services
' ====================================
If FSO.FolderExists(BaseDir & "\body") Then
    LogMsg "Starting Body Layer..."
    RunHidden BaseDir & "\body", "python lymphatic_system.py"
    WScript.Sleep 1000
End If

LogMsg "=== Trinity AGI Auto-Start Complete ==="

' Cleanup
Set FSO = Nothing
Set WshShell = Nothing
