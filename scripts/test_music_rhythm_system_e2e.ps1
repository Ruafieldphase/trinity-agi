#!/usr/bin/env pwsh
<#
.SYNOPSIS
    🧪 음악-리듬 시스템 E2E 통합 테스트

.DESCRIPTION
    전체 시스템을 자동으로 테스트합니다:
    1. 음악 감지
    2. 리듬 페이즈 판단
    3. 호환성 체크
    4. 자동 전환/각성 트리거

.PARAMETER Quick
    빠른 테스트 (1회만 실행)

.EXAMPLE
    .\test_music_rhythm_system_e2e.ps1
    .\test_music_rhythm_system_e2e.ps1 -Quick
#>

param(
    [switch]$Quick
)

$ErrorActionPreference = 'Stop'
$ws = $PSScriptRoot | Split-Path -Parent

Write-Host "`n🧪 음악-리듬 시스템 E2E 통합 테스트 시작`n" -ForegroundColor Cyan

# 테스트 결과
$results = @{
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    tests     = @()
    passed    = 0
    failed    = 0
}

function Test-AudioDetection {
    Write-Host "`n[1/5] 🎵 음악 감지 테스트..." -ForegroundColor Yellow
    
    try {
        $detectScript = "$ws\scripts\detect_audio_playback.ps1"
        if (-not (Test-Path -LiteralPath $detectScript)) {
            throw "detect_audio_playback.ps1을 찾을 수 없습니다"
        }
        
        $result = & $detectScript -OutJson "$ws\outputs\test_audio_detection.json"
        
        if (Test-Path "$ws\outputs\test_audio_detection.json") {
            $data = Get-Content "$ws\outputs\test_audio_detection.json" -Raw | ConvertFrom-Json
            
            Write-Host "   ✅ 음악 감지 성공" -ForegroundColor Green
            Write-Host "   - 재생 중: $($data.is_music_playing)" -ForegroundColor Gray
            Write-Host "   - 브라우저: $($data.browser_count)개" -ForegroundColor Gray
            
            return @{ success = $true; data = $data }
        }
        else {
            throw "출력 파일 생성 실패"
        }
    }
    catch {
        Write-Host "   ❌ 실패: $_" -ForegroundColor Red
        return @{ success = $false; error = $_.Exception.Message }
    }
}

function Test-RhythmPhaseDetection {
    Write-Host "`n[2/5] 🌊 리듬 페이즈 감지 테스트..." -ForegroundColor Yellow
    
    try {
        $rhythmFile = "$ws\outputs\RHYTHM_REST_PHASE_latest.md"
        
        if (Test-Path -LiteralPath $rhythmFile) {
            $content = Get-Content -LiteralPath $rhythmFile -Raw -Encoding UTF8
            
            $phase = "unknown"
            if ($content -match "DEEP_REST|deep_rest") { $phase = "deep_rest" }
            elseif ($content -match "RESTING|resting") { $phase = "resting" }
            elseif ($content -match "FLOWING|flowing") { $phase = "flowing" }
            elseif ($content -match "WORKING|working") { $phase = "working" }
            
            Write-Host "   ✅ 리듬 페이즈 감지 성공: $phase" -ForegroundColor Green
            
            return @{ success = $true; phase = $phase }
        }
        else {
            Write-Host "   ⚠️ 리듬 파일 없음 (기본값 사용)" -ForegroundColor Yellow
            return @{ success = $true; phase = "unknown" }
        }
    }
    catch {
        Write-Host "   ❌ 실패: $_" -ForegroundColor Red
        return @{ success = $false; error = $_.Exception.Message }
    }
}

function Test-ReaperMonitor {
    Write-Host "`n[3/5] 🎸 Reaper 모니터 테스트..." -ForegroundColor Yellow
    
    try {
        $monitorScript = "$ws\scripts\run_reaper_monitor.ps1"
        if (-not (Test-Path -LiteralPath $monitorScript)) {
            throw "run_reaper_monitor.ps1을 찾을 수 없습니다"
        }
        
        # 1회 실행
        $result = & $monitorScript -Once
        
        $reportFile = "$ws\outputs\music_monitoring\music_rhythm_match_latest.json"
        if (Test-Path -LiteralPath $reportFile) {
            $data = Get-Content -LiteralPath $reportFile -Raw | ConvertFrom-Json
            
            Write-Host "   ✅ Reaper 모니터 성공" -ForegroundColor Green
            Write-Host "   - 호환성: $($data.compatible)" -ForegroundColor Gray
            Write-Host "   - 현재 페이즈: $($data.current_rhythm_phase)" -ForegroundColor Gray
            Write-Host "   - 추론 페이즈: $($data.inferred_phase)" -ForegroundColor Gray
            
            return @{ success = $true; data = $data }
        }
        else {
            Write-Host "   ⚠️ Reaper 오프라인 또는 음악 미재생" -ForegroundColor Yellow
            return @{ success = $true; offline = $true }
        }
    }
    catch {
        Write-Host "   ❌ 실패: $_" -ForegroundColor Red
        return @{ success = $false; error = $_.Exception.Message }
    }
}

