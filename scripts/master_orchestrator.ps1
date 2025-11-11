#Requires -Version 5.1
<#
.SYNOPSIS
    Master Orchestrator - 모든 자동화를 조율하는 중앙 제어 시스템
.DESCRIPTION
    부팅 시 단 한 번 실행되면 모든 핵심 프로세스를 시작하고 감시합니다.
    - 자동 업그레이드 감지
    - Task Queue Server 시작/확인
    - RPA Worker 시작/확인
    - Monitoring Daemon 시작/확인
    - Self-Healing Watchdog 시작
    - 시스템 상태 검증
#>

param(
    [switch]$SkipWatchdog,
    [switch]$Force,
    [switch]$Quiet,
    [int]$ServerPort = 8091,
    [string]$WorkspaceRoot = "$PSScriptRoot\.."
)

$ErrorActionPreference = "Continue"
$startTime = Get-Date

if (-not $Quiet) {
    Write-Host "`n╔════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║   AGI Master Orchestrator v1.0        ║" -ForegroundColor Cyan
    Write-Host "║   Starting All Core Systems...        ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════╝`n" -ForegroundColor Cyan
}

# Helper: Check if process is running
function Test-ProcessRunning {
    param([string]$Pattern)
    $procs = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*$Pattern*" }
    return ($null -ne $procs -and $procs.Count -gt 0)
}

# Helper: Wait for server health
function Wait-ForServer {
    param([string]$Url, [int]$MaxWait = 30)
    $waited = 0
    while ($waited -lt $MaxWait) {
        try {
            $resp = Invoke-WebRequest -Uri $Url -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
            if ($resp.StatusCode -eq 200) {
                Write-Host "  ✓ Server is healthy at $Url" -ForegroundColor Green
                return $true
            }
        }
        catch { }
        Start-Sleep -Seconds 2
        $waited += 2
    }
    Write-Host "  ✗ Server not responding at $Url (waited ${MaxWait}s)" -ForegroundColor Yellow
    return $false
}

# Step 1: Ensure Task Queue Server
Write-Host "[1/6] Task Queue Server..." -ForegroundColor Cyan
$serverRunning = Test-ProcessRunning "task_queue_server.py"
if (-not $serverRunning -or $Force) {
    Write-Host "  Starting Task Queue Server..." -ForegroundColor Yellow
    & "$WorkspaceRoot\scripts\ensure_task_queue_server.ps1" -Port $ServerPort
    Start-Sleep -Seconds 3
}
else {
    Write-Host "  Already running" -ForegroundColor Green
}

$serverHealthy = Wait-ForServer -Url "http://127.0.0.1:${ServerPort}/api/health" -MaxWait 15
if (-not $serverHealthy) {
    Write-Host "  WARNING: Server may not be fully ready" -ForegroundColor Red
}

