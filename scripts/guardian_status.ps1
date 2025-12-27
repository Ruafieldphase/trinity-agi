# Guardian Quick Status
# 빠른 상태 확인

$StateFile = "C:\workspace\agi\outputs\guardian_state.json"

if (Test-Path $StateFile) {
    $state = Get-Content $StateFile | ConvertFrom-Json

    $status = $state.status
    $heartbeat = $state.heartbeat_count
    $uptime = [math]::Round($state.uptime_seconds / 60, 1)
    $python = $state.health.python_count
    $agi = $state.health.agi_count
    $mem = [math]::Round($state.health.memory_percent, 1)
    $warnings = $state.warnings.Count
    $killed = $state.processes_killed

    Write-Host ""
    Write-Host "  Rhythm Guardian Status" -ForegroundColor Cyan
    Write-Host "  ----------------------" -ForegroundColor Cyan

    if ($status -eq "running") {
        Write-Host "  Status:    " -NoNewline; Write-Host "RUNNING" -ForegroundColor Green
    } else {
        Write-Host "  Status:    " -NoNewline; Write-Host $status.ToUpper() -ForegroundColor Red
    }

    Write-Host "  Heartbeat: $heartbeat"
    Write-Host "  Uptime:    ${uptime}m"
    Write-Host "  Python:    $python processes"
    Write-Host "  AGI:       $agi processes"
    Write-Host "  Memory:    ${mem}%"

    if ($warnings -gt 0) {
        Write-Host "  Warnings:  " -NoNewline; Write-Host "$warnings" -ForegroundColor Yellow
    } else {
        Write-Host "  Warnings:  0" -ForegroundColor Green
    }

    if ($killed -gt 0) {
        Write-Host "  Cleaned:   $killed processes" -ForegroundColor Yellow
    }

    Write-Host ""
} else {
    Write-Host ""
    Write-Host "  Guardian is NOT running" -ForegroundColor Red
    Write-Host "  Run: .\scripts\start_guardian.ps1" -ForegroundColor Gray
    Write-Host ""
}
