#Requires -Version 5.1
<#
.SYNOPSIS
    Adaptive Music Player - 상황에 맞는 음악 자동 재생

.DESCRIPTION
    리듬 페이즈, 시간대, 작업 컨텍스트에 따라 자동으로 음악 선택 및 재생
    
.PARAMETER Category
    재생할 음악 카테고리 (wake_up, focus, coding, rest, transition)
    
.PARAMETER Url
    직접 지정할 YouTube URL
    
.PARAMETER AutoSelect
    자동 선택 모드 (리듬/시간 기반)
    
.EXAMPLE
    .\play_adaptive_music.ps1
    # 자동 선택 모드
    
.EXAMPLE
    .\play_adaptive_music.ps1 -Category wake_up
    # 각성용 음악 재생
    
.EXAMPLE
    .\play_adaptive_music.ps1 -Category coding
    # 코딩용 음악 재생
#>
param(
    [ValidateSet("wake_up", "focus", "coding", "rest", "transition")]
    [string]$Category,
    
    [string]$Url
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# 경로 설정
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspace = Split-Path -Parent $scriptRoot
$pythonScript = Join-Path $scriptRoot "adaptive_music_player.py"

# Python 실행 파일 찾기
$pythonExe = $null
$venvPaths = @(
    "$workspace\fdo_agi_repo\.venv\Scripts\python.exe",
    "$workspace\LLM_Unified\.venv\Scripts\python.exe"
)

foreach ($path in $venvPaths) {
    if (Test-Path $path) {
        $pythonExe = $path
        break
    }
}

if (-not $pythonExe) {
    $pythonExe = "python"
}

# 인자 구성
$pythonArgs = @($pythonScript)

if ($Url) {
    $pythonArgs += "--url", $Url
}
elseif ($Category) {
    $pythonArgs += "--category", $Category
}
# else: AutoSelect (기본 동작)

# Python 스크립트 실행
Write-Host "🎵 Launching Adaptive Music Player..." -ForegroundColor Cyan
& $pythonExe @pythonArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Music playback initiated!" -ForegroundColor Green
}
else {
    Write-Host "`n❌ Music playback failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}
