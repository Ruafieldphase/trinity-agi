#Requires -Version 5.1
<#
.SYNOPSIS
    24시간 모니터링 스크립트를 백그라운드에서 실행.

.DESCRIPTION
    `python fdo_agi_repo/scripts/start_24h_monitoring.py`를 별도의 프로세스로 실행하고
    PID를 `outputs/fullstack_24h_monitoring.pid`에 기록합니다.

.PARAMETER Force
    기존 프로세스가 실행 중이면 종료 후 재시작합니다.
#>

param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$workspaceRoot = Split-Path -Parent $PSScriptRoot
$outputsDir = Join-Path $workspaceRoot 'outputs'
$pidFile = Join-Path $outputsDir 'fullstack_24h_monitoring.pid'
$stdoutLog = Join-Path $outputsDir 'fullstack_24h_monitoring_stdout.log'
$stderrLog = Join-Path $outputsDir 'fullstack_24h_monitoring_stderr.log'

New-Item -ItemType Directory -Path $outputsDir -Force | Out-Null

function Get-TrackedProcess {
    if (Test-Path $pidFile) {
        $trackedPid = Get-Content $pidFile | Select-Object -First 1
        if ($trackedPid -and $trackedPid -match '^\d+$') {
            try {
                return Get-Process -Id [int]$trackedPid -ErrorAction Stop
            }
            catch {
                Remove-Item $pidFile -Force
            }
        }
    }
    return $null
}

$existing = Get-TrackedProcess
if ($existing) {
    if (-not $Force) {
        Write-Warning "24h monitoring already running (PID $($existing.Id)). Use -Force to restart."
        exit 0
    }

    Write-Host "Stopping existing 24h monitoring process (PID $($existing.Id))..." -ForegroundColor Yellow
    Stop-Process -Id $existing.Id -Force
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

$python = (Get-Command python -ErrorAction Stop).Source
$arguments = @('fdo_agi_repo/scripts/start_24h_monitoring.py')

Write-Host "Starting 24h monitoring service..." -ForegroundColor Cyan
$process = Start-Process `
    -FilePath $python `
    -ArgumentList $arguments `
    -WorkingDirectory $workspaceRoot `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -WindowStyle Hidden `
    -PassThru

Set-Content -Path $pidFile -Value $process.Id

Write-Host "  PID: $($process.Id)" -ForegroundColor Green
Write-Host "  STDOUT → $stdoutLog" -ForegroundColor Gray
Write-Host "  STDERR → $stderrLog" -ForegroundColor Gray