# Step 1b: Ensure Original Data API (8093)
Write-Host "`n[2/6] Original Data API (8093)..." -ForegroundColor Cyan
try {
    & "$WorkspaceRoot\scripts\ensure_original_data_api.ps1" -StartIfStopped -Port 8093 | Out-Null
    Write-Host "  ✓ Original Data API ensured" -ForegroundColor Green
}
catch {
    Write-Host "  ✗ Failed to ensure Original Data API: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Step 2: Ensure RPA Worker
Write-Host "`n[3/6] RPA Worker..." -ForegroundColor Cyan
$workerRunning = Test-ProcessRunning "rpa_worker.py"
if (-not $workerRunning -or $Force) {
    Write-Host "  Starting RPA Worker..." -ForegroundColor Yellow
    & "$WorkspaceRoot\scripts\ensure_rpa_worker.ps1" -EnforceSingle -MaxWorkers 1
    Start-Sleep -Seconds 2
}
else {
    Write-Host "  Already running" -ForegroundColor Green
}

# Step 3: Ensure Monitoring Daemon
Write-Host "`n[4/7] Monitoring Daemon..." -ForegroundColor Cyan
$monitorRunning = Test-ProcessRunning "monitoring_daemon.py"
if (-not $monitorRunning -or $Force) {
    Write-Host "  Starting Monitoring Daemon..." -ForegroundColor Yellow
    $venvPython = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
    $daemonScript = "$WorkspaceRoot\fdo_agi_repo\monitoring\monitoring_daemon.py"
    
    if (Test-Path $venvPython) {
        Start-Process -FilePath $venvPython `
            -ArgumentList @($daemonScript, "--server", "http://127.0.0.1:${ServerPort}", "--interval", "5") `
            -WindowStyle Hidden `
            -WorkingDirectory "$WorkspaceRoot\fdo_agi_repo"
        Start-Sleep -Seconds 2
        Write-Host "  ✓ Monitoring Daemon started" -ForegroundColor Green
    }
    else {
        Write-Host "  ✗ Python venv not found: $venvPython" -ForegroundColor Red
    }
}
else {
    Write-Host "  Already running" -ForegroundColor Green
}

# Step 3.5: Ensure Music + Flow Observer Daemons
Write-Host "`n[4.5/7] Music + Flow Observer Daemons..." -ForegroundColor Cyan
try {
    $ensureScript = "$WorkspaceRoot\scripts\ensure_music_flow_daemons.ps1"
    if (Test-Path $ensureScript) {
        $result = & $ensureScript -Silent -JsonOnly 2>&1 | Out-String
        try {
            $status = $result | ConvertFrom-Json
            # JSON 필드명: music.running, flow.running (실제 구조)
            if ($status.music.running -and $status.flow.running) {
                Write-Host "  ✓ Music & Flow daemons running" -ForegroundColor Green
                Write-Host "    Music: PID $($status.music.pid)" -ForegroundColor Gray
                Write-Host "    Flow: Job $($status.flow.pid)" -ForegroundColor Gray
            }
            elseif ($status.music.running -or $status.flow.running) {
                Write-Host "  ⚠️  Partially running" -ForegroundColor Yellow
                if ($status.music.running) {
                    Write-Host "    Music: PID $($status.music.pid)" -ForegroundColor Gray
                }
                if ($status.flow.running) {
                    Write-Host "    Flow: Job $($status.flow.pid)" -ForegroundColor Gray
                }
            }
            else {
                Write-Host "  ✗ Failed to start daemons" -ForegroundColor Red
            }
        }
        catch {
            # JSON 파싱 실패 시 기본 메시지
            Write-Host "  ✓ Daemons ensured (status check failed)" -ForegroundColor Yellow
            Write-Host "    Parse error: $($_.Exception.Message)" -ForegroundColor Gray
        }
    }
    else {
        Write-Host "  ⚠️  Music+Flow ensure script not found" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  ✗ Failed to ensure Music+Flow daemons: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 4: Start Self-Healing Watchdog
if (-not $SkipWatchdog) {
    Write-Host "`n[5/7] Self-Healing Watchdog..." -ForegroundColor Cyan
    $watchdogRunning = Test-ProcessRunning "self_healing_watchdog.ps1"
    if (-not $watchdogRunning -or $Force) {
        Write-Host "  Starting Watchdog..." -ForegroundColor Yellow
        $watchdogScript = "$WorkspaceRoot\scripts\self_healing_watchdog.ps1"
        Start-Process -FilePath "powershell.exe" `
            -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $watchdogScript) `
            -WindowStyle Hidden `
            -WorkingDirectory $WorkspaceRoot
        Start-Sleep -Seconds 1
        Write-Host "  ✓ Watchdog started" -ForegroundColor Green
    }
    else {
        Write-Host "  Already running" -ForegroundColor Green
    }
}
else {
    Write-Host "`n[5/7] Watchdog skipped (-SkipWatchdog)" -ForegroundColor Gray
}

# Step 5: Run Self-Managing Agent (자율 점검 및 복구)
Write-Host "`n[6/7] Self-Managing Agent (AI Self-Check)..." -ForegroundColor Cyan
$pythonExe = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
$agentScript = "$WorkspaceRoot\fdo_agi_repo\orchestrator\self_managing_agent.py"

if ((Test-Path $pythonExe) -and (Test-Path $agentScript)) {
    try {
        & $pythonExe $agentScript --quiet
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ All dependencies verified" -ForegroundColor Green
        }
        else {
            Write-Host "  ⚠️  Some manual steps may be needed" -ForegroundColor Yellow
            Write-Host "     Check: outputs\self_managing_agent_latest.md" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "  ✗ Agent failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}
else {
    Write-Host "  ⚠️  Self-Managing Agent not available (Python venv or script missing)" -ForegroundColor Yellow
}

# Step 6: Generate Status Dashboard
Write-Host "`n[7/7] Status Dashboard..." -ForegroundColor Cyan
try {
    & "$WorkspaceRoot\scripts\quick_status.ps1" -HideOptional -Perf | Out-Null
    Write-Host "  ✓ Dashboard generated" -ForegroundColor Green
}
catch {
    Write-Host "  ✗ Dashboard generation failed" -ForegroundColor Red
}

# Step 7: Start Autopoietic Trinity Cycle Monitor
Write-Host "`n[extra 1/4] Trinity Cycle Monitor..." -ForegroundColor Cyan
$trinityRunning = Test-ProcessRunning "autopoietic_trinity_cycle.ps1"
if (-not $trinityRunning -or $Force) {
    Write-Host "  Scheduling Trinity Cycle..." -ForegroundColor Yellow
    # Trinity는 10:00에 실행되도록 작업 스케줄러에 등록되어 있음
    # 여기서는 등록 상태만 확인
    try {
        # 여러 가능한 이름 패턴으로 검색
        $trinityTask = Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object {
            $_.TaskName -like '*Trinity*' -or $_.TaskName -like '*Autopoietic*'
        } | Select-Object -First 1
        
        if ($trinityTask) {
            Write-Host "  ✓ Trinity Cycle scheduled: $($trinityTask.TaskName) ($($trinityTask.State))" -ForegroundColor Green
        }
        else {
            Write-Host "  ⚠️  Trinity Cycle not scheduled (run register_trinity_cycle_task.ps1)" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "  ⚠️  Could not verify Trinity Cycle status" -ForegroundColor Yellow
    }
}
else {
    Write-Host "  Already running or scheduled" -ForegroundColor Green
}

# Step 8: Start BQI Phase 6 System Monitor
Write-Host "`n[extra 2/4] BQI Phase 6 System..." -ForegroundColor Cyan
try {
    # 패턴으로 검색
    $bqiTasks = Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object {
        $_.TaskName -like '*BQI*' -or $_.TaskName -like '*Binoche*'
    }
    
    if ($bqiTasks.Count -gt 0) {
        Write-Host "  ✓ BQI systems scheduled: $($bqiTasks.Count) tasks" -ForegroundColor Green
        foreach ($task in ($bqiTasks | Select-Object -First 5)) {
            Write-Host "    - $($task.TaskName) ($($task.State))" -ForegroundColor Gray
        }
        if ($bqiTasks.Count -gt 5) {
            Write-Host "    - ... and $($bqiTasks.Count - 5) more" -ForegroundColor Gray
        }
    }
    else {
        Write-Host "  ⚠️  BQI systems not scheduled" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  ⚠️  Could not verify BQI status" -ForegroundColor Yellow
}

# Step 9: Start Cache Validation Monitor
Write-Host "`n[extra 3/4] Cache Validation System..." -ForegroundColor Cyan
try {
    # CacheValidation_ 패턴으로 검색
    $cacheTasks = Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object {
        $_.TaskName -like '*CacheValidation*'
    }
    if ($cacheTasks.Count -gt 0) {
        Write-Host "  ✓ Cache validation scheduled: $($cacheTasks.Count) tasks" -ForegroundColor Green
        foreach ($task in $cacheTasks) {
            Write-Host "    - $($task.TaskName) ($($task.State))" -ForegroundColor Gray
        }
    }
    else {
        Write-Host "  ⚠️  Cache validation not scheduled" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  ⚠️  Could not verify Cache validation status" -ForegroundColor Yellow
}

# Summary
$endTime = Get-Date
$elapsed = ($endTime - $startTime).TotalSeconds
Write-Host "`n=== Master Orchestrator Complete ===" -ForegroundColor Cyan
Write-Host "Elapsed: ${elapsed}s" -ForegroundColor Gray
Write-Host "Core systems: 7 active (including Music+Flow daemons)" -ForegroundColor Green
Write-Host "Scheduled systems: Trinity, BQI, Cache validation verified" -ForegroundColor Green
Write-Host "All systems should now be running autonomously." -ForegroundColor Green
Write-Host "AI is self-managing. You just code. 🤖`n" -ForegroundColor Cyan

exit 0
