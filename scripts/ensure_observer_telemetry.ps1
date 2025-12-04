#requires -Version 5.1
<#
.SYNOPSIS
    Ensure stream observer telemetry is running (auto-restart if needed).
.DESCRIPTION
    Checks if observe_desktop_telemetry.ps1 is running via PID file.
    If not running or stale, starts a new background instance.
    Safe to run repeatedly (idempotent).
.PARAMETER IntervalSeconds
    Polling interval for telemetry (default: 5)
.PARAMETER Force
    Kill existing process and force restart
.EXAMPLE
    .\scripts\ensure_observer_telemetry.ps1
    .\scripts\ensure_observer_telemetry.ps1 -Force
#>
param(
    [int]$IntervalSeconds = 5,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$workspaceRoot = Split-Path -Parent $PSScriptRoot
$telemetryDir = Join-Path $workspaceRoot 'outputs\telemetry'
$pidFile = Join-Path $telemetryDir 'observer_telemetry.pid'
$observerScript = Join-Path $PSScriptRoot 'observe_desktop_telemetry.ps1'

# Ensure telemetry directory exists
if (-not (Test-Path -LiteralPath $telemetryDir)) {
    New-Item -ItemType Directory -Path $telemetryDir -Force | Out-Null
}

function Get-ObserverPID {
    if (-not (Test-Path -LiteralPath $pidFile)) { return $null }
    $content = Get-Content -LiteralPath $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    [int]$procId = 0
    if ([int]::TryParse($content, [ref]$procId)) { return $procId }
    return $null
}

function Test-ProcessRunning([int]$procId) {
    if ($procId -le 0) { return $false }
    try {
        $proc = Get-Process -Id $procId -ErrorAction Stop
        return ($null -ne $proc)
    }
    catch { return $false }
}

function Stop-ObserverProcess {
    $procId = Get-ObserverPID
    if ($null -eq $procId) { return }
    if (Test-ProcessRunning $procId) {
        Write-Host "🛑 Stopping existing observer (PID: $procId)" -ForegroundColor Yellow
        try {
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500
        }
        catch {
            Write-Host "   Warning: Failed to stop PID $procId" -ForegroundColor DarkYellow
        }
    }
    # Clean up stale PID file
    if (Test-Path -LiteralPath $pidFile) {
        Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
    }
}

function Start-ObserverBackground {
    Write-Host "🚀 Starting observer telemetry (interval: ${IntervalSeconds}s)" -ForegroundColor Green
    $job = Start-Job -ScriptBlock {
        param($script, $interval)
        & powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File $script -IntervalSeconds $interval
    } -ArgumentList $observerScript, $IntervalSeconds
    
    # Wait briefly to check if job starts successfully
    Start-Sleep -Milliseconds 1000
    $state = (Get-Job -Id $job.Id).State
    
    if ($state -eq 'Running') {
        Write-Host "   ✅ Observer started successfully (Job ID: $($job.Id))" -ForegroundColor Green
        return $true
    }
    else {
        Write-Host "   ❌ Observer failed to start (State: $state)" -ForegroundColor Red
        $output = Receive-Job -Id $job.Id -ErrorAction SilentlyContinue
        if ($output) {
            Write-Host "   Output: $output" -ForegroundColor DarkRed
        }
        Remove-Job -Id $job.Id -Force -ErrorAction SilentlyContinue
        return $false
    }
}

# Main logic
Write-Host "📊 Observer Telemetry Manager" -ForegroundColor Cyan
Write-Host "   Script: $observerScript" -ForegroundColor DarkGray
Write-Host "   PID File: $pidFile" -ForegroundColor DarkGray

if ($Force) {
    Write-Host "🔄 Force restart requested" -ForegroundColor Yellow
    Stop-ObserverProcess
    Start-ObserverBackground
    exit 0
}

$procId = Get-ObserverPID
if ($null -eq $procId) {
    Write-Host "ℹ️  No PID file found - starting new observer" -ForegroundColor Cyan
    Start-ObserverBackground
    exit 0
}

if (Test-ProcessRunning $procId) {
    Write-Host "✅ Observer already running (PID: $procId)" -ForegroundColor Green
    # Verify it's actually writing data
    $latestLog = Get-ChildItem -Path $telemetryDir -Filter 'stream_observer_*.jsonl' -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
    
    if ($latestLog -and ((Get-Date) - $latestLog.LastWriteTime).TotalMinutes -lt 5) {
        $ageMin = [math]::Round(((Get-Date) - $latestLog.LastWriteTime).TotalMinutes, 1)
        Write-Host "   📝 Latest log: $($latestLog.Name) (${ageMin}m ago)" -ForegroundColor DarkGreen
        Write-Host "   Status: HEALTHY ✓" -ForegroundColor Green
    }
    else {
        Write-Host "   ⚠️  Warning: No recent telemetry data (process may be stalled)" -ForegroundColor Yellow
        Write-Host "   Consider using -Force to restart" -ForegroundColor Yellow
    }
    exit 0
}
else {
    Write-Host "⚠️  Stale PID file detected (process not running)" -ForegroundColor Yellow
    Stop-ObserverProcess
    Start-ObserverBackground
    exit 0
}
