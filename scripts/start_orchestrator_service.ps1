#Requires -Version 5.1
<#
.SYNOPSIS
    Start the Full-Stack Orchestrator in the background as a long-running service.

.DESCRIPTION
    Wraps `python fdo_agi_repo/orchestrator/full_stack_orchestrator.py --mode run`
    and keeps track of the spawned process via a PID file inside `outputs/`.
    STDOUT/STDERR are redirected to `outputs/fullstack_stdout.log` and
    `outputs/fullstack_stderr.log`.

.PARAMETER Duration
    Optional run duration in seconds. Omit (or set to 0) to let the orchestrator
    run indefinitely until explicitly stopped.

.PARAMETER Force
    Stop an existing orchestrator process (if tracked) before launching a new one.

.PARAMETER PassThru
    Return the underlying Process object.
#>

param(
    [int]$Duration = 86400,
    [switch]$Force,
    [switch]$PassThru
)

$ErrorActionPreference = 'Stop'

$workspaceRoot = Split-Path -Parent $PSScriptRoot
$outputsDir = Join-Path $workspaceRoot 'outputs'
$pidFile = Join-Path $outputsDir 'fullstack_orchestrator.pid'
$stdoutLog = Join-Path $outputsDir 'fullstack_stdout.log'
$stderrLog = Join-Path $outputsDir 'fullstack_stderr.log'

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
        Write-Warning "Orchestrator already running (PID $($existing.Id)). Use -Force to restart."
        if ($PassThru) { return $existing }
        exit 0
    }

    Write-Host "Stopping existing orchestrator (PID $($existing.Id))..." -ForegroundColor Yellow
    Stop-Process -Id $existing.Id -Force
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

$python = (Get-Command python -ErrorAction Stop).Source
$effectiveDuration = if ($Duration -le 0) { 86400 } else { $Duration }
$arguments = @(
    'fdo_agi_repo/orchestrator/full_stack_orchestrator.py',
    '--mode', 'run',
    '--duration', $effectiveDuration.ToString()
)

Write-Host "Starting Full-Stack Orchestrator..." -ForegroundColor Cyan
$durationText = if ($Duration -le 0) { '86400 (default)' } else { $Duration }
Write-Host "  Duration (seconds): $durationText" -ForegroundColor Gray

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

if ($PassThru) {
    return $process
}