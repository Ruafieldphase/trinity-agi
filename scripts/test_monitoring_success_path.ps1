#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Full E2E Test with Mock Worker (Success Path)

.DESCRIPTION
    1. Task Queue Server 시작
    2. Mock Worker 시작 (작업을 즉시 성공 처리)
    3. 테스트 작업 5개 추가
    4. Monitoring Daemon 실행 (30초)
    5. 결과 확인 및 보고서 생성

.PARAMETER Port
    Task Queue Server 포트 (기본값: 8091)

.PARAMETER TaskCount
    추가할 작업 수 (기본값: 5)

.PARAMETER Duration
    모니터링 시간(분) (기본값: 0.5)

.EXAMPLE
    .\test_monitoring_success_path.ps1
    .\test_monitoring_success_path.ps1 -TaskCount 10 -Duration 1
#>

param(
    [int]$Port = 8091,
    [int]$TaskCount = 5,
    [double]$Duration = 0.5
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$ServerPath = Join-Path $WorkspaceRoot "LLM_Unified\ion-mentoring"
$RPAPath = Join-Path $WorkspaceRoot "fdo_agi_repo"

Write-Host "🎯 Full E2E Monitoring Test (Success Path)" -ForegroundColor Cyan
Write-Host "  Port: $Port" -ForegroundColor Gray
Write-Host "  Tasks: $TaskCount" -ForegroundColor Gray
Write-Host "  Duration: $Duration minutes" -ForegroundColor Gray
Write-Host ""

# 1. Task Queue Server 시작
Write-Host "📡 [1/5] Starting Task Queue Server..." -ForegroundColor Yellow
$ServerJob = Start-Job -ScriptBlock {
    param($ServerPath, $Port)
    Set-Location $ServerPath
    & .\.venv\Scripts\python.exe task_queue_server.py --port $Port 2>&1 | Out-Null
} -ArgumentList $ServerPath, $Port -Name "TaskQueueServer_E2E"

Start-Sleep -Seconds 3

try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 3
    Write-Host "  ✅ Server online: $($health.status)" -ForegroundColor Green
}
catch {
    Write-Host "  ❌ Server failed!" -ForegroundColor Red
    Stop-Job -Id $ServerJob.Id -ErrorAction SilentlyContinue
    Remove-Job -Id $ServerJob.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# 2. Mock Worker 시작 (Python 인라인 스크립트)
Write-Host "🤖 [2/5] Starting Mock Worker..." -ForegroundColor Yellow

$MockWorkerScript = @"
import requests
import time
import random
import sys

SERVER = 'http://127.0.0.1:$Port'
WORKER_NAME = 'mock-worker-success'

def process_task(task):
    task_id = task['task_id']
    task_type = task.get('type', 'unknown')
    
    # Simulate processing (0.2-0.5s)
    time.sleep(random.uniform(0.2, 0.5))
    
    # Always success
    result = {
        'success': True,
        'data': {
            'task_id': task_id,
            'task_type': task_type,
            'duration_ms': random.randint(200, 500),
            'result': 'Mock task completed successfully'
        }
    }
    
    # Submit result
    try:
        requests.post(f'{SERVER}/api/tasks/{task_id}/result', json=result, timeout=5)
        print(f'✅ Task {task_id} completed')
        return True
    except Exception as e:
        print(f'❌ Failed to submit result: {e}')
        return False

def main():
    print(f'Mock Worker started: {WORKER_NAME}')
    
    while True:
        try:
            # Fetch next task
            response = requests.get(
                f'{SERVER}/api/tasks/next',
                headers={'X-Worker-Name': WORKER_NAME},
                timeout=5
            )
            
            if response.status_code != 200:
                time.sleep(1)
                continue
            
            data = response.json()
            task = data.get('task')
            
            if not task:
                time.sleep(0.5)
                continue
            
            # Process task
            process_task(task)
            
        except KeyboardInterrupt:
            print('Worker stopped by user')
            break
        except Exception as e:
            print(f'Worker error: {e}')
            time.sleep(1)

if __name__ == '__main__':
    main()
"@

$MockWorkerPath = Join-Path $RPAPath "mock_worker.py"
$MockWorkerScript | Out-File -FilePath $MockWorkerPath -Encoding UTF8

$WorkerJob = Start-Job -ScriptBlock {
    param($RPAPath, $MockWorkerPath)
    Set-Location $RPAPath
    & .\.venv\Scripts\python.exe $MockWorkerPath 2>&1
} -ArgumentList $RPAPath, $MockWorkerPath -Name "MockWorker_E2E"

Write-Host "  ✅ Mock Worker started (Job ID: $($WorkerJob.Id))" -ForegroundColor Green
Start-Sleep -Seconds 2

# 3. 테스트 작업 추가
Write-Host "📝 [3/5] Creating $TaskCount test tasks..." -ForegroundColor Yellow

for ($i = 1; $i -le $TaskCount; $i++) {
    try {
        $body = @{
            type = "test_task"
            data = @{
                task_number = $i
                description = "E2E Test Task #$i"
            }
        } | ConvertTo-Json -Compress

        $response = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/tasks/create" `
            -Method Post `
            -ContentType "application/json" `
            -Body $body `
            -TimeoutSec 3

        Write-Host "  ✅ Task #$i created: $($response.task_id)" -ForegroundColor Green
        Start-Sleep -Milliseconds 100
    }
    catch {
        Write-Host "  ⚠️ Failed to create task #$i" -ForegroundColor Yellow
    }
}

Write-Host ""

# 4. Monitoring Daemon 실행
Write-Host "📊 [4/5] Starting Monitoring Daemon..." -ForegroundColor Yellow
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

# 5. 최종 결과 확인
Write-Host "📊 [5/5] Final Results" -ForegroundColor Yellow
Write-Host ""

try {
    $stats = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/stats" -TimeoutSec 3
    
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "               Final Statistics              " -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Tasks Created:   $TaskCount" -ForegroundColor Gray
    Write-Host "  Pending:         $($stats.pending)" -ForegroundColor Yellow
    Write-Host "  In-flight:       $($stats.inflight)" -ForegroundColor Yellow
    Write-Host "  Completed:       $($stats.completed)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  ✅ Successful:   $($stats.successful)" -ForegroundColor Green
    Write-Host "  ❌ Failed:       $($stats.failed)" -ForegroundColor Red
    Write-Host ""
    
    $successRateColor = if ($stats.success_rate -ge 90) { "Green" } elseif ($stats.success_rate -ge 70) { "Yellow" } else { "Red" }
    Write-Host "  Success Rate:    $([math]::Round($stats.success_rate, 1))%" -ForegroundColor $successRateColor
    
    if ($stats.avg_duration_ms -gt 0) {
        Write-Host "  Avg Duration:    $([math]::Round($stats.avg_duration_ms, 0))ms" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    
    # 성공 판정
    if ($stats.success_rate -ge 80) {
        Write-Host ""
        Write-Host "🎉 TEST PASSED! Success rate: $([math]::Round($stats.success_rate, 1))%" -ForegroundColor Green
        $exitCode = 0
    }
    else {
        Write-Host ""
        Write-Host "⚠️ TEST FAILED! Success rate: $([math]::Round($stats.success_rate, 1))% (threshold: 80%)" -ForegroundColor Red
        $exitCode = 1
    }
    
}
catch {
    Write-Host "  ❌ Failed to fetch final stats: $_" -ForegroundColor Red
    $exitCode = 1
}

Write-Host ""

# Cleanup
Write-Host "🧹 Cleanup..." -ForegroundColor Yellow
Stop-Job -Id $ServerJob.Id -ErrorAction SilentlyContinue
Stop-Job -Id $WorkerJob.Id -ErrorAction SilentlyContinue
Remove-Job -Id $ServerJob.Id -Force -ErrorAction SilentlyContinue
Remove-Job -Id $WorkerJob.Id -Force -ErrorAction SilentlyContinue

if (Test-Path $MockWorkerPath) {
    Remove-Item $MockWorkerPath -Force -ErrorAction SilentlyContinue
}

Write-Host "  ✅ Cleanup complete" -ForegroundColor Green
Write-Host ""

# Output files
$MetricsFile = Join-Path $RPAPath "outputs\rpa_monitoring_metrics.jsonl"
$AlertsFile = Join-Path $RPAPath "outputs\rpa_monitoring_alerts.jsonl"

Write-Host "📁 Output Files:" -ForegroundColor Cyan
if (Test-Path $MetricsFile) {
    $lineCount = (Get-Content $MetricsFile | Measure-Object -Line).Lines
    Write-Host "  📊 Metrics: $lineCount snapshots" -ForegroundColor Gray
    Write-Host "      $MetricsFile" -ForegroundColor DarkGray
}
if (Test-Path $AlertsFile) {
    $lineCount = (Get-Content $AlertsFile | Measure-Object -Line).Lines
    Write-Host "  🚨 Alerts:  $lineCount alerts" -ForegroundColor Gray
    Write-Host "      $AlertsFile" -ForegroundColor DarkGray
}

Write-Host ""
exit $exitCode