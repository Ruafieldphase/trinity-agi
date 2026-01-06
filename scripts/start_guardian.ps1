
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot
$Action = "Start-Process"
$ScriptPath = "$WorkspaceRoot\scripts\rhythm_guardian.py"
$PythonPath = "pythonw.exe"

Write-Host "🛡️ Invoking Rhythm Guardian..."
Start-Process -FilePath $PythonPath -ArgumentList "-u $ScriptPath" -WindowStyle Hidden
Write-Host "✅ Guardian invoked in background."