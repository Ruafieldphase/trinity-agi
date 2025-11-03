$scriptPath = 'C:\workspace\agi\scripts\collect_system_metrics.ps1'
$interval = 300

while ($true) {
    try {
        & $scriptPath
        Write-Host "[\09:40:32] Metrics collected" -ForegroundColor Green
    } catch {
        Write-Host "[\09:40:32] Error: $_" -ForegroundColor Red
    }
    Start-Sleep -Seconds $interval
}
