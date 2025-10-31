#!/usr/bin/env pwsh
<#
.SYNOPSIS
    End-to-End Monitoring Test - Task Queue Server + Worker + Monitoring Daemon

.DESCRIPTION
    1. Task Queue Server 시작
    2. RPA Worker 시작  
    3. YouTube 학습 작업 3개 추가
    4. Monitoring Daemon 실행 (30초)
    5. 결과 확인

.PARAMETER Port
    Task Queue Server 포트 (기본값: 8091)

.PARAMETER Duration
    모니터링 데몬 실행 시간(분) (기본값: 0.5 = 30초)

.EXAMPLE
    .\start_monitoring_e2e.ps1
    .\start_monitoring_e2e.ps1 -Port 8092 -Duration 1
#>

param(
    [int]$Port = 8091,
    [double]$Duration = 0.5
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$ServerPath = Join-Path $WorkspaceRoot "LLM_Unified\ion-mentoring"
$RPAPath = Join-Path $WorkspaceRoot "fdo_agi_repo"
$MonitoringPath = Join-Path $RPAPath "monitoring"

Write-Host "🚀 Starting E2E Monitoring Test" -ForegroundColor Cyan
Write-Host "  Port: $Port" -ForegroundColor Gray
Write-Host "  Duration: $Duration minutes" -ForegroundColor Gray
Write-Host ""

# 1. Task Queue Server 시작
Write-Host "📡 Step 1: Starting Task Queue Server (Port $Port)..." -ForegroundColor Yellow
$ServerJob = Start-Job -ScriptBlock {
    param($ServerPath, $Port)
    Set-Location $ServerPath
    & .\.venv\Scripts\python.exe task_queue_server.py --port $Port
} -ArgumentList $ServerPath, $Port -Name "TaskQueueServer_$Port"

Write-Host "  Job ID: $($ServerJob.Id)" -ForegroundColor Gray
Start-Sleep -Seconds 3

# Health check
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 3
    Write-Host "  ✅ Server is online: $($health.status)" -ForegroundColor Green
}
catch {
    Write-Host "  ❌ Server failed to start!" -ForegroundColor Red
    Stop-Job -Id $ServerJob.Id -ErrorAction SilentlyContinue
    Remove-Job -Id $ServerJob.Id -ErrorAction SilentlyContinue
    exit 1
}

Write-Host ""

# 2. YouTube 학습 작업 3개 추가
Write-Host "📝 Step 2: Enqueueing 3 YouTube tasks..." -ForegroundColor Yellow
$urls = @(
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://www.youtube.com/watch?v=jNQXAC9IVRw",
    "https://www.youtube.com/watch?v=9bZkp7q19f0"
)

foreach ($url in $urls) {
    try {
        $body = @{
            type = "youtube_learn"
            data = @{
                url            = $url
                clip_seconds   = 10
                max_frames     = 2
                frame_interval = 30.0
            }
        } | ConvertTo-Json -Compress

        $response = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/tasks/create" `
            -Method Post `
            -ContentType "application/json" `
            -Body $body `
            -TimeoutSec 3

        Write-Host "  ✅ Task created: $($response.task_id)" -ForegroundColor Green
    }
    catch {
        Write-Host "  ⚠️ Failed to create task: $_" -ForegroundColor Yellow
    }
}

Write-Host ""

# 3. RPA Worker 시작
Write-Host "🤖 Step 3: Starting RPA Worker..." -ForegroundColor Yellow
$WorkerJob = Start-Job -ScriptBlock {
    param($RPAPath, $Port)
    Set-Location $RPAPath
    & .\.venv\Scripts\python.exe integrations\rpa_worker.py `
        --server "http://127.0.0.1:$Port" `
        --interval 0.5 `
        --worker-name "test-worker" `
        --log-level INFO
} -ArgumentList $RPAPath, $Port -Name "RPAWorker_$Port"

Write-Host "  Job ID: $($WorkerJob.Id)" -ForegroundColor Gray
Start-Sleep -Seconds 2

Write-Host ""

# 4. Monitoring Daemon 실행
Write-Host "📊 Step 4: Starting Monitoring Daemon ($Duration minutes)..." -ForegroundColor Yellow
Write-Host ""

try {
    Set-Location $RPAPath
    & .\.venv\Scripts\python.exe monitoring\monitoring_daemon.py `
        --server "http://127.0.0.1:$Port" `
        --interval 3 `
        --duration $Duration
}
catch {
    Write-Host "  ⚠️ Monitoring daemon error: $_" -ForegroundColor Yellow
}

Write-Host ""

# 5. 결과 확인
Write-Host "📊 Step 5: Checking Final Results..." -ForegroundColor Yellow

try {
    $stats = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/stats" -TimeoutSec 3
    Write-Host ""
    Write-Host "Final Statistics:" -ForegroundColor Cyan
    Write-Host "  Pending:    $($stats.pending)" -ForegroundColor Gray
    Write-Host "  Inflight:   $($stats.inflight)" -ForegroundColor Gray
    Write-Host "  Completed:  $($stats.completed)" -ForegroundColor Gray
    Write-Host "  Successful: $($stats.successful) ✅" -ForegroundColor Green
    Write-Host "  Failed:     $($stats.failed) ❌" -ForegroundColor Red
    Write-Host "  Success Rate: $([math]::Round($stats.success_rate, 1))%" -ForegroundColor $(if ($stats.success_rate -ge 80) { "Green" } else { "Yellow" })
}
catch {
    Write-Host "  ⚠️ Failed to fetch stats: $_" -ForegroundColor Yellow
}

Write-Host ""

# Cleanup
Write-Host "🧹 Cleanup: Stopping background jobs..." -ForegroundColor Yellow
Stop-Job -Id $ServerJob.Id -ErrorAction SilentlyContinue
Stop-Job -Id $WorkerJob.Id -ErrorAction SilentlyContinue
Remove-Job -Id $ServerJob.Id -Force -ErrorAction SilentlyContinue
Remove-Job -Id $WorkerJob.Id -Force -ErrorAction SilentlyContinue

Write-Host "  ✅ Jobs stopped" -ForegroundColor Green
Write-Host ""

# 출력 파일 경로
$MetricsFile = Join-Path $RPAPath "outputs\rpa_monitoring_metrics.jsonl"
$AlertsFile = Join-Path $RPAPath "outputs\rpa_monitoring_alerts.jsonl"

Write-Host "📁 Output Files:" -ForegroundColor Cyan
if (Test-Path $MetricsFile) {
    $lineCount = (Get-Content $MetricsFile | Measure-Object -Line).Lines
    Write-Host "  Metrics: $MetricsFile ($lineCount snapshots)" -ForegroundColor Gray
}
if (Test-Path $AlertsFile) {
    $lineCount = (Get-Content $AlertsFile | Measure-Object -Line).Lines
    Write-Host "  Alerts:  $AlertsFile ($lineCount alerts)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "✅ E2E Monitoring Test Complete!" -ForegroundColor Green
