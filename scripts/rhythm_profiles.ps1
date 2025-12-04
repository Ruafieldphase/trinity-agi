#requires -Version 5.1
<#
.SYNOPSIS
  Toggle background services by daily rhythm: Focus (lean), Balanced, Collection (night).

.DESCRIPTION
  Starts/stops known background daemons and monitors to match the selected profile.
  - Focus: minimal background load for coding sessions
  - Balanced: default set (safe, light monitors)
  - Collection: heavier collectors for off-hours/night

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts/rhythm_profiles.ps1 -Profile Focus

.PARAMETER Profile
  One of: Focus | Balanced | Collection

.PARAMETER DryRun
  Show actions without executing.

.NOTES
  Idempotent: safe to re-run. Targets only specific processes by command line patterns.
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [ValidateSet('Focus', 'Balanced', 'Collection')]
    [string]$Profile = 'Balanced',

    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$ws = Split-Path -Parent $PSScriptRoot  # workspace root

function Write-Info($msg) { Write-Host "[rhythm] $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "[ OK ] $msg" -ForegroundColor Green }
function Write-Act($msg) { Write-Host "[ .. ] $msg" -ForegroundColor Yellow }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor DarkYellow }

function Invoke-IfNotDry([scriptblock]$action) {
    if ($DryRun) { return } else { & $action }
}

function Stop-ByPattern([string[]]$patterns) {
    $procs = Get-Process -Name 'python', 'pwsh', 'powershell' -ErrorAction SilentlyContinue | Where-Object {
        $cmd = $_.CommandLine
        if (-not $cmd) { return $false }
        foreach ($p in $patterns) { if ($cmd -like $p) { return $true } }
        return $false
    }
    if ($procs) {
        $procs | ForEach-Object {
            Write-Act "Stopping PID=$($_.Id) name=$($_.ProcessName)"
            Invoke-IfNotDry { Stop-Process -Id $_.Id -Force }
        }
    }
}

function Ensure-QueueServer() {
    Write-Act 'Ensuring Task Queue Server (8091)'
    $script = Join-Path $ws 'scripts/ensure_task_queue_server.ps1'
    if (Test-Path -LiteralPath $script) { Invoke-IfNotDry { & $script -Port 8091 } } else { Write-Warn 'ensure_task_queue_server.ps1 not found' }
}

function Ensure-SingleWorker() {
    Write-Act 'Ensuring single RPA worker'
    $script = Join-Path $ws 'scripts/ensure_rpa_worker.ps1'
    if (Test-Path -LiteralPath $script) { Invoke-IfNotDry { & $script -EnforceSingle -MaxWorkers 1 } } else { Write-Warn 'ensure_rpa_worker.ps1 not found' }
}

function Stop-AllWorkers() {
    Write-Act 'Stopping all RPA workers'
    $script = Join-Path $ws 'scripts/ensure_rpa_worker.ps1'
    if (Test-Path -LiteralPath $script) { Invoke-IfNotDry { & $script -KillAll } } else { Write-Warn 'ensure_rpa_worker.ps1 not found' }
}

function Start-Watchdog([int]$IntervalSec = 60) {
    Write-Act "Starting Task Watchdog (interval ${IntervalSec}s)"
    $venvPy = Join-Path $ws 'fdo_agi_repo/.venv/Scripts/python.exe'
    $py = if (Test-Path -LiteralPath $venvPy) { $venvPy } else { 'python' }
    $script = Join-Path $ws 'fdo_agi_repo/scripts/task_watchdog.py'
    if (!(Test-Path -LiteralPath $script)) { Write-Warn 'task_watchdog.py not found'; return }
    Invoke-IfNotDry { Start-Process -FilePath $py -ArgumentList @("`"$script`"", "--server", "http://127.0.0.1:8091", "--interval", $IntervalSec, "--auto-recover") -WindowStyle Hidden | Out-Null }
}

function Stop-Watchdog() {
    Write-Act 'Stopping Task Watchdog'
    Stop-ByPattern @('*task_watchdog.py*')
}

function Start-ObserverTelemetry([int]$IntervalSec = 5) {
    Write-Act "Starting Observer Telemetry (Interval=${IntervalSec}s)"
    $script = Join-Path $ws 'scripts/observe_desktop_telemetry.ps1'
    if (Test-Path -LiteralPath $script) { Invoke-IfNotDry { Start-Process -FilePath 'powershell' -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$script`"", '-IntervalSeconds', "$IntervalSec") -WindowStyle Hidden | Out-Null } }
    else { Write-Warn 'observe_desktop_telemetry.ps1 not found' }
}

