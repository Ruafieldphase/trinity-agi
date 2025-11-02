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
Write-Host "[1/5] Task Queue Server..." -ForegroundColor Cyan
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

# Step 2: Ensure RPA Worker
Write-Host "`n[2/5] RPA Worker..." -ForegroundColor Cyan
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
Write-Host "`n[3/5] Monitoring Daemon..." -ForegroundColor Cyan
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

# Step 4: Start Self-Healing Watchdog
if (-not $SkipWatchdog) {
    Write-Host "`n[4/5] Self-Healing Watchdog..." -ForegroundColor Cyan
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
    Write-Host "`n[4/5] Watchdog skipped (-SkipWatchdog)" -ForegroundColor Gray
}

# Step 5: Run Self-Managing Agent (자율 점검 및 복구)
Write-Host "`n[5/6] Self-Managing Agent (AI Self-Check)..." -ForegroundColor Cyan
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
Write-Host "`n[6/6] Status Dashboard..." -ForegroundColor Cyan
try {
    & "$WorkspaceRoot\scripts\quick_status.ps1" -HideOptional -Perf | Out-Null
    Write-Host "  ✓ Dashboard generated" -ForegroundColor Green
}
catch {
    Write-Host "  ✗ Dashboard generation failed" -ForegroundColor Red
}

# Summary
$endTime = Get-Date
$elapsed = ($endTime - $startTime).TotalSeconds
Write-Host "`n=== Master Orchestrator Complete ===" -ForegroundColor Cyan
Write-Host "Elapsed: ${elapsed}s" -ForegroundColor Gray
Write-Host "All systems should now be running autonomously." -ForegroundColor Green
Write-Host "AI is self-managing. You just code. 🤖`n" -ForegroundColor Cyan

exit 0
