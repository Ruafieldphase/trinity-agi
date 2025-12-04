<#
.SYNOPSIS
    GitHub Copilot용 세션 컨텍스트 요약 생성

.DESCRIPTION
    새 Copilot 채팅 세션에서 빠르게 참조할 수 있는 
    간단한 컨텍스트 요약을 생성합니다.

.EXAMPLE
    .\generate_copilot_context.ps1
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'
$ws = Split-Path $PSScriptRoot -Parent
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# 출력 파일
$outFile = Join-Path $ws "outputs\.copilot_context_summary.md"

Write-Host "🤖 Copilot 컨텍스트 요약 생성 중..." -ForegroundColor Cyan

# === 1. 리듬 상태 ===
$rhythmStatus = "⚠️ 리듬 파일 없음"
$rhythmFiles = Get-ChildItem (Join-Path $ws "outputs") -Filter "RHYTHM_*.md" | 
Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($rhythmFiles) {
    $preview = Get-Content $rhythmFiles.FullName -TotalCount 5
    $previewText = $preview -join " "
    if ($previewText -match '\*\*상태\*\*:\s*(.+)') {
        $rhythmStatus = $matches[1].Trim()
    }
    elseif ($previewText -match '건강도\*\*:\s*(.+)') {
        $rhythmStatus = $matches[1].Trim()
    }
    else {
        $rhythmStatus = "✅ 리듬 파일 존재 (파일: $($rhythmFiles.Name))"
    }
}

# === 2. 자율 목표 Top 3 ===
$topGoals = "⚠️ 목표 정보 없음"
$goalFile = Join-Path $ws "fdo_agi_repo\memory\goal_tracker.json"
if (Test-Path $goalFile) {
    try {
        $goals = Get-Content $goalFile -Raw | ConvertFrom-Json
        $recent = $goals.goals | Sort-Object last_updated -Descending | Select-Object -First 3
        $topGoals = ($recent | ForEach-Object {
                $icon = switch ($_.status) {
                    "completed" { "✅" }
                    "failed" { "❌" }
                    "in_progress" { "🔄" }
                    default { "⏸️" }
                }
                "- $icon $($_.title)"
            }) -join "`n"
    }
    catch {
        $topGoals = "⚠️ 목표 파일 파싱 실패"
    }
}

# === 3. 시스템 건강도 ===
$systemHealth = "⚠️ 시스템 상태 확인 불가"
$statusFile = Join-Path $ws "outputs\quick_status_latest.json"
if (Test-Path $statusFile) {
    try {
        $status = Get-Content $statusFile -Raw | ConvertFrom-Json
        $queueOk = $status.queue_server.status -eq "ok"
        $lumensOk = $status.lumen_status.endpoints_checked -gt 0
        
        if ($queueOk -and $lumensOk) {
            $systemHealth = "✅ 정상 (Queue + Lumen 동작)"
        }
        elseif ($queueOk) {
            $systemHealth = "⚠️ 부분 정상 (Queue만 동작)"
        }
        else {
            $systemHealth = "❌ 이상 감지"
        }
    }
    catch {
        $systemHealth = "⚠️ 상태 파일 파싱 실패"
    }
}

# === 4. 추천 다음 행동 ===
$recommendations = @()
$continuityFile = Join-Path $ws "outputs\session_continuity_latest.md"
if (Test-Path $continuityFile) {
    $content = Get-Content $continuityFile -Raw
    if ($content -match '## 추천 다음 행동\s*\n\n(.+?)(?=\n---|\z)') {
        $recBlock = $matches[1].Trim()
        $recommendations = ($recBlock -split '\n' | Where-Object { $_ -match '^\d+\.' }) -join "`n"
    }
}
if (-not $recommendations) {
    $recommendations = "1. 세션 연속성 리포트 확인: ``outputs/session_continuity_latest.md``"
}

# === 템플릿 생성 ===
$template = @"
# GitHub Copilot 세션 컨텍스트 (자동 생성)

**마지막 업데이트**: $timestamp

---

## 🎯 빠른 상태 요약

### 리듬 상태

$rhythmStatus

### 자율 목표 (Top 3)

$topGoals

### 시스템 건강도

$systemHealth

---

## 💡 추천 다음 행동

$recommendations

---

## 📂 상세 파일 위치

- 세션 리포트: ``outputs/session_continuity_latest.md``
- 리듬 상태: ``outputs/RHYTHM_REST_PHASE_*.md``
- 목표 트래커: ``fdo_agi_repo/memory/goal_tracker.json``
- 시스템 상태: ``outputs/quick_status_latest.json``

---

*자동 생성: generate_copilot_context.ps1*
"@

# 파일 저장
[System.IO.File]::WriteAllText($outFile, $template, [System.Text.Encoding]::UTF8)

Write-Host "✅ Copilot 컨텍스트 요약 생성 완료" -ForegroundColor Green
Write-Host "   파일: $outFile" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 새 Copilot 채팅에서 다음 명령어로 로드:" -ForegroundColor Yellow
Write-Host "   @workspace /file:outputs/.copilot_context_summary.md" -ForegroundColor White
