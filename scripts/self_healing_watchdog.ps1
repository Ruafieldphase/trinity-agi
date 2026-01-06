#Requires -Version 5.1
<#
.SYNOPSIS
    Self-Healing Watchdog - 모든 핵심 프로세스를 감시하고 자동으로 재시작
.DESCRIPTION
    5분마다 핵심 프로세스를 체크하고, 죽은 것을 자동으로 재시작합니다.
    - Task Queue Server (8091)
    - RPA Worker
    - Monitoring Daemon
    - Original Data API (8093)
    
    백그라운드에서 지속 실행되며, 로그를 outputs/watchdog_log.jsonl에 기록합니다.
#>

param(
    [int]$CheckInterval = 300,  # 5분
    [int]$ServerPort = 8091,
    [string]$LogFile = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\watchdog_log.jsonl"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


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

function Restart-OriginalDataApi {
    param([int]$Port = 8093)
    Write-WatchdogLog -Action "restart" -Target "original_data_api" -Status "attempting"
    try {
        & "$WorkspaceRoot\scripts\ensure_original_data_api.ps1" -StartIfStopped -Port $Port | Out-Null
        $ok = Test-ServerHealth -Url "http://127.0.0.1:${Port}/health"
        if ($ok) {
            Write-WatchdogLog -Action "restart" -Target "original_data_api" -Status "success"
            return $true
        }
        else {
            Write-WatchdogLog -Action "restart" -Target "original_data_api" -Status "unhealthy"
            return $false
        }
    }
    catch {
        Write-WatchdogLog -Action "restart" -Target "original_data_api" -Status "failed" -Details $_.Exception.Message
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

    # Check Original Data API (8093)
    $odataHealthy = Test-ServerHealth -Url "http://127.0.0.1:8093/health"
    if (-not $odataHealthy) {
        Write-WatchdogLog -Action "check" -Target "original_data_api" -Status "down"
        Restart-OriginalDataApi -Port 8093 | Out-Null
    }
    
    # Information-theoretic stall detection (StallGuard)
    try {
        $venvPython = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
        $py = if (Test-Path $venvPython) { $venvPython } else { "python" }
        $stallGuard = "$WorkspaceRoot\fdo_agi_repo\monitoring\stall_guard.py"
        $paths = @()
        $cand = @(
            "$WorkspaceRoot\outputs\results_log.jsonl",
            "$WorkspaceRoot\fdo_agi_repo\memory\resonance_ledger.jsonl",
            "$WorkspaceRoot\fdo_agi_repo\outputs\online_learning_log.jsonl"
        )
        foreach ($p in $cand) { if (Test-Path $p) { $paths += $p } }
        $urls = @("http://127.0.0.1:${ServerPort}/api/health")

        if (Test-Path $stallGuard -and $paths.Count -gt 0) {
            $args = @($stallGuard,
                "--paths") + $paths + @(
                "--urls") + $urls + @(
                "--window-seconds", "300",
                "--min-entropy", "2.5",
                "--min-compression-ratio", "1.05",
                "--out-json", "$WorkspaceRoot\outputs\stall_guard_report.json"
            )

            $proc = Start-Process -FilePath $py -ArgumentList $args -NoNewWindow -PassThru -Wait
            $exitCode = $proc.ExitCode
            if ($exitCode -ne 0) {
                Write-WatchdogLog -Action "stall_detected" -Target "system" -Status "recovering" -Details "exit=$exitCode"
                # Targeted recovery: restart worker first, then server if still failing next loop
                Restart-RpaWorker | Out-Null
            }
            else {
                Write-WatchdogLog -Action "stall_check" -Target "system" -Status "ok"
            }
        }
    }
    catch {
        Write-WatchdogLog -Action "stall_check" -Target "system" -Status "error" -Details $_.Exception.Message
    }

    # All checks passed (or handled)
    Write-WatchdogLog -Action "check" -Target "all" -Status "ok"
    
    Start-Sleep -Seconds $CheckInterval
}