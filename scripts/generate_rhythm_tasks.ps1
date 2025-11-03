#Requires -Version 5.1
<#
.SYNOPSIS
    Rhythm-based Task Generator - 리듬 기반 작업 생성기
.DESCRIPTION
    현재 시간대와 시스템 상태에 따라 적절한 tasks.json을 동적으로 생성합니다.
    리듬=에너지=시간=관계 철학 구현
#>

param(
    [string]$WorkspaceFolder = "C:\workspace\agi",
    [switch]$Force,
    [switch]$ShowRhythm
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 리듬 감지
function Get-CurrentRhythm {
    $hour = (Get-Date).Hour
    
    # 시간대 기반 기본 리듬
    $timeRhythm = if ($hour -ge 6 -and $hour -lt 10) {
        "MORNING"
    }
    elseif ($hour -ge 10 -and $hour -lt 14) {
        "DAYTIME_FOCUS"
    }
    elseif ($hour -ge 14 -and $hour -lt 18) {
        "DAYTIME_FLOW"
    }
    elseif ($hour -ge 18 -and $hour -lt 22) {
        "EVENING"
    }
    else {
        "NIGHT"
    }
    
    # 시스템 상태 확인
    $cpu = (Get-Counter '\Processor(_Total)\% Processor Time' -ErrorAction SilentlyContinue).CounterSamples[0].CookedValue
    $memPercent = (Get-WmiObject Win32_OperatingSystem | Select-Object @{Name = "MemoryUsage"; Expression = { [math]::Round(($_.TotalVisibleMemorySize - $_.FreePhysicalMemory) / $_.TotalVisibleMemorySize * 100, 2) } }).MemoryUsage
    
    # 큐 상태 확인
    $queueSize = 0
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8091/api/queue/status" -TimeoutSec 2 -ErrorAction SilentlyContinue
        $queueSize = $response.queue_size
    }
    catch {}
    
    # 상태 기반 조정
    $stateModifier = "NORMAL"
    if ($cpu -gt 80 -or $memPercent -gt 85) {
        $stateModifier = "BUSY"
    }
    elseif ($queueSize -gt 50) {
        $stateModifier = "EMERGENCY"
    }
    
    return @{
        TimeRhythm    = $timeRhythm
        StateModifier = $stateModifier
        Hour          = $hour
        CPU           = [math]::Round($cpu, 1)
        Memory        = $memPercent
        QueueSize     = $queueSize
    }
}

# 리듬별 작업 분류
$rhythmTasks = @{
    MORNING       = @(
        "Morning: Kickoff (1h, open)",
        "Morning: Kickoff + Status (1h, open)",
        "?? AGI: Start Session (Check Status)",
        "System: Health Check (Quick)",
        "AGI: Quick Health Check (fast)",
        "Lumen: Quick Health Probe",
        "Monitoring: Unified Dashboard (AGI + Lumen)",
        "Queue: Health Check",
        "Watchdog: Check Task Watchdog Status"
    )
    
    DAYTIME_FOCUS = @(
        # 개발 & 테스트
        "Python: Run All Tests (repo venv)",
        "Dev: Local CI Check (Fast)",
        "Queue: Quick E2E (Ensure Server+Worker)",
        "RPA: Smoke E2E (OCR)",
        "Integration: Run Gitko E2E Test",
        
        # 빠른 체크
        "Queue: Health Check",
        "Queue: Latest Results (Success 5)",
        "System: Health Check (Quick)"
    )
    
    DAYTIME_FLOW  = @(
        # 분석 & 모니터링
        "Monitoring: Unified Dashboard (AGI + Lumen)",
        "Realtime: Summarize + Open",
        "YouTube: Build Index (open)",
        "Original Data: Build Index (open)",
        
        # 리듬 작업
        "?? Rhythm: Detect Current",
        "?? Rhythm: Show Resource Budget",
        "Autopoietic: Generate Loop Report (24h)",
        
        # 개발
        "Python: Run All Tests (parallel)",
        "Load Test: Light Smoke (10s)"
    )
    
    EVENING       = @(
        # 정리 & 백업
        "?뮶 Session: End Day (Save & Backup)",
        "End of Day: Backup",
        "Monitoring: Generate Report (24h) + Open",
        "?? Trinity: Autopoietic Cycle (24h, open)",
        
        # 요약
        "?占쏙옙 AGI: Summarize Ledger (24h)",
        "Realtime: Build ??Summarize ??Open (24h)",
        "?? Ops: Full Status Dashboard",
        
        # 정리
        "Monitoring: Rotate Snapshots (zip if needed)",
        "Operations: Cleanup Old Logs (7 days, DryRun)"
    )
    
    NIGHT         = @(
        # 학습 & 최적화
        "BQI: Run Phase 6 (Full Pipeline)",
        "?占쏙옙 BQI: Run Online Learner (24h)",
        "?占쏙옙 BQI: Ensemble Monitor (24h)",
        
        # 자동화 등록
        "?? Master: Register Auto-Start (5min delay)",
        "BQI: Register Phase 6 Scheduler (03:05)",
        "Monitoring: Register Collector (5m)",
        "Task Queue Server: Register (At Logon)",
        
        # 심층 분석
        "Python: Coverage HTML (generate)",
        "?占쏙옙 Analysis: Cache Effectiveness Report",
        "?占쏙옙 Analysis: Sena Correlation (10m window)"
    )
    
    EMERGENCY     = @(
        # 긴급 복구
        "Emergency: Rollback Canary (Interactive)",
        "Recover: Auto-Recover (one-shot)",
        "Diag: Binoche Agent (one-shot)",
        
        # 최소 체크
        "AGI: Quick Health Check (fast)",
        "Queue: Health Check",
        "System: Health Check (Quick)",
        
        # 긴급 중지
        "Watchdog: Stop Task Watchdog",
        "Monitor: Stop Worker Monitor",
        "Queue: Kill All Workers (DryRun)"
    )
    
    BUSY          = @(
        # 효율적 체크
        "AGI: Quick Health Check (fast)",
        "Queue: Health Check",
        "Queue: Latest Results (Success 5)",
        
        # 빠른 테스트
        "Dev: Local CI Check (Fast)",
        "Queue: Quick E2E (Verify ??Results ??Open Screenshot)",
        
        # 상태 확인
        "Monitoring: Unified Dashboard (AGI + Lumen)",
        "?? Rhythm: Detect Current"
    )
    
    ALWAYS        = @(
        # 언제나 사용 가능한 기본 작업
        "Queue: Ensure Server (8091)",
        "Queue: Ensure Worker",
        "ChatOps: Unified Status (?듯빀 ?곹깭)",
        "?? Rhythm: Detect Current",
        "?? Rhythm: Generate Adaptive Config",
        "Control Hub: Start (Tray)",
        "Control Hub: Open Dashboard"
    )
}

