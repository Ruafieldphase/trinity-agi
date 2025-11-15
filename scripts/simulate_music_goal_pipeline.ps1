#!/usr/bin/env pwsh
# simulate_music_goal_pipeline.ps1
# Music → Rhythm → Goal 전체 파이프라인 시뮬레이션

param(
    [int]$DurationSeconds = 300,  # 5분 기본
    [switch]$SkipMusicPlay,       # 음악 재생 스킵 (테스트용)
    [switch]$OpenResults,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$ws = "c:\workspace\agi"
$py = "$ws\fdo_agi_repo\.venv\Scripts\python.exe"
if (!(Test-Path -LiteralPath $py)) { $py = 'python' }

function Write-Step {
    param($msg)
    Write-Host "`n🎯 $msg" -ForegroundColor Cyan
}

function Write-Success {
    param($msg)
    Write-Host "  ✅ $msg" -ForegroundColor Green
}

function Write-Info {
    param($msg)
    Write-Host "  ℹ️  $msg" -ForegroundColor Yellow
}

# ============================================================
# Step 1: Music Daemon 상태 확인
# ============================================================
Write-Step "Music Daemon 상태 확인"
$musicProc = Get-Process -Name 'python' -ErrorAction SilentlyContinue | Where-Object { 
    $_.CommandLine -like '*music_daemon.py*' 
}

if ($musicProc) {
    Write-Success "Music Daemon 실행 중 (PID: $($musicProc.Id))"
}
else {
    Write-Info "Music Daemon이 실행되지 않음. 자동 시작..."
    Start-Process -FilePath $py -ArgumentList @(
        "$ws\scripts\music_daemon.py",
        "--interval", "60",
        "--threshold", "0.3",
        "--auto-goal"
    ) -WindowStyle Hidden -PassThru | Out-Null
    Start-Sleep -Seconds 3
    Write-Success "Music Daemon 시작됨"
}

# ============================================================
# Step 2: 음악 재생 시뮬레이션 (선택적)
# ============================================================
if (!$SkipMusicPlay) {
    Write-Step "음악 재생 시뮬레이션 ($DurationSeconds초)"
    Write-Info "실제 음악 재생 대신 리듬 리포트 직접 생성..."
    
    # RHYTHM_REST_PHASE 파일 생성 (시뮬레이션)
    $rhythmReport = @{
        timestamp       = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
        phase           = "focus"
        metrics         = @{
            focus_duration_minutes = 15
            intensity_score        = 0.85
            quality_score          = 0.78
            overall_score          = 0.82
        }
        recommendations = @(
            "maintain_focus",
            "schedule_short_break"
        )
    }
    
    $rhythmFile = "$ws\outputs\RHYTHM_REST_PHASE_$(Get-Date -Format 'yyyyMMdd').md"
    @"
# Rhythm Report - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

**Phase**: $($rhythmReport.phase)
**Overall Score**: $($rhythmReport.metrics.overall_score * 100)%

## Metrics
- Focus Duration: $($rhythmReport.metrics.focus_duration_minutes) min
- Intensity: $($rhythmReport.metrics.intensity_score * 100)%
- Quality: $($rhythmReport.metrics.quality_score * 100)%

## Recommendations
$($rhythmReport.recommendations | ForEach-Object { "- $_" } | Out-String)
"@ | Out-File -FilePath $rhythmFile -Encoding utf8 -Force
    
    Write-Success "리듬 리포트 생성 완료"
}

# ============================================================
# Step 3: Music Daemon (one-shot with auto-goal)
# ============================================================
Write-Step "Music Daemon 실행 (Goal 생성)"
& $py "$ws\scripts\music_daemon.py" --once --threshold 1.0 --auto-goal

if ($LASTEXITCODE -eq 0) {
    Write-Success "Music Daemon 실행 완료"
}
else {
    Write-Info "Music Daemon 경고/실패 무시 (계속 진행)"
}

# ============================================================
# Step 4: Goal Generator 실행
# ============================================================
Write-Step "자율 목표 생성기 실행 (24h 분석)"
& $py "$ws\scripts\autonomous_goal_generator.py" --hours 24

if ($LASTEXITCODE -eq 0) {
    Write-Success "목표 생성 완료"
}
else {
    Write-Host "  ❌ 목표 생성 실패 (exit code: $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}

# ============================================================
# Step 4: Goal Tracker 확인
# ============================================================
Write-Step "Goal Tracker 상태 확인"
$trackerPath = "$ws\fdo_agi_repo\memory\goal_tracker.json"
if (Test-Path -LiteralPath $trackerPath) {
    $tracker = Get-Content -LiteralPath $trackerPath -Raw | ConvertFrom-Json
    
    $musicGoals = $tracker.goals | Where-Object { 
        $_.source -eq 'music_daemon' -or $_.origin -eq 'rhythm'
    }
    
    Write-Success "총 목표: $($tracker.goals.Count)개"
    Write-Info "Music-Goal: $($musicGoals.Count)개"
    
    if ($musicGoals.Count -gt 0) {
        Write-Host "`n  📋 최근 Music-Goal:" -ForegroundColor Magenta
        $musicGoals | Select-Object -First 3 | ForEach-Object {
            Write-Host "    - [$($_.status)] $($_.title)" -ForegroundColor White
        }
    }
}
else {
    Write-Host "  ⚠️  Goal Tracker 파일 없음" -ForegroundColor Yellow
}

# ============================================================
# Step 5: Music-Goal 이벤트 로그 확인
# ============================================================
Write-Step "Music-Goal 이벤트 로그 확인"
$eventLog = "$ws\outputs\music_goal_events.jsonl"
if (Test-Path -LiteralPath $eventLog) {
    $eventCount = (Get-Content -LiteralPath $eventLog).Count
    Write-Success "총 $eventCount 개 이벤트 기록됨"
    
    $latestEvent = Get-Content -LiteralPath $eventLog -Tail 1 | ConvertFrom-Json
    Write-Host "`n  🎵 최근 이벤트:" -ForegroundColor Magenta
    Write-Host "    Time: $($latestEvent.timestamp)" -ForegroundColor White
    Write-Host "    Type: $($latestEvent.event_type)" -ForegroundColor White
    Write-Host "    Goal: $($latestEvent.goal_title)" -ForegroundColor White
}
else {
    Write-Info "이벤트 로그 아직 없음"
}

# ============================================================
# Step 6: Dashboard 생성 (선택적)
# ============================================================
if ($OpenResults) {
    Write-Step "Goal Dashboard 생성"
    & "$ws\scripts\generate_autonomous_goal_dashboard.ps1" -OpenBrowser
    
    Write-Step "Music-Goal 이벤트 로그 열기"
    if (Test-Path -LiteralPath $eventLog) {
        code $eventLog
    }
}

# ============================================================
# Summary
# ============================================================
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🎉 Music-Goal 파이프라인 시뮬레이션 완료" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

Write-Host "`n📊 다음 단계:" -ForegroundColor Yellow
Write-Host "  1. Task: 'Goal: Execute #1 (Quantum Observer)' 실행" -ForegroundColor White
Write-Host "  2. Task: '📊 Goal: Open Dashboard (HTML)' 확인" -ForegroundColor White
Write-Host "  3. outputs/music_goal_events.jsonl 모니터링" -ForegroundColor White

if ($Verbose) {
    Write-Host "`n🔍 상세 로그:" -ForegroundColor Cyan
    Write-Host "  - Rhythm: $rhythmFile"
    Write-Host "  - Goals: $ws\outputs\autonomous_goals_latest.json"
    Write-Host "  - Tracker: $trackerPath"
    Write-Host "  - Events: $eventLog"
}
