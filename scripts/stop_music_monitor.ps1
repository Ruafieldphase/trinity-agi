#Requires -Version 5.1
<#
.SYNOPSIS
    Stop realtime music monitor daemon

.DESCRIPTION
    Stops all running music monitor processes.

.EXAMPLE
    .\stop_music_monitor.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host "🛑 Stopping music monitors..." -ForegroundColor Yellow

$Processes = Get-Process -Name "pwsh", "powershell", "python" -ErrorAction SilentlyContinue |
Where-Object { $_.CommandLine -like "*realtime_music_analyzer.py*" }

if ($Processes) {
    $Processes | Stop-Process -Force
    Write-Host "✓ Stopped $($Processes.Count) monitor(s)" -ForegroundColor Green
}
else {
    Write-Host "ℹ️ No music monitor running" -ForegroundColor Cyan
}
