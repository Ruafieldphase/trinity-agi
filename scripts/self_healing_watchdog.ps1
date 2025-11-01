#Requires -Version 5.1
<#
.SYNOPSIS
    Self-Healing Watchdog - 모든 핵심 프로세스를 감시하고 자동으로 재시작
.DESCRIPTION
    5분마다 핵심 프로세스를 체크하고, 죽은 것을 자동으로 재시작합니다.
    - Task Queue Server (8091)
    - RPA Worker
    - Monitoring Daemon
    
    백그라운드에서 지속 실행되며, 로그를 outputs/watchdog_log.jsonl에 기록합니다.
#>

param(
    [int]$CheckInterval = 300,  # 5분
    [int]$ServerPort = 8091,
    [string]$LogFile = "$PSScriptRoot\..\outputs\watchdog_log.jsonl"
)

$ErrorActionPreference = "Continue"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

# Ensure log directory
$logDir = Split-Path -Parent $LogFile
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Write-WatchdogLog {
    param([string]$Action, [string]$Target, [string]$Status, [string]$Details = "")
    $entry = @{
        timestamp = (Get-Date).ToString("o")
        action    = $Action
        target    = $Target
        status    = $Status
        details   = $Details
    }
    $json = $entry | ConvertTo-Json -Compress
    Add-Content -Path $LogFile -Value $json -Encoding UTF8
}

function Test-ProcessRunning {
    param([string]$Pattern)
    $procs = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*$Pattern*" }
    return ($null -ne $procs -and $procs.Count -gt 0)
}

function Test-ServerHealth {
    param([string]$Url)
    try {
        $resp = Invoke-WebRequest -Uri $Url -TimeoutSec 3 -UseBasicParsing -ErrorAction SilentlyContinue
        return ($resp.StatusCode -eq 200)
    }
    catch {
        return $false
    }
}

function Restart-TaskQueueServer {
    Write-WatchdogLog -Action "restart" -Target "task_queue_server" -Status "attempting"
    try {
        & "$WorkspaceRoot\scripts\ensure_task_queue_server.ps1" -Port $ServerPort
        Start-Sleep -Seconds 5
        $healthy = Test-ServerHealth -Url "http://127.0.0.1:${ServerPort}/api/health"
        if ($healthy) {
            Write-WatchdogLog -Action "restart" -Target "task_queue_server" -Status "success"
            return $true
        }
        else {
            Write-WatchdogLog -Action "restart" -Target "task_queue_server" -Status "unhealthy"
            return $false
        }
    }
    catch {
        Write-WatchdogLog -Action "restart" -Target "task_queue_server" -Status "failed" -Details $_.Exception.Message
        return $false
    }
}

function Restart-RpaWorker {
    Write-WatchdogLog -Action "restart" -Target "rpa_worker" -Status "attempting"
    try {
        & "$WorkspaceRoot\scripts\ensure_rpa_worker.ps1" -EnforceSingle -MaxWorkers 1
        Start-Sleep -Seconds 3
        $running = Test-ProcessRunning "rpa_worker.py"
        if ($running) {
            Write-WatchdogLog -Action "restart" -Target "rpa_worker" -Status "success"
            return $true
        }
        else {
            Write-WatchdogLog -Action "restart" -Target "rpa_worker" -Status "failed"
            return $false
        }
    }
    catch {
        Write-WatchdogLog -Action "restart" -Target "rpa_worker" -Status "failed" -Details $_.Exception.Message
        return $false
    }
}

function Restart-MonitoringDaemon {
    Write-WatchdogLog -Action "restart" -Target "monitoring_daemon" -Status "attempting"
    try {
        $venvPython = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
        $daemonScript = "$WorkspaceRoot\fdo_agi_repo\monitoring\monitoring_daemon.py"
        
        if (Test-Path $venvPython) {
            Start-Process -FilePath $venvPython `
                -ArgumentList @($daemonScript, "--server", "http://127.0.0.1:${ServerPort}", "--interval", "5") `
                -WindowStyle Hidden `
                -WorkingDirectory "$WorkspaceRoot\fdo_agi_repo"
            Start-Sleep -Seconds 3
            $running = Test-ProcessRunning "monitoring_daemon.py"
            if ($running) {
                Write-WatchdogLog -Action "restart" -Target "monitoring_daemon" -Status "success"
                return $true
            }
            else {
                Write-WatchdogLog -Action "restart" -Target "monitoring_daemon" -Status "failed"
                return $false
            }
        }
        else {
            Write-WatchdogLog -Action "restart" -Target "monitoring_daemon" -Status "failed" -Details "venv not found"
            return $false
        }
    }
    catch {
        Write-WatchdogLog -Action "restart" -Target "monitoring_daemon" -Status "failed" -Details $_.Exception.Message
        return $false
    }
}

# Main watchdog loop
Write-WatchdogLog -Action "start" -Target "watchdog" -Status "running" -Details "CheckInterval=${CheckInterval}s"

while ($true) {
    # Check Task Queue Server
    $serverHealthy = Test-ServerHealth -Url "http://127.0.0.1:${ServerPort}/api/health"
    if (-not $serverHealthy) {
        Write-WatchdogLog -Action "check" -Target "task_queue_server" -Status "down"
        Restart-TaskQueueServer | Out-Null
    }
    
    # Check RPA Worker
    $workerRunning = Test-ProcessRunning "rpa_worker.py"
    if (-not $workerRunning) {
        Write-WatchdogLog -Action "check" -Target "rpa_worker" -Status "down"
        Restart-RpaWorker | Out-Null
    }
    
    # Check Monitoring Daemon
    $monitorRunning = Test-ProcessRunning "monitoring_daemon.py"
    if (-not $monitorRunning) {
        Write-WatchdogLog -Action "check" -Target "monitoring_daemon" -Status "down"
        Restart-MonitoringDaemon | Out-Null
    }
    
    # All checks passed
    Write-WatchdogLog -Action "check" -Target "all" -Status "ok"
    
    Start-Sleep -Seconds $CheckInterval
}
