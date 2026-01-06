# Launch AGI daemons in hidden mode (no console windows)
# This script uses pythonw.exe to run Python scripts without console windows


. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot
$pythonw = "pythonw"
$scriptsPath = "$WorkspaceRoot\scripts"

Write-Host "Launching AGI daemons in hidden mode..."

# Launch Master Daemon Loop
Write-Host "Starting master_daemon_loop.py (hidden)..."
Start-Process -FilePath $pythonw -ArgumentList "$scriptsPath\master_daemon_loop.py" -WindowStyle Hidden -NoNewWindow

Start-Sleep -Seconds 2

# Launch Rhythm Think
Write-Host "Starting rhythm_think.py (hidden)..."
Start-Process -FilePath $pythonw -ArgumentList "$scriptsPath\rhythm_think.py" -WindowStyle Hidden -NoNewWindow

Start-Sleep -Seconds 2

# Launch Music Daemon
Write-Host "Starting music_daemon.py (hidden)..."
Start-Process -FilePath $pythonw -ArgumentList "$scriptsPath\music_daemon.py" -WindowStyle Hidden -NoNewWindow

Start-Sleep -Seconds 2

# Launch Human Ops Summary
Write-Host "Starting human_ops_summary.py (hidden)..."
Start-Process -FilePath $pythonw -ArgumentList "$scriptsPath\human_ops_summary.py" -WindowStyle Hidden -NoNewWindow

Write-Host ""
Write-Host "All daemons launched in hidden mode."
Write-Host "To check status: Get-Process python* | Where-Object {$_.CommandLine -like '*agi*'}"