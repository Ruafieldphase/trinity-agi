#!/usr/bin/env pwsh
<#
.SYNOPSIS
    새 VS Code 창에서 세션 연속성을 자동 복원합니다.

.DESCRIPTION
    워크스페이스를 열 때 자동으로:
    - 최근 세션 상태 스냅샷 로드
    - 현재 리듬 상태 리포트 표시
    - 핵심 프로세스 상태 확인
    - Goal Tracker 최근 상태 요약
    - 추천 다음 행동 제시

.PARAMETER Silent
    UI 출력 없이 조용히 실행 (백그라운드 복원용)

.PARAMETER OpenReport
    복원 리포트를 자동으로 VS Code에서 열기

.EXAMPLE
    .\session_continuity_restore.ps1
    새 창 열 때 자동 복원 (기본)

.EXAMPLE
    .\session_continuity_restore.ps1 -OpenReport
    복원 후 리포트 자동 오픈
#>

param(
    [switch]$Silent,
    [switch]$OpenReport
)

$ErrorActionPreference = 'Stop'
$ws = Split-Path -Parent $PSScriptRoot

function Write-Status {
    param([string]$Message, [string]$Color = 'Cyan')
    if (-not $Silent) {
        Write-Host $Message -ForegroundColor $Color
    }
}

function Get-LatestSessionSnapshot {
    $snapshotDir = Join-Path $ws 'outputs\session_memory'
    if (Test-Path $snapshotDir) {
        $latest = Get-ChildItem -Path $snapshotDir -Filter '*.json' -File |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
        return $latest
    }
    return $null
}

function Get-RhythmStatus {
    $rhythmFiles = @(
        'outputs\RHYTHM_REST_PHASE_20251107.md',
        'outputs\RHYTHM_SYSTEM_STATUS_REPORT.md'
    )
    
    foreach ($file in $rhythmFiles) {
        $path = Join-Path $ws $file
        if (Test-Path $path) {
            return $path
        }
    }
    return $null
}

function Get-GoalTrackerSummary {
    $goalPath = Join-Path $ws 'fdo_agi_repo\memory\goal_tracker.json'
    if (-not (Test-Path $goalPath)) {
        return $null
    }
    
    try {
        $data = Get-Content $goalPath -Raw | ConvertFrom-Json
        if ($data.goals -and $data.goals.Count -gt 0) {
            $recent = $data.goals | Select-Object -First 3
            return @{
                TotalGoals  = $data.goals.Count
                RecentGoals = $recent
                LastUpdate  = (Get-Item $goalPath).LastWriteTime
            }
        }
    }
    catch {
        Write-Status "⚠️ Goal Tracker 읽기 오류: $_" -Color Yellow
    }
    return $null
}

function Get-CoreProcessesStatus {
    $statusPath = Join-Path $ws 'outputs\core_processes_latest.json'
    if (Test-Path $statusPath) {
        $age = (Get-Date) - (Get-Item $statusPath).LastWriteTime
        if ($age.TotalMinutes -lt 30) {
            return @{
                Available = $true
                Age       = $age
                Path      = $statusPath
            }
        }
    }
    return @{ Available = $false }
}

# ========================================
# Main Restore Logic
# ========================================

Write-Status "`n🔄 세션 연속성 복원 시작..." -Color Green
Write-Status "시간: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"

$report = @()
$report += "# 세션 연속성 복원 리포트"
$report += ""
$report += "**복원 시간**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$report += ""

# 1. 최근 세션 스냅샷
Write-Status "📸 최근 세션 스냅샷 확인..."
$snapshot = Get-LatestSessionSnapshot
if ($snapshot) {
    Write-Status "  ✅ 스냅샷 발견: $($snapshot.Name)" -Color Green
    Write-Status "     생성 시간: $($snapshot.LastWriteTime)"
    $report += "## 최근 세션 스냅샷"
    $report += "- **파일**: ``$($snapshot.FullName)``"
    $report += "- **생성**: $($snapshot.LastWriteTime)"
    $report += ""
}
else {
    Write-Status "  ⚠️ 세션 스냅샷 없음 (첫 실행)" -Color Yellow
    $report += "## 최근 세션 스냅샷"
    $report += "- 없음 (첫 실행 또는 스냅샷 미생성)"
    $report += ""
}

# 2. 리듬 상태
Write-Status "`n🌊 리듬 상태 확인..."
$rhythmStatus = Get-RhythmStatus
if ($rhythmStatus) {
    Write-Status "  ✅ 리듬 리포트 발견" -Color Green
    $report += "## 리듬 상태"
    $report += "- **리포트**: ``$rhythmStatus``"
    
    # 리포트 미리보기 (첫 10줄)
    $preview = Get-Content $rhythmStatus -TotalCount 10
    $report += "- **미리보기**:"
    $report += "  ``````"
    $report += $preview -join "`n  "
    $report += "  ``````"
    $report += ""
}
else {
    Write-Status "  ℹ️ 리듬 리포트 없음" -Color Gray
    $report += "## 리듬 상태"
    $report += "- 리포트 없음"
    $report += ""
}

