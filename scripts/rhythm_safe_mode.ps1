#Requires -Version 5.1
param(
    [switch]$Enable,
    [switch]$Disable
)

<#
.SYNOPSIS
  Toggle Rhythm Safe Mode to reduce background load during peak focus hours.

.DESCRIPTION
  -Enable: Stop high-frequency/background loops (observer telemetry, worker monitors, watchdog),
           stop YouTube live observer, enforce a single queue worker, stop canary loops.
  -Disable: Exit safe mode (no-op by default). Use VS Code tasks to selectively restart services.

.NOTES
  Intended to be idempotent and safe to re-run. Outputs a JSON summary.
#>

function Write-Info($msg) { Write-Host "[SafeMode] $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERR] $msg" -ForegroundColor Red }

if (-not $Enable -and -not $Disable) { $Enable = $true }
if ($Enable -and $Disable) { Write-Err "Use either -Enable or -Disable, not both."; exit 1 }

$ws = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
Set-Location $ws

$actions = @()

if ($Enable) {
    Write-Info "Entering Rhythm Safe Mode..."

    # 1) Stop Observer Telemetry
    $telemetryStop = Join-Path $ws 'scripts/stop_observer_telemetry.ps1'
    if (Test-Path -LiteralPath $telemetryStop) {
        & $telemetryStop | Out-Null
        $actions += @{ name = 'observer_telemetry'; action = 'stop'; result = 'ok' }
        Write-Ok "Observer telemetry stopped"
    }
    else {
        $actions += @{ name = 'observer_telemetry'; action = 'stop'; result = 'missing' }
        Write-Warn "stop_observer_telemetry.ps1 not found"
    }

    # 2) Stop Worker Monitors (daemon/foreground)
    foreach ($f in 'stop_worker_monitor_daemon.ps1', 'stop_worker_monitor_foreground.ps1', 'stop_worker_monitor.ps1') {
        $p = Join-Path $ws ("scripts/" + $f)
        if (Test-Path -LiteralPath $p) {
            & $p | Out-Null
            $actions += @{ name = 'worker_monitor'; action = 'stop'; file = $f; result = 'ok' }
        }
    }

    # 3) Stop Task Watchdog (mirror VS Code task logic)
    try {
        $procs = Get-Process -Name 'pwsh', 'powershell' -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like '*task_watchdog.py*' }
        if ($procs) {
            $procs | Stop-Process -Force -ErrorAction SilentlyContinue
            $actions += @{ name = 'task_watchdog'; action = 'stop'; count = $procs.Count; result = 'ok' }
            Write-Ok ("Task Watchdog stopped (" + $procs.Count + ")")
        }
        else {
            $actions += @{ name = 'task_watchdog'; action = 'stop'; result = 'not_running' }
        }
    }
    catch {
        $actions += @{ name = 'task_watchdog'; action = 'stop'; result = 'error'; error = $_.Exception.Message }
        Write-Warn "Failed to stop watchdog: $($_.Exception.Message)"
    }

    # 4) Stop YouTube Live Observer (if present)
    $ytStop = Join-Path $ws 'scripts/stop_youtube_live_observer.ps1'
    if (Test-Path -LiteralPath $ytStop) {
        & $ytStop | Out-Null
        $actions += @{ name = 'youtube_live_observer'; action = 'stop'; result = 'ok' }
        Write-Ok "YouTube live observer stopped"
    }
    else {
        $actions += @{ name = 'youtube_live_observer'; action = 'stop'; result = 'missing' }
    }

    # 5) Stop Canary Loops
    $stopCanary = Join-Path $ws 'LLM_Unified/ion-mentoring/scripts/start_monitor_loop.ps1'
    if (Test-Path -LiteralPath $stopCanary) {
        & $stopCanary -KillExisting -StopOnly | Out-Null
        $actions += @{ name = 'canary_loops'; action = 'stop'; result = 'ok' }
        Write-Ok "Canary loops stopped"
    }
    else {
        $actions += @{ name = 'canary_loops'; action = 'stop'; result = 'missing' }
    }

    # 6) Enforce Single Worker
    $ensureWorker = Join-Path $ws 'scripts/ensure_rpa_worker.ps1'
    if (Test-Path -LiteralPath $ensureWorker) {
        & $ensureWorker -EnforceSingle -MaxWorkers 1 | Out-Null
        $actions += @{ name = 'queue_worker'; action = 'enforce_single'; max = 1; result = 'ok' }
        Write-Ok "Queue worker enforced to single"
    }
    else {
        $actions += @{ name = 'queue_worker'; action = 'enforce_single'; result = 'missing' }
    }

    $mode = 'enabled'
}
elseif ($Disable) {
    Write-Info "Exiting Rhythm Safe Mode..."
    # No automatic restarts here to avoid heavy loops; guide user to VS Code tasks.
    $actions += @{ name = 'safe_mode'; action = 'disable'; result = 'no-op'; note = 'use VS Code tasks to restart services selectively' }
    $mode = 'disabled'
}

$out = [ordered]@{
    mode      = $mode
    timestamp = (Get-Date).ToString('s')
    workspace = $ws
    actions   = $actions
}

$json = $out | ConvertTo-Json -Depth 6
Write-Output $json