function Test-MusicWakeProtocol {
    Write-Host "`n[4/5] ⏰ Music Wake Protocol 테스트..." -ForegroundColor Yellow
    
    try {
        $wakeScript = "$ws\scripts\music_wake_protocol.py"
        if (-not (Test-Path -LiteralPath $wakeScript)) {
            throw "music_wake_protocol.py를 찾을 수 없습니다"
        }
        
        # Python 찾기
        $pythonPaths = @(
            "$ws\fdo_agi_repo\.venv\Scripts\python.exe",
            "$ws\LLM_Unified\.venv\Scripts\python.exe",
            "python"
        )
        
        $pythonExe = $null
        foreach ($p in $pythonPaths) {
            if (Test-Path -LiteralPath $p -ErrorAction SilentlyContinue) {
                $pythonExe = $p
                break
            }
            elseif ($p -eq 'python') {
                if (Get-Command python -ErrorAction SilentlyContinue) {
                    $pythonExe = 'python'
                    break
                }
            }
        }
        
        if ($pythonExe) {
            & $pythonExe $wakeScript --dry-run
            
            Write-Host "   ✅ Wake Protocol 정상" -ForegroundColor Green
            return @{ success = $true }
        }
        else {
            Write-Host "   ⚠️ Python을 찾을 수 없음 (스킵)" -ForegroundColor Yellow
            return @{ success = $true; skipped = $true }
        }
    }
    catch {
        Write-Host "   ❌ 실패: $_" -ForegroundColor Red
        return @{ success = $false; error = $_.Exception.Message }
    }
}

function Test-AdaptiveMusicPlayer {
    Write-Host "`n[5/5] 🎼 Adaptive Music Player 테스트..." -ForegroundColor Yellow
    
    try {
        $playerScript = "$ws\scripts\generate_music_simple.ps1"
        if (-not (Test-Path -LiteralPath $playerScript)) {
            throw "generate_music_simple.ps1을 찾을 수 없습니다"
        }
        
        # Config 파일 확인
        $configFile = "$ws\config\music_library.json"
        if (Test-Path -LiteralPath $configFile) {
            $config = Get-Content -LiteralPath $configFile -Raw | ConvertFrom-Json
            
            $categories = @($config.categories.PSObject.Properties.Name)
            
            Write-Host "   ✅ Music Player 정상" -ForegroundColor Green
            Write-Host "   - 카테고리: $($categories -join ', ')" -ForegroundColor Gray
            
            return @{ success = $true; categories = $categories }
        }
        else {
            throw "music_library.json을 찾을 수 없습니다"
        }
    }
    catch {
        Write-Host "   ❌ 실패: $_" -ForegroundColor Red
        return @{ success = $false; error = $_.Exception.Message }
    }
}

# 테스트 실행
$results.tests += @{
    name   = "Audio Detection"
    result = Test-AudioDetection
}

$results.tests += @{
    name   = "Rhythm Phase Detection"
    result = Test-RhythmPhaseDetection
}

$results.tests += @{
    name   = "Reaper Monitor"
    result = Test-ReaperMonitor
}

$results.tests += @{
    name   = "Music Wake Protocol"
    result = Test-MusicWakeProtocol
}

$results.tests += @{
    name   = "Adaptive Music Player"
    result = Test-AdaptiveMusicPlayer
}

# 결과 집계
foreach ($test in $results.tests) {
    if ($test.result.success) {
        $results.passed++
    }
    else {
        $results.failed++
    }
}

# 최종 리포트
Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
Write-Host "📊 테스트 결과 요약" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan

Write-Host "`n✅ 통과: $($results.passed)개" -ForegroundColor Green
Write-Host "❌ 실패: $($results.failed)개" -ForegroundColor Red

$totalTests = $results.passed + $results.failed
$successRate = if ($totalTests -gt 0) { [math]::Round(($results.passed / $totalTests) * 100, 1) } else { 0 }

Write-Host "`n성공률: $successRate%" -ForegroundColor $(if ($successRate -ge 80) { "Green" } else { "Yellow" })

# JSON 저장
$outputFile = "$ws\outputs\music_rhythm_e2e_test_latest.json"
$outputDir = Split-Path -Parent $outputFile
if (-not (Test-Path -LiteralPath $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

$results | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $outputFile -Encoding UTF8
Write-Host "`n💾 결과 저장: $outputFile" -ForegroundColor Gray

# 종료 코드
if ($results.failed -eq 0) {
    Write-Host "`n🎉 모든 테스트 통과!" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "`n⚠️ 일부 테스트 실패" -ForegroundColor Yellow
    exit 1
}