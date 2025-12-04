#Requires -Version 5.1
<#
.SYNOPSIS
    24시간 모니터링 백그라운드 프로세스 종료.
#>

$ErrorActionPreference = 'Stop'

$workspaceRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $workspaceRoot 'outputs/fullstack_24h_monitoring.pid'

if (-not (Test-Path $pidFile)) {
    Write-Host "No monitoring PID file found." -ForegroundColor Yellow
    exit 0
}

$trackedPid = Get-Content $pidFile | Select-Object -First 1
if (-not $trackedPid -or $trackedPid -notmatch '^\d+$') {
    Write-Warning "PID file is invalid. Removing file."
    Remove-Item $pidFile -Force
    exit 1
}

try {
    $process = Get-Process -Id [int]$trackedPid -ErrorAction Stop
    Write-Host "Stopping monitoring process (PID $trackedPid)..." -ForegroundColor Yellow
    Stop-Process -Id $process.Id -Force
}
catch {
    Write-Warning "Process $trackedPid not found. Removing PID file."
}

Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
Write-Host "Done." -ForegroundColor Green