# 현재 리듬 가져오기
$rhythm = Get-CurrentRhythm

if ($ShowRhythm) {
    Write-Host "`n=== Current Rhythm Status ===" -ForegroundColor Cyan
    Write-Host "Time Rhythm:    $($rhythm.TimeRhythm)" -ForegroundColor Yellow
    Write-Host "State Modifier: $($rhythm.StateModifier)" -ForegroundColor $(if ($rhythm.StateModifier -eq "EMERGENCY") { "Red" } elseif ($rhythm.StateModifier -eq "BUSY") { "Yellow" } else { "Green" })
    Write-Host "Current Hour:   $($rhythm.Hour):00" -ForegroundColor White
    Write-Host "CPU Usage:      $($rhythm.CPU)%" -ForegroundColor White
    Write-Host "Memory Usage:   $($rhythm.Memory)%" -ForegroundColor White
    Write-Host "Queue Size:     $($rhythm.QueueSize)" -ForegroundColor White
    Write-Host ""
}

# 적용할 작업 목록 생성
$selectedTasks = @()
$selectedTasks += $rhythmTasks.ALWAYS

# 상태 우선순위
if ($rhythm.StateModifier -eq "EMERGENCY") {
    $selectedTasks += $rhythmTasks.EMERGENCY
    Write-Host "?? EMERGENCY MODE: 긴급 복구 작업만 표시" -ForegroundColor Red
}
elseif ($rhythm.StateModifier -eq "BUSY") {
    $selectedTasks += $rhythmTasks.BUSY
    Write-Host "?? BUSY MODE: 효율 중심 작업 표시" -ForegroundColor Yellow
}
else {
    # 시간대별 작업 추가
    $selectedTasks += $rhythmTasks[$rhythm.TimeRhythm]
    Write-Host "?? $($rhythm.TimeRhythm) MODE: 시간대 맞춤 작업 표시" -ForegroundColor Green
}

Write-Host "`n선택된 작업: $($selectedTasks.Count)개" -ForegroundColor Cyan
Write-Host "전체 작업 풀: ~200개 중 필터링됨" -ForegroundColor Gray

# 원본 tasks.json 읽기
$tasksPath = Join-Path $WorkspaceFolder ".vscode\tasks.json"
$backupPath = Join-Path $WorkspaceFolder ".vscode\tasks_full_backup.json"

if (-not (Test-Path $backupPath) -or $Force) {
    Write-Host "원본 tasks.json 백업 중..." -ForegroundColor Yellow
    Copy-Item -Path $tasksPath -Destination $backupPath -Force
}

$originalContent = Get-Content -Path $tasksPath -Raw -Encoding UTF8
$tasksObj = $originalContent | ConvertFrom-Json

# 선택된 작업만 필터링
$filteredTasks = $tasksObj.tasks | Where-Object {
    $selectedTasks -contains $_.label
}

Write-Host "필터링 결과: $($filteredTasks.Count)개 작업" -ForegroundColor Green

# 새 tasks.json 생성
$newTasksObj = @{
    version = "2.0.0"
    tasks   = $filteredTasks
}

$newTasksJson = $newTasksObj | ConvertTo-Json -Depth 100
$newTasksPath = Join-Path $WorkspaceFolder ".vscode\tasks_rhythm.json"

$newTasksJson | Out-File -FilePath $newTasksPath -Encoding UTF8 -Force

Write-Host "`n?? Rhythm-based tasks.json 생성 완료!" -ForegroundColor Green
Write-Host "   파일: $newTasksPath" -ForegroundColor Gray
Write-Host "`n?? 적용하려면:" -ForegroundColor Cyan
Write-Host "   Copy-Item '$newTasksPath' '$tasksPath' -Force" -ForegroundColor Yellow
Write-Host "`n?? 복원하려면:" -ForegroundColor Cyan
Write-Host "   Copy-Item '$backupPath' '$tasksPath' -Force" -ForegroundColor Yellow

# 메타데이터 저장
$metadata = @{
    generated_at   = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    rhythm         = $rhythm
    selected_tasks = $selectedTasks
    filtered_count = $filteredTasks.Count
    original_count = $tasksObj.tasks.Count
}

$metadataPath = Join-Path $WorkspaceFolder "outputs\tasks_rhythm_metadata.json"
$metadata | ConvertTo-Json -Depth 10 | Out-File -FilePath $metadataPath -Encoding UTF8 -Force

Write-Host "`n?? 메타데이터: $metadataPath" -ForegroundColor Gray
