# Phase 5 통합 시스템 시작 스크립트
# Task Queue Server + Web Dashboard + Monitoring Daemon을 모두 시작

param(
    [switch]$StopAll,
    [switch]$CheckStatus
)

$ErrorActionPreference = "Stop"

$TASK_QUEUE_PORT = 8091
$WEB_DASHBOARD_PORT = 8000
$WORKSPACE = "C:\workspace\agi"

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Yellow
    Write-Host ("=" * 60) -ForegroundColor Cyan
}

function Check-Port {
    param([int]$Port)
    
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 2 -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

function Stop-AllServers {
    Write-Header "Stopping All Servers"
    
    # Task Queue Server Job 종료
    Get-Job -Name 'TaskQueueServer' -ErrorAction SilentlyContinue | Stop-Job
    Get-Job -Name 'TaskQueueServer' -ErrorAction SilentlyContinue | Remove-Job
    
    # Web Dashboard Job 종료
    Get-Job -Name 'WebDashboard' -ErrorAction SilentlyContinue | Stop-Job
    Get-Job -Name 'WebDashboard' -ErrorAction SilentlyContinue | Remove-Job
    
    # Monitoring Daemon Job 종료
    Get-Job -Name 'MonitoringDaemon' -ErrorAction SilentlyContinue | Stop-Job
    Get-Job -Name 'MonitoringDaemon' -ErrorAction SilentlyContinue | Remove-Job
    
    Write-Host "✅ All servers stopped" -ForegroundColor Green
}

function Show-Status {
    Write-Header "System Status Check"
    
    # Task Queue Server
    if (Check-Port -Port $TASK_QUEUE_PORT) {
        Write-Host "✅ Task Queue Server (port $TASK_QUEUE_PORT) is ONLINE" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Task Queue Server (port $TASK_QUEUE_PORT) is OFFLINE" -ForegroundColor Red
    }
    
    # Web Dashboard
    if (Check-Port -Port $WEB_DASHBOARD_PORT) {
        Write-Host "✅ Web Dashboard (port $WEB_DASHBOARD_PORT) is ONLINE" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Web Dashboard (port $WEB_DASHBOARD_PORT) is OFFLINE" -ForegroundColor Red
    }
    
    # Background Jobs
    Write-Host ""
    Write-Host "Background Jobs:" -ForegroundColor Cyan
    Get-Job | Format-Table Id, Name, State, HasMoreData
}

if ($StopAll) {
    Stop-AllServers
    exit 0
}

if ($CheckStatus) {
    Show-Status
    exit 0
}

# 시작 시퀀스
Write-Header "🚀 Phase 5: Starting Integrated System"

# Step 1: Task Queue Server 시작
Write-Host ""
Write-Host "[1/3] Starting Task Queue Server..." -ForegroundColor Cyan

if (Check-Port -Port $TASK_QUEUE_PORT) {
    Write-Host "  ℹ️ Task Queue Server is already running" -ForegroundColor Yellow
}
else {
    Start-Job -Name 'TaskQueueServer' -ScriptBlock {
        Set-Location 'C:\workspace\agi\LLM_Unified\ion-mentoring'
        python task_queue_server.py --port 8091
    } | Out-Null
    
    Write-Host "  ⏳ Waiting for Task Queue Server to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    
    if (Check-Port -Port $TASK_QUEUE_PORT) {
        Write-Host "  ✅ Task Queue Server started successfully" -ForegroundColor Green
    }
    else {
        Write-Host "  ❌ Failed to start Task Queue Server" -ForegroundColor Red
        exit 1
    }
}

# Step 2: Web Dashboard 시작
Write-Host ""
Write-Host "[2/3] Starting Web Dashboard..." -ForegroundColor Cyan

if (Check-Port -Port $WEB_DASHBOARD_PORT) {
    Write-Host "  ℹ️ Web Dashboard is already running" -ForegroundColor Yellow
}
else {
    Start-Job -Name 'WebDashboard' -ScriptBlock {
        Set-Location 'C:\workspace\agi\fdo_agi_repo'
        python monitoring\web_server.py
    } | Out-Null
    
    Write-Host "  ⏳ Waiting for Web Dashboard to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    
    if (Check-Port -Port $WEB_DASHBOARD_PORT) {
        Write-Host "  ✅ Web Dashboard started successfully" -ForegroundColor Green
    }
    else {
        Write-Host "  ❌ Failed to start Web Dashboard" -ForegroundColor Red
        exit 1
    }
}

# Step 3: Monitoring Daemon 시작 (선택적)
Write-Host ""
Write-Host "[3/3] Starting Monitoring Daemon..." -ForegroundColor Cyan

$daemonScript = "$WORKSPACE\fdo_agi_repo\monitoring\monitoring_daemon.py"
if (Test-Path $daemonScript) {
    Start-Job -Name 'MonitoringDaemon' -ScriptBlock {
        param($script, $workspace)
        Set-Location $workspace
        python $script --interval 10
    } -ArgumentList $daemonScript, $WORKSPACE | Out-Null
    
    Write-Host "  ✅ Monitoring Daemon started" -ForegroundColor Green
}
else {
    Write-Host "  ℹ️ Monitoring Daemon script not found (optional)" -ForegroundColor Yellow
}

# 최종 상태 확인
Write-Host ""
Show-Status

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "  ✅ Phase 5 System Started Successfully!" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host ""
Write-Host "📌 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Open Web Dashboard: http://127.0.0.1:$WEB_DASHBOARD_PORT" -ForegroundColor White
Write-Host "  2. Run E2E Test: python monitoring\test_phase5_e2e.py" -ForegroundColor White
Write-Host "  3. Stop all servers: .\start_phase5_system.ps1 -StopAll" -ForegroundColor White
Write-Host ""
