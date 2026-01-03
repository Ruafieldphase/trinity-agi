
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot
﻿$scriptPath = "$WorkspaceRoot\scripts\collect_system_metrics.ps1"
$interval = 300

while ($true) {
    try {
        & $scriptPath
        Write-Host "[\09:32:59] Metrics collected" -ForegroundColor Green
    } catch {
        Write-Host "[\09:32:59] Error: $_" -ForegroundColor Red
    }
    Start-Sleep -Seconds $interval
}