#Requires -Version 5.1
<#
.SYNOPSIS
    Stop the background Full-Stack Orchestrator service started via start_orchestrator_service.ps1.
#>

$ErrorActionPreference = 'Stop'

$workspaceRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $workspaceRoot 'outputs/fullstack_orchestrator.pid'

if (-not (Test-Path $pidFile)) {
    Write-Host "No PID file found. Orchestrator may not be running." -ForegroundColor Yellow
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
    Write-Host "Stopping orchestrator (PID $trackedPid)..." -ForegroundColor Yellow
    Stop-Process -Id $process.Id -Force
}
catch {
    Write-Warning "Process $trackedPid not found. Removing PID file."
}

Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
Write-Host "Done." -ForegroundColor Green