# 3. Goal Tracker
Write-Status "`n🎯 자율 목표 시스템 확인..."
$goalSummary = Get-GoalTrackerSummary
if ($goalSummary) {
    Write-Status "  ✅ Goal Tracker 활성" -Color Green
    Write-Status "     총 목표: $($goalSummary.TotalGoals)"
    Write-Status "     최근 업데이트: $($goalSummary.LastUpdate)"
    
    $report += "## 자율 목표 시스템"
    $report += "- **상태**: 활성"
    $report += "- **총 목표**: $($goalSummary.TotalGoals)"
    $report += "- **최근 업데이트**: $($goalSummary.LastUpdate)"
    $report += ""
    $report += "### 최근 목표 (Top 3)"
    foreach ($goal in $goalSummary.RecentGoals) {
        $status = $goal.status
        $emoji = if ($status -eq 'completed') { '✅' } elseif ($status -eq 'failed') { '❌' } else { '🔄' }
        $report += "- $emoji **$($goal.title)** ($status)"
    }
    $report += ""
}
else {
    Write-Status "  ℹ️ Goal Tracker 데이터 없음" -Color Gray
    $report += "## 자율 목표 시스템"
    $report += "- 데이터 없음"
    $report += ""
}

# 4. 코어 프로세스 상태
Write-Status "`n⚙️ 코어 프로세스 상태 확인..."
$coreStatus = Get-CoreProcessesStatus
if ($coreStatus.Available) {
    $ageMin = [math]::Round($coreStatus.Age.TotalMinutes, 1)
    Write-Status "  ✅ 상태 정보 사용 가능 (${ageMin}분 전)" -Color Green
    $report += "## 코어 프로세스 상태"
    $report += "- **상태 파일**: ``$($coreStatus.Path)``"
    $report += "- **생성**: ${ageMin}분 전"
    $report += "- 상세 정보는 파일 참조"
    $report += ""
}
else {
    Write-Status "  ⚠️ 최신 상태 정보 없음 (30분 이상 경과)" -Color Yellow
    $report += "## 코어 프로세스 상태"
    $report += "- 최신 정보 없음 (재생성 권장)"
    $report += ""
}

# 5. 추천 다음 행동
Write-Status "`n💡 추천 다음 행동..."
$report += "## 추천 다음 행동"
$report += ""

$recommendations = @()

if (-not $coreStatus.Available) {
    $recommendations += "1. **시스템 상태 확인**: VS Code 태스크 ``System: Core Processes (JSON)`` 실행"
}

if ($rhythmStatus) {
    $recommendations += "2. **리듬 리포트 확인**: ``$rhythmStatus`` 읽기"
}
else {
    $recommendations += "2. **리듬 생성**: 24시간 모니터링 리포트 생성 후 리듬 분석"
}

if ($goalSummary -and $goalSummary.TotalGoals -gt 0) {
    $recommendations += "3. **목표 계속**: 자율 목표 실행기 확인 (Goal: Execute + Open Tracker)"
}
else {
    $recommendations += "3. **목표 생성**: 자율 목표 생성기 실행 (Goal: Generate + Open)"
}

$recommendations += "4. **자연스러운 흐름**: 위 추천사항은 선택사항. 지금 하고 싶은 것부터 시작하세요."

foreach ($rec in $recommendations) {
    Write-Status "  $rec" -Color Cyan
    $report += $rec
}

$report += ""
$report += "---"
$report += "*자동 생성: session_continuity_restore.ps1*"

# 리포트 저장
$reportPath = Join-Path $ws 'outputs\session_continuity_latest.md'
$report -join "`n" | Out-File -FilePath $reportPath -Encoding utf8 -NoNewline

Write-Status "`n✅ 세션 연속성 복원 완료" -Color Green
Write-Status "   리포트: $reportPath`n"

# Copilot 컨텍스트 요약 생성
Write-Status "🤖 Copilot 컨텍스트 요약 생성 중..." -Color Cyan
$copilotScript = Join-Path $ws 'scripts\generate_copilot_context.ps1'
if (Test-Path $copilotScript) {
    try {
        & $copilotScript
        Write-Status "   ✅ Copilot 컨텍스트 요약 생성 완료" -Color Green
    }
    catch {
        Write-Status "   ⚠️ Copilot 컨텍스트 생성 실패 (무시)" -Color Yellow
    }
}

# 자동으로 리포트 열기 (옵션)
if ($OpenReport) {
    Write-Status "📂 리포트 열기..." -Color Cyan
    code $reportPath
}

exit 0
