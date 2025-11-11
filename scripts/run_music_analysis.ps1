#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Reaper + 음악 분석 실행 스크립트
.DESCRIPTION
    librosa로 음악 분석 → Reaper 리듬 매핑 → 세션 업데이트
.EXAMPLE
    .\run_music_analysis.ps1 -SampleFile "music\source\hope_and_rest.mp3"
#>

param(
    [string]$SampleFile = "",
    [string]$MusicDir = "C:\workspace\agi\music",
    [string]$OutputDir = "C:\workspace\agi\outputs",
    [switch]$SkipReaper,
    [switch]$OpenResults
)

$ErrorActionPreference = "Stop"
$ws = "C:\workspace\agi"
$pyExe = "$ws\fdo_agi_repo\.venv\Scripts\python.exe"

if (!(Test-Path $pyExe)) {
    $pyExe = "python"
}

Write-Host "`n🎼 Reaper + 음악 분석 파이프라인" -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor DarkCyan

# 1. 음악 분석 실행
Write-Host "📊 Step 1: 음악 패턴 분석 (librosa)" -ForegroundColor Cyan
$analysisArgs = @(
    "$ws\scripts\analyze_music_with_librosa.py"
    "--music-dir"
    $MusicDir
    "--output-dir"
    $OutputDir
)

if ($SampleFile) {
    $analysisArgs += "--sample-file"
    $analysisArgs += $SampleFile
}

& $pyExe @analysisArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 음악 분석 실패" -ForegroundColor Red
    exit 1
}

Write-Host "✓ 음악 분석 완료`n" -ForegroundColor Green

# 2. Reaper 리듬 매핑 (optional)
if (!$SkipReaper) {
    Write-Host "🎚️ Step 2: Reaper 리듬 매핑" -ForegroundColor Cyan
    & $pyExe "$ws\scripts\map_music_to_rhythm.py" `
        --analysis-file "$OutputDir\music_analysis_latest.json" `
        --rhythm-file "$OutputDir\RHYTHM_SYSTEM_STATUS_REPORT.md" `
        --output-file "$OutputDir\reaper_rhythm_mapping.json"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Reaper 매핑 실패 (스킵)" -ForegroundColor Yellow
    }
    else {
        Write-Host "✓ Reaper 매핑 완료`n" -ForegroundColor Green
    }
}

# 3. 세션 업데이트
Write-Host "📖 Step 3: 세션 업데이트" -ForegroundColor Cyan
& $pyExe "$ws\scripts\update_session_with_music.py" `
    --analysis-file "$OutputDir\music_analysis_latest.json" `
    --mapping-file "$OutputDir\reaper_rhythm_mapping.json" `
    --output-file "$OutputDir\session_update_music_latest.md"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 세션 업데이트 실패" -ForegroundColor Red
    exit 1
}

Write-Host "✓ 세션 업데이트 완료`n" -ForegroundColor Green

# 4. Goal Tracker 업데이트
Write-Host "🎯 Step 4: Goal Tracker 업데이트" -ForegroundColor Cyan
$goalTracker = "$ws\fdo_agi_repo\memory\goal_tracker.json"
if (Test-Path $goalTracker) {
    $goals = Get-Content $goalTracker -Raw | ConvertFrom-Json
    $musicGoal = $goals.goals | Where-Object { $_.title -like "*음악*" -or $_.title -like "*Reaper*" } | Select-Object -First 1
    
    if ($musicGoal -and $musicGoal.status -ne "completed") {
        $musicGoal.status = "in_progress"
        $musicGoal.last_update = (Get-Date -Format "o")
        $musicGoal.metadata.progress_notes += "`n[$(Get-Date -Format 'yyyy-MM-dd HH:mm')] 음악 분석 + Reaper 매핑 완료"
        
        $goals | ConvertTo-Json -Depth 10 | Set-Content $goalTracker -Encoding UTF8
        Write-Host "✓ Goal Tracker 업데이트 완료`n" -ForegroundColor Green
    }
}

# 5. 결과 요약
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkCyan
Write-Host "✨ 완료!" -ForegroundColor Green
Write-Host "`n생성된 파일:" -ForegroundColor Cyan
Write-Host "  📊 $OutputDir\music_analysis_latest.json" -ForegroundColor Yellow
Write-Host "  🎚️ $OutputDir\reaper_rhythm_mapping.json" -ForegroundColor Yellow
Write-Host "  📖 $OutputDir\session_update_music_latest.md" -ForegroundColor Yellow

if ($OpenResults) {
    Write-Host "`n📂 파일 열기..." -ForegroundColor Cyan
    code "$OutputDir\session_update_music_latest.md"
}

Write-Host "`n🎵 자연스러운 리듬으로 작업 완료!`n" -ForegroundColor Magenta
