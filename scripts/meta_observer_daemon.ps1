# Meta-Layer Observer Daemon
# OS-level supervision with heartbeat monitoring
# Runs as Scheduled Task, independent of PowerShell jobs

param(
    [int]$IntervalSeconds = 30,
    [int]$TimeoutSeconds = 300,  # 5 minutes
    [string]$LogFile = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\meta_observer_log.jsonl"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Continue"

Write-Host "🔍 Meta-Layer Observer Daemon Started" -ForegroundColor Cyan
Write-Host "   Interval: $IntervalSeconds seconds" -ForegroundColor Gray
Write-Host "   Timeout: $TimeoutSeconds seconds" -ForegroundColor Gray
Write-Host "   Log: $LogFile" -ForegroundColor Gray
Write-Host ""

# Ensure outputs directory
$outputDir = Split-Path $LogFile -Parent
if (!(Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

function Write-Log {
    param($Message, $Level = "INFO", $Data = @{})
    $entry = @{
        timestamp = (Get-Date).ToUniversalTime().ToString("o")
        level     = $Level
        message   = $Message
        data      = $Data
    } | ConvertTo-Json -Compress
    Add-Content -Path $LogFile -Value $entry
}

function Get-AllMonitoredProcesses {
    $processes = @()
    
    # PowerShell jobs
    Get-Job | Where-Object { $_.State -eq 'Running' } | ForEach-Object {
        $processes += @{
            type    = "PowerShell Job"
            name    = $_.Name
            id      = $_.Id
            state   = $_.State
            started = $_.PSBeginTime
        }
    }
    
    # Task Queue Server
    $taskQueue = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
        try {
            (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine -like '*task_queue_server*'
        }
        catch { $false }
    }
    if ($taskQueue) {
        $processes += @{
            type   = "Task Queue Server"
            name   = "task_queue_server.py"
            id     = $taskQueue.Id
            state  = "Running"
            cpu    = $taskQueue.CPU
            memory = $taskQueue.WorkingSet64
        }
    }
    
    # RPA Workers
    Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
        try {
            (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine -like '*rpa_worker*'
        }
        catch { $false }
    } | ForEach-Object {
        $processes += @{
            type   = "RPA Worker"
            name   = "rpa_worker.py"
            id     = $_.Id
            state  = "Running"
            cpu    = $_.CPU
            memory = $_.WorkingSet64
        }
    }
    
    # Long-running PowerShell scripts
    Get-Process -Name pwsh, powershell -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
            if ($cmdLine -and $cmdLine.Length -gt 50) {
                $runtime = (Get-Date) - $_.StartTime
                if ($runtime.TotalSeconds -gt 60) {
                    # Running > 1 minute
                    $processes += @{
                        type            = "PowerShell Script"
                        name            = "pwsh/powershell"
                        id              = $_.Id
                        state           = "Running"
                        runtime_seconds = [int]$runtime.TotalSeconds
                        cpu             = $_.CPU
                        cmdline_preview = $cmdLine.Substring(0, [Math]::Min(100, $cmdLine.Length))
                    }
                }
            }
        }
        catch {}
    }
    
    return $processes
}

function Check-StuckProcess {
    param($Process)
    
    $isStuck = $false
    $reason = ""
    
    # Check timeout
    if ($Process.runtime_seconds -and $Process.runtime_seconds -gt $TimeoutSeconds) {
        $isStuck = $true
        $reason = "Timeout exceeded ($($Process.runtime_seconds)s > ${TimeoutSeconds}s)"
    }
    
    # Check CPU (completely idle for long time)
    if ($Process.cpu -ne $null -and $Process.cpu -lt 0.1 -and $Process.runtime_seconds -gt 120) {
        $isStuck = $true
        $reason = "No CPU activity (CPU: $($Process.cpu)%)"
    }
    
    return @{
        is_stuck = $isStuck
        reason   = $reason
    }
}

function Kill-StuckProcess {
    param($Process)
    
    try {
        Stop-Process -Id $Process.id -Force
        Write-Host "   ⚠️  Killed stuck process: $($Process.type) (PID: $($Process.id))" -ForegroundColor Yellow
        Write-Log -Message "Killed stuck process" -Level "WARNING" -Data $Process
        return $true
    }
    catch {
        Write-Host "   ❌ Failed to kill process: $($_.Exception.Message)" -ForegroundColor Red
        Write-Log -Message "Failed to kill process" -Level "ERROR" -Data @{
            process = $Process
            error   = $_.Exception.Message
        }
        return $false
    }
}

# Main loop
$iteration = 0
while ($true) {
    $iteration++
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    Write-Host "[$timestamp] Iteration $iteration - Scanning processes..." -ForegroundColor Gray
    
    try {
        $processes = Get-AllMonitoredProcesses
        $totalCount = $processes.Count
        $stuckCount = 0
        $killedCount = 0
        
        Write-Host "   Found $totalCount monitored processes" -ForegroundColor Cyan
        
        foreach ($proc in $processes) {
            $check = Check-StuckProcess -Process $proc
            if ($check.is_stuck) {
                $stuckCount++
                Write-Host "   🔴 STUCK: $($proc.type) (PID: $($proc.id)) - $($check.reason)" -ForegroundColor Red
                
                # Kill stuck process
                if (Kill-StuckProcess -Process $proc) {
                    $killedCount++
                }
            }
        }
        
        if ($stuckCount -eq 0) {
            Write-Host "   ✅ All processes healthy" -ForegroundColor Green
        }
        else {
            Write-Host "   ⚠️  Stuck: $stuckCount, Killed: $killedCount" -ForegroundColor Yellow
        }
        
        # Log summary
        Write-Log -Message "Scan complete" -Data @{
            iteration = $iteration
            total     = $totalCount
            stuck     = $stuckCount
            killed    = $killedCount
        }
        
    }
    catch {
        Write-Host "   ❌ Error during scan: $($_.Exception.Message)" -ForegroundColor Red
        Write-Log -Message "Scan error" -Level "ERROR" -Data @{
            error = $_.Exception.Message
        }
    }
    
    Write-Host ""
    Start-Sleep -Seconds $IntervalSeconds
}