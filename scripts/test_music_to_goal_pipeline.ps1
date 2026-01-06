#!/usr/bin/env pwsh
# Test Music → Rhythm → Goal 파이프라인
# Music Daemon의 자동 목표 생성 플로우 E2E 테스트

[CmdletBinding()]
param(
    [switch]$Silent,
    [int]$TestDuration = 60,  # 테스트 기간 (초)
    [switch]$DryRun
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

Write-Host "🎵 Music → Rhythm → Goal 파이프라인 테스트" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor DarkGray
Write-Host ""

# 1️⃣ 현재 상태 확인
Write-Host "📊 현재 시스템 상태 확인..." -ForegroundColor Yellow

$rhythmFile = Join-Path $WorkspaceRoot "outputs\RHYTHM_REST_PHASE_20251107.md"
$goalTrackerFile = Join-Path $WorkspaceRoot "fdo_agi_repo\memory\goal_tracker.json"
$musicEventLog = Join-Path $WorkspaceRoot "outputs\music_goal_events.jsonl"

# 리듬 상태 확인
if (Test-Path $rhythmFile) {
    $rhythmContent = Get-Content -Path $rhythmFile -Raw
    if ($rhythmContent -match "Overall Health Score:\s*(\d+\.\d+)%") {
        $rhythmScore = [double]$Matches[1]
        Write-Host "  ✅ 리듬 스코어: $rhythmScore%" -ForegroundColor Green
        $rhythmHealthy = ($rhythmScore -gt 85.0)
    } else {
        Write-Host "  ⚠️  리듬 스코어 파싱 실패" -ForegroundColor Yellow
        $rhythmHealthy = $false
    }
} else {
    Write-Host "  ❌ 리듬 리포트 없음" -ForegroundColor Red
    $rhythmHealthy = $false
}

# 목표 트래커 확인
$goalsBefore = @()
if (Test-Path $goalTrackerFile) {
    $trackerData = Get-Content -Path $goalTrackerFile -Raw | ConvertFrom-Json
    $goalsBefore = $trackerData.goals
    Write-Host "  📋 현재 목표 수: $($goalsBefore.Count)" -ForegroundColor Cyan
    
    $musicGoals = $goalsBefore | Where-Object { 
        $_.tags -and ($_.tags -contains "source:music_daemon" -or $_.tags -contains "trigger:rhythm")
    }
    Write-Host "  🎵 Music 유래 목표: $($musicGoals.Count)" -ForegroundColor Magenta
}

Write-Host ""

# 2️⃣ 시뮬레이션 리듬 데이터 생성 (테스트용)
Write-Host "🎭 시뮬레이션 리듬 이벤트 생성..." -ForegroundColor Yellow

if (-not $DryRun) {
    # 리듬 변화 시뮬레이션
    $testRhythmData = @"
# RHYTHM REST PHASE - Test Simulation
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Overall Health Score: 92.5% (EXCELLENT)

### System Components
- Task Queue Server (8091): ✅ ONLINE
- RPA Worker: ✅ ACTIVE (1 worker)
- Watchdog: ✅ RUNNING

### Recent Activity
- 자동 목표 생성 테스트 진행 중
- 리듬 기반 워크플로우 검증

### Rhythm Patterns
- Energy Level: High (92%)
- Focus Score: 0.85
- Flow State: ACTIVE
- Suggested Action: Create new goals
"@
    
    $testRhythmFile = Join-Path $WorkspaceRoot "outputs\RHYTHM_TEST_SIMULATION.md"
    $testRhythmData | Out-File -FilePath $testRhythmFile -Encoding UTF8 -Force
    Write-Host "  ✅ 테스트 리듬 파일 생성: RHYTHM_TEST_SIMULATION.md" -ForegroundColor Green
}

Write-Host ""

# 3️⃣ Python Music Daemon 호출 (테스트 모드)
Write-Host "🎵 Music Daemon 테스트 실행..." -ForegroundColor Yellow

$pythonExe = Join-Path $WorkspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"
$musicDaemonScript = Join-Path $WorkspaceRoot "scripts\music_daemon.py"

if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

if ($DryRun) {
    Write-Host "  🧪 [DRY-RUN] 실제 실행하지 않음" -ForegroundColor Yellow
    Write-Host "  명령: & $pythonExe $musicDaemonScript --once --threshold 0.0 --auto-goal" -ForegroundColor DarkGray
} else {
    Write-Host "  실행 중... (--once --threshold 0.0 --auto-goal)" -ForegroundColor Cyan
    
    try {
        & $pythonExe $musicDaemonScript --once --threshold 0.0 --auto-goal 2>&1 | Tee-Object -Variable musicOutput
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            Write-Host "  ✅ Music Daemon 실행 완료" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  Music Daemon 종료 (Exit: $exitCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ❌ 실행 실패: $_" -ForegroundColor Red
    }
}

Write-Host ""

# 4️⃣ 결과 검증
Write-Host "🔍 결과 검증..." -ForegroundColor Yellow

Start-Sleep -Seconds 2  # 파일 쓰기 대기

# 목표 트래커 재확인
$goalsAfter = @()
if (Test-Path $goalTrackerFile) {
    $trackerDataAfter = Get-Content -Path $goalTrackerFile -Raw | ConvertFrom-Json
    $goalsAfter = $trackerDataAfter.goals
    
    $newGoalsCount = $goalsAfter.Count - $goalsBefore.Count
    Write-Host "  📋 새로 생성된 목표: $newGoalsCount" -ForegroundColor Cyan
    
    # Music 유래 목표 확인
    $musicGoalsAfter = $goalsAfter | Where-Object { 
        $_.tags -and ($_.tags -contains "source:music_daemon" -or $_.tags -contains "trigger:rhythm")
    }
    Write-Host "  🎵 Music 유래 목표: $($musicGoalsAfter.Count)" -ForegroundColor Magenta
    
    # 최신 목표 출력
    if ($musicGoalsAfter.Count -gt 0) {
        Write-Host ""
        Write-Host "  📌 최신 Music 유래 목표:" -ForegroundColor Green
        $latest = $musicGoalsAfter | Sort-Object { $_.created_at } -Descending | Select-Object -First 3
        foreach ($g in $latest) {
            Write-Host "    - $($g.title) [$($g.status)]" -ForegroundColor White
            if ($g.tags) {
                Write-Host "      태그: $($g.tags -join ', ')" -ForegroundColor DarkGray
            }
        }
    }
}

# 이벤트 로그 확인
if (Test-Path $musicEventLog) {
    $events = Get-Content -Path $musicEventLog -Tail 5
    Write-Host ""
    Write-Host "  📝 최근 Music-Goal 이벤트 (최근 5개):" -ForegroundColor Yellow
    foreach ($e in $events) {
        $evt = $e | ConvertFrom-Json
        Write-Host "    [$($evt.timestamp)] $($evt.event_type): $($evt.goal_title)" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor DarkGray
Write-Host "✅ 파이프라인 테스트 완료" -ForegroundColor Green
Write-Host ""

# 요약 리포트
$report = @{
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    rhythm_healthy = $rhythmHealthy
    goals_before = $goalsBefore.Count
    goals_after = $goalsAfter.Count
    new_goals = $goalsAfter.Count - $goalsBefore.Count
    music_goals = ($musicGoalsAfter | Measure-Object).Count
    test_duration = $TestDuration
    dry_run = $DryRun.IsPresent
}

$reportJson = $report | ConvertTo-Json -Depth 5
$reportFile = Join-Path $WorkspaceRoot "outputs\music_goal_pipeline_test_latest.json"
$reportJson | Out-File -FilePath $reportFile -Encoding UTF8 -Force

Write-Host "📊 테스트 리포트 저장: outputs\music_goal_pipeline_test_latest.json" -ForegroundColor Cyan
Write-Host ""