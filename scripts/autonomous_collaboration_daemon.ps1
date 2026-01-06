# Autonomous Collaboration Daemon Manager
# =======================================
# Runs Shion (and optionally simulated Sena) auto-responders as background services

param(
    [string]$Action = "start",      # start, stop, status, restart
    [int]$ShionInterval = 30,       # Shion polling interval in seconds
    [int]$SenaInterval = 15,        # Sena polling interval in seconds
    [switch]$EnableSenaSimulation   # start sena_auto_responder.py when set
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$LogFile = "$WorkspaceRoot\outputs\autonomous_collab_daemon.log"
$PidFile = "$WorkspaceRoot\outputs\autonomous_collab_daemon.pid"
$PythonExe = Join-Path $WorkspaceRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) { $PythonExe = "python.exe" }

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $LogFile -Value $logMessage
}

function Start-Daemon {
    Write-Log "Starting Autonomous Collaboration Daemon..."
    
    # Check if already running
    if (Test-Path $PidFile) {
        $pids = Get-Content $PidFile | ConvertFrom-Json
        $running = @()
        
        foreach ($pidEntry in $pids.PSObject.Properties) {
            if ($pidEntry.Name -eq 'started') { continue }
            if ($pidEntry.Value -and (Get-Process -Id $pidEntry.Value -ErrorAction SilentlyContinue)) {
                $running += $pidEntry.Name
            }
        }
        
        if ($running.Count -gt 0) {
            Write-Log "⚠️ Daemon already running: $($running -join ', ')"
            Write-Log "   Use 'stop' or 'restart' action"
            return
        }
    }
    
    # Start Shion Auto-Responder
    Write-Log "🚀 Starting Shion Auto-Responder (interval: ${ShionInterval}s)..."
    $shionProc = Start-Process -FilePath $PythonExe `
        -ArgumentList "scripts\shion_auto_responder.py", "--daemon", "--interval", $ShionInterval `
        -WorkingDirectory $WorkspaceRoot `
        -WindowStyle Hidden `
        -PassThru
    
    if ($shionProc) {
        Write-Log "   ✅ Shion PID: $($shionProc.Id)"
    }
    else {
        Write-Log "   ❌ Failed to start Shion Auto-Responder"
    }
    
    Start-Sleep -Seconds 2
    
    # Start Sena Auto-Responder (simulation, optional)
    $senaProc = $null
    if ($EnableSenaSimulation.IsPresent) {
        Write-Log "🚀 Starting Sena Auto-Responder (simulation, interval: ${SenaInterval}s)..."
        $senaProc = Start-Process -FilePath $PythonExe `
            -ArgumentList "scripts\sena_auto_responder.py", "--daemon", "--interval", $SenaInterval `
            -WorkingDirectory $WorkspaceRoot `
            -WindowStyle Hidden `
            -PassThru
        
        if ($senaProc) {
            Write-Log "   ✅ Sena (simulated) PID: $($senaProc.Id)"
        }
        else {
            Write-Log "   ❌ Failed to start Sena Auto-Responder (simulation)"
        }
    }
    else {
        Write-Log "Sena Auto-Responder (simulation) is disabled. Use -EnableSenaSimulation to start it."
    }
    
    # Save PIDs (allow sena to be null)
    $pidData = @{
        shion   = if ($shionProc) { $shionProc.Id } else { $null }
        sena    = if ($senaProc) { $senaProc.Id } else { $null }
        started = (Get-Date).ToString("o")
    }
    $pidData | ConvertTo-Json | Set-Content -Path $PidFile
    
    Write-Log "✅ Autonomous Collaboration Daemon started"
    if ($shionProc) {
        Write-Log "   Shion PID: $($shionProc.Id)"
    }
    if ($senaProc) {
        Write-Log "   Sena (simulated) PID: $($senaProc.Id)"
    }
    Write-Log "   Log: $LogFile"
}

function Stop-Daemon {
    Write-Log "Stopping Autonomous Collaboration Daemon..."
    
    if (-not (Test-Path $PidFile)) {
        Write-Log "⚠️ No PID file found. Daemon may not be running."
        return
    }
    
    $pids = Get-Content $PidFile | ConvertFrom-Json

    foreach ($pidEntry in $pids.PSObject.Properties) {
        if ($pidEntry.Name -eq 'started') { continue }
        if (-not $pidEntry.Value) { continue }

        $proc = Get-Process -Id $pidEntry.Value -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Log "Stopping $($pidEntry.Name) responder (PID: $($pidEntry.Value))..."
            try {
                Stop-Process -Id $pidEntry.Value -Force -ErrorAction Stop
                Write-Log "   ✅ Stopped $($pidEntry.Name) responder"
            }
            catch {
                Write-Log "   ❌ Failed to stop $($pidEntry.Name) responder: $_"
            }
        }
        else {
            Write-Log "   ℹ️ $($pidEntry.Name) responder (PID: $($pidEntry.Value)) is not running"
        }
    }

    Remove-Item $PidFile -ErrorAction SilentlyContinue
    Write-Log "✅ Autonomous Collaboration Daemon stopped"
}

function Get-DaemonStatus {
    Write-Host "=" * 60
    Write-Host "Autonomous Collaboration Daemon Status"
    Write-Host "=" * 60

    if (-not (Test-Path $PidFile)) {
        Write-Host "Status: NOT RUNNING"
        Write-Host ""
        return
    }

    $pids = Get-Content $PidFile | ConvertFrom-Json
    $started = $pids.started

    Write-Host "Started: $started"
    Write-Host ""

    $allRunning = $true

    foreach ($pidEntry in $pids.PSObject.Properties) {
        if ($pidEntry.Name -eq 'started') { continue }
        if (-not $pidEntry.Value) { continue }

        $proc = Get-Process -Id $pidEntry.Value -ErrorAction SilentlyContinue
        if ($proc) {
            $cpu = [math]::Round($proc.CPU, 2)
            $mem = [math]::Round($proc.WorkingSet64 / 1MB, 1)
            Write-Host "✅ $($pidEntry.Name.ToUpper()) Responder"
            Write-Host "   PID: $($pidEntry.Value)"
            Write-Host "   CPU: ${cpu}s"
            Write-Host "   Memory: ${mem} MB"
            Write-Host ""
        }
        else {
            Write-Host "❌ $($pidEntry.Name.ToUpper()) Responder"
            Write-Host "   PID: $($pidEntry.Value) (NOT RUNNING)"
            Write-Host ""
            $allRunning = $false
        }
    }

    if ($allRunning) {
        Write-Host "Overall Status: ✅ RUNNING"
    }
    else {
        Write-Host "Overall Status: ⚠️ PARTIAL / STOPPED"
    }
    Write-Host "=" * 60
}

function Restart-Daemon {
    Write-Log "Restarting Autonomous Collaboration Daemon..."
    Stop-Daemon
    Start-Sleep -Seconds 2
    Start-Daemon
}

# Main execution
switch ($Action.ToLower()) {
    "start" {
        Start-Daemon
    }
    "stop" {
        Stop-Daemon
    }
    "status" {
        Get-DaemonStatus
    }
    "restart" {
        Restart-Daemon
    }
    default {
        Write-Host "Usage: .\autonomous_collaboration_daemon.ps1 -Action [start|stop|status|restart]"
        Write-Host ""
        Write-Host "Options:"
        Write-Host "  -ShionInterval <seconds>        Shion polling interval (default: 30)"
        Write-Host "  -SenaInterval <seconds>         Sena polling interval (default: 15)"
        Write-Host "  -EnableSenaSimulation           Start sena_auto_responder (simulation only)"
    }
}