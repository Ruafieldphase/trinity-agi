#Requires -Version 5.1
<#
.SYNOPSIS
    Music-Goal 통합 E2E 테스트 스크립트

.DESCRIPTION
    전체 파이프라인 검증:
    1. Python E2E 스크립트 실행
    2. Goal Tracker 상태 확인
    3. 이벤트 로그 검증
    4. Dashboard 생성

.PARAMETER OpenDashboard
    테스트 후 Goal Dashboard를 자동으로 열기

.EXAMPLE
    .\test_music_goal_integration.ps1 -OpenDashboard
#>

param(
    [switch]$OpenDashboard
)

$ErrorActionPreference = "Stop"
$workspaceRoot = Split-Path -Parent $PSScriptRoot

Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "🧪 Music-Goal Integration E2E Test" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan

# Python 환경 확인
$pythonExe = Join-Path $workspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

# 1. E2E 파이프라인 실행
Write-Host "`n📊 Step 1: Running E2E Pipeline..." -ForegroundColor Yellow
$pipelineScript = Join-Path $workspaceRoot "scripts\music_to_goal_pipeline_e2e.py"

try {
    & $pythonExe $pipelineScript
    if ($LASTEXITCODE -ne 0) {
        throw "Pipeline execution failed with exit code $LASTEXITCODE"
    }
    Write-Host "   ✓ Pipeline executed successfully" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Pipeline failed: $_" -ForegroundColor Red
    exit 1
}

# 2. Goal Tracker 검증
Write-Host "`n📊 Step 2: Validating Goal Tracker..." -ForegroundColor Yellow
$trackerPath = Join-Path $workspaceRoot "fdo_agi_repo\memory\goal_tracker.json"

if (Test-Path $trackerPath) {
    $tracker = Get-Content $trackerPath -Raw | ConvertFrom-Json
    $musicGoals = $tracker.goals | Where-Object { $_.source -eq "music_daemon" }
    
    Write-Host "   ✓ Total Goals: $($tracker.goals.Count)" -ForegroundColor Green
    Write-Host "   ✓ Music-Generated Goals: $($musicGoals.Count)" -ForegroundColor Green
    
    if ($musicGoals.Count -gt 0) {
        $latestGoal = $musicGoals | Sort-Object -Property created_at -Descending | Select-Object -First 1
        Write-Host "`n   📌 Latest Music Goal:" -ForegroundColor Cyan
        Write-Host "      Title: $($latestGoal.title)" -ForegroundColor White
        Write-Host "      Status: $($latestGoal.status)" -ForegroundColor White
        Write-Host "      Tags: $($latestGoal.tags -join ', ')" -ForegroundColor White
    }
} else {
    Write-Host "   ⚠️  Goal Tracker not found" -ForegroundColor Yellow
}

# 3. 이벤트 로그 검증
Write-Host "`n📊 Step 3: Validating Event Log..." -ForegroundColor Yellow
$eventLogPath = Join-Path $workspaceRoot "outputs\music_goal_events.jsonl"

if (Test-Path $eventLogPath) {
    $events = Get-Content $eventLogPath | ForEach-Object { $_ | ConvertFrom-Json }
    $recentEvents = $events | Select-Object -Last 10
    
    Write-Host "   ✓ Total Events: $($events.Count)" -ForegroundColor Green
    Write-Host "   ✓ Recent Events (last 10):" -ForegroundColor Cyan
    
    $recentEvents | ForEach-Object {
        $ts = [datetime]::Parse($_.timestamp).ToString("HH:mm:ss")
        Write-Host "      [$ts] $($_.event_type)" -ForegroundColor White
    }
} else {
    Write-Host "   ⚠️  Event log not found" -ForegroundColor Yellow
}

# 4. Dashboard 생성 (옵션)
if ($OpenDashboard) {
    Write-Host "`n📊 Step 4: Generating Dashboard..." -ForegroundColor Yellow
    $dashboardScript = Join-Path $workspaceRoot "scripts\generate_autonomous_goal_dashboard.ps1"
    
    if (Test-Path $dashboardScript) {
        & $dashboardScript -OpenBrowser
        Write-Host "   ✓ Dashboard opened" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Dashboard script not found" -ForegroundColor Yellow
    }
}

# 5. 결과 요약
Write-Host "`n" -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "✅ Music-Goal Integration Test Complete" -ForegroundColor Green
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan

Write-Host "`n📁 Outputs:" -ForegroundColor Cyan
Write-Host "   - Goal Tracker: $trackerPath" -ForegroundColor White
Write-Host "   - Event Log: $eventLogPath" -ForegroundColor White

$resultPath = Join-Path $workspaceRoot "outputs\music_goal_pipeline_result_latest.json"
if (Test-Path $resultPath) {
    Write-Host "   - Pipeline Result: $resultPath" -ForegroundColor White
}

Write-Host "`n💡 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Review Goal Dashboard: .\scripts\generate_autonomous_goal_dashboard.ps1 -OpenBrowser" -ForegroundColor White
Write-Host "   2. Check event timeline: code $eventLogPath" -ForegroundColor White
Write-Host "   3. Verify Music Daemon is running with --auto-goal" -ForegroundColor White

exit 0