function Stop-ObserverTelemetry() {
    Write-Act 'Stopping Observer Telemetry'
    $script = Join-Path $ws 'scripts/stop_observer_telemetry.ps1'
    if (Test-Path -LiteralPath $script) { Invoke-IfNotDry { & $script } } else { Stop-ByPattern @('*observe_desktop_telemetry.ps1*') }
}

function Stop-GoalDashboardWatch() {
    Write-Act 'Stopping Goal Dashboard (watch mode)'
    Stop-ByPattern @('*generate_autonomous_goal_dashboard.ps1* -Watch*')
}

function Start-MusicDaemon([int]$Interval = 60, [double]$Threshold = 0.3) {
    Write-Act "Starting Music Auto-Play Daemon (interval=${Interval}s, threshold=$Threshold)"
    $venvPy = Join-Path $ws 'fdo_agi_repo/.venv/Scripts/python.exe'
    $py = if (Test-Path -LiteralPath $venvPy) { $venvPy } else { 'python' }
    $script = Join-Path $ws 'scripts/music_daemon.py'
    if (Test-Path -LiteralPath $script) { Invoke-IfNotDry { Start-Process -FilePath $py -ArgumentList @("`"$script`"", "--interval", $Interval, "--threshold", $Threshold) -WindowStyle Hidden | Out-Null } } else { Write-Warn 'music_daemon.py not found' }
}

function Stop-MusicDaemon() {
    Write-Act 'Stopping Music Auto-Play Daemon'
    Stop-ByPattern @('*music_daemon.py*')
}

function Stop-CanaryLoops() {
    Write-Act 'Stopping monitoring canary loops'
    Stop-ByPattern @('*start_monitor_loop_with_probe.ps1*', '*start_monitor_loop.ps1*')
}

function Start-WorkerMonitor([int]$Interval = 5) {
    Write-Act "Starting Worker Monitor (daemon, ${Interval}s)"
    $script = Join-Path $ws 'scripts/start_worker_monitor_daemon.ps1'
    if (Test-Path -LiteralPath $script) { Invoke-IfNotDry { & $script -KillExisting -IntervalSeconds $Interval } } else { Write-Warn 'start_worker_monitor_daemon.ps1 not found' }
}

function Stop-WorkerMonitor() {
    Write-Act 'Stopping Worker Monitor (daemon)'
    $script = Join-Path $ws 'scripts/stop_worker_monitor_daemon.ps1'
    if (Test-Path -LiteralPath $script) { Invoke-IfNotDry { & $script } } else { Stop-ByPattern @('*worker_monitor_daemon.ps1*', '*worker_monitor_foreground.ps1*') }
}

Write-Info "Applying profile: $Profile  (DryRun=$DryRun)"

switch ($Profile) {
    'Focus' {
        # Minimal background load for coding
        Stop-ObserverTelemetry
        Stop-MusicDaemon
        Stop-GoalDashboardWatch
        Stop-CanaryLoops
        Stop-WorkerMonitor
        Stop-Watchdog   # restart with longer interval

        Ensure-QueueServer
        Ensure-SingleWorker
        Start-Watchdog -IntervalSec 120
        Write-Ok 'Focus profile applied.'
    }

    'Balanced' {
        # Light monitors, normal watchdog
        Ensure-QueueServer
        Ensure-SingleWorker
        Start-Watchdog -IntervalSec 60

        # Prefer telemetry off by default; user can enable if needed
        Stop-ObserverTelemetry
        Stop-MusicDaemon
        Start-WorkerMonitor -Interval 10
        Write-Ok 'Balanced profile applied.'
    }

    'Collection' {
        # Heavier collectors for off-hours/night
        Ensure-QueueServer
        Ensure-SingleWorker
        Start-Watchdog -IntervalSec 60

        Start-ObserverTelemetry -IntervalSec 5
        Start-WorkerMonitor -Interval 5
        # Music auto-play typically off at night; keep stopped to avoid noise
        Stop-MusicDaemon
        Write-Ok 'Collection profile applied.'
    }
}

Write-Info 'Done.'
