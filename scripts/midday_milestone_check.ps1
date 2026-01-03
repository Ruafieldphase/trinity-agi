#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Phase 10.1: Mid-day Milestone Check (12:00 KST)

.DESCRIPTION
    12:00 KST에 자동으로 실행되어 Orchestrator 진행 상황을 체크하고
    목표 달성 여부를 확인합니다.

.PARAMETER AlertOnly
    알림만 표시하고 종료
#>
param(
    [switch]$AlertOnly,
    [string]$Start
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'

# 현재 시각
$now = Get-Date

# 기준 시작 시각 설정 (기본값: 2025-11-04 08:06:06 KST)
if ([string]::IsNullOrWhiteSpace($Start)) {
    $Start = '2025-11-04 08:06:06'
}

try {
    $startTime = [datetime]::Parse($Start)
}
catch {
    Write-Host "❌ Invalid -Start value. Use 'yyyy-MM-dd HH:mm:ss'" -ForegroundColor Red
    exit 1
}

# 동적 타겟 메트릭 계산 (5분 주기)
$minutesElapsed = ($now - $startTime).TotalMinutes
if ($minutesElapsed -lt 0) { $minutesElapsed = 0 }
$expectedCycles = [Math]::Floor($minutesElapsed / 5)
if ($expectedCycles -lt 0) { $expectedCycles = 0 }
$TARGET_CYCLES = $expectedCycles
$TARGET_EVENTS_MIN = $TARGET_CYCLES * 3
$TARGET_EVENTS_MAX = $TARGET_CYCLES * 5

Write-Host "\n$('=' * 70)" -ForegroundColor Cyan
Write-Host "   PHASE 10.1: MID-DAY MILESTONE CHECK" -ForegroundColor Green
Write-Host "$('=' * 70)`n" -ForegroundColor Cyan

Write-Host "⏰ Check time: $($now.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor White

if ($AlertOnly) {
    Write-Host "`n📢 REMINDER: Mid-day check scheduled for 12:00 KST" -ForegroundColor Yellow
    Write-Host "   Expected cycles: ~$TARGET_CYCLES" -ForegroundColor Gray
    Write-Host "   Expected events: $TARGET_EVENTS_MIN-$TARGET_EVENTS_MAX" -ForegroundColor Gray
    exit 0
}

# State 파일 로드
$statePath = "$WorkspaceRoot\outputs\full_stack_orchestrator_state.json"
if (-not (Test-Path $statePath)) {
    Write-Host "❌ State file not found: $statePath" -ForegroundColor Red
    exit 1
}

$state = Get-Content $statePath | ConvertFrom-Json

Write-Host "`n📊 CURRENT STATUS:`n" -ForegroundColor Yellow
Write-Host "  Learning cycles: $($state.state.learning_cycles)" -ForegroundColor Cyan
Write-Host "  Events processed: $($state.state.events_processed)" -ForegroundColor Cyan
Write-Host "  Last optimization: $($state.state.last_optimization)" -ForegroundColor Gray
Write-Host "  State updated: $($state.saved_at)" -ForegroundColor Gray

# 목표 달성 여부 체크 (여유치 허용)
$cyclesMet = $state.state.learning_cycles -ge ([Math]::Ceiling([double]$TARGET_CYCLES * 0.9))  # 90% 허용
$eventsMin = $state.state.events_processed -ge ([Math]::Ceiling([double]$TARGET_EVENTS_MIN * 0.8))  # 80% 허용

Write-Host "`n🎯 MILESTONE GOALS:`n" -ForegroundColor Magenta
Write-Host "  Target cycles: $TARGET_CYCLES (±10%)" -ForegroundColor White
Write-Host "    Actual: $($state.state.learning_cycles) " -NoNewline
if ($cyclesMet) {
    Write-Host "✅" -ForegroundColor Green
}
else {
    Write-Host "⚠️" -ForegroundColor Yellow
}

Write-Host "  Target events: $TARGET_EVENTS_MIN-$TARGET_EVENTS_MAX" -ForegroundColor White
Write-Host "    Actual: $($state.state.events_processed) " -NoNewline
if ($eventsMin) {
    Write-Host "✅" -ForegroundColor Green
}
else {
    Write-Host "⚠️" -ForegroundColor Yellow
}

# 진행률 계산
$hoursElapsed = ($now - $startTime).TotalHours
if ($hoursElapsed -le 0) { $hoursElapsed = 0.01 }
$progressPercent = ($hoursElapsed / 24.0) * 100

Write-Host "`n📈 PROGRESS:`n" -ForegroundColor Cyan
Write-Host "  Time elapsed: $([Math]::Round($hoursElapsed, 2))h / 24h" -ForegroundColor White
Write-Host "  Progress: $([Math]::Round($progressPercent, 1))%" -ForegroundColor White
Write-Host "  Cycles/hour: $([Math]::Round($state.state.learning_cycles / $hoursElapsed, 1))" -ForegroundColor White
$__cyclesVal = [double]$state.state.learning_cycles
if ($__cyclesVal -le 0) {
    Write-Host "  Events/cycle: 0" -ForegroundColor White
}
else {
    Write-Host "  Events/cycle: $([Math]::Round($state.state.events_processed / $__cyclesVal, 2))" -ForegroundColor White
}

# 24시간 예측
$projectedCycles = [Math]::Round((($state.state.learning_cycles / $hoursElapsed) * 24), 0)
$projectedEvents = [Math]::Round((($state.state.events_processed / $hoursElapsed) * 24), 0)

Write-Host "`n🔮 24-HOUR PROJECTION:`n" -ForegroundColor Magenta
Write-Host "  Projected cycles: $projectedCycles (target: 288)" -ForegroundColor White
Write-Host "  Projected events: $projectedEvents (target: 864-1440)" -ForegroundColor White

# 최종 상태
Write-Host "`n📋 STATUS: " -NoNewline
if ($cyclesMet -and $eventsMin) {
    Write-Host "✅ ON TRACK" -ForegroundColor Green
    Write-Host "`nOrchestrator is performing as expected." -ForegroundColor Gray
}
elseif ($cyclesMet -or $eventsMin) {
    Write-Host "⚠️ PARTIAL SUCCESS" -ForegroundColor Yellow
    Write-Host "`nSome metrics below target, but still operational." -ForegroundColor Gray
}
else {
    Write-Host "❌ BELOW EXPECTATIONS" -ForegroundColor Red
    Write-Host "`nInvestigation recommended." -ForegroundColor Gray
}

Write-Host "`n$('=' * 70)`n" -ForegroundColor Cyan

# 스냅샷 저장
$snapshot = @{
    timestamp   = $now.ToString('yyyy-MM-dd HH:mm:ss')
    milestone   = 'mid-day'
    target_time = '12:00 KST'
    actual_time = $now.ToString('HH:mm:ss')
    start_time  = $startTime.ToString('yyyy-MM-dd HH:mm:ss')
    metrics     = @{
        learning_cycles  = $state.state.learning_cycles
        events_processed = $state.state.events_processed
        hours_elapsed    = [Math]::Round($hoursElapsed, 2)
        progress_percent = [Math]::Round($progressPercent, 1)
    }
    targets     = @{
        cycles     = $TARGET_CYCLES
        events_min = $TARGET_EVENTS_MIN
        events_max = $TARGET_EVENTS_MAX
    }
    projections = @{
        cycles_24h = $projectedCycles
        events_24h = $projectedEvents
    }
    status      = if ($cyclesMet -and $eventsMin) { "on_track" } elseif ($cyclesMet -or $eventsMin) { "partial" } else { "below_target" }
}

$snapshotPath = "$WorkspaceRoot\outputs\midday_milestone_snapshot.json"
$snapshot | ConvertTo-Json -Depth 5 | Out-File $snapshotPath -Encoding UTF8
Write-Host "💾 Snapshot saved: $snapshotPath" -ForegroundColor Green