#!/usr/bin/env pwsh
<#
.SYNOPSIS
    🎵 Reaper 실시간 음악 모니터 (PowerShell 래퍼)

.DESCRIPTION
    재생 중인 음악이 현재 리듬 페이즈와 맞는지 확인합니다.

.PARAMETER Once
    1회만 실행

.PARAMETER Interval
    체크 간격(초) (기본: 30)

.PARAMETER ReaperUrl
    Reaper Web Interface URL

.EXAMPLE
    .\run_reaper_monitor.ps1 -Once
    .\run_reaper_monitor.ps1 -Interval 60
#>

param(
    [switch]$Once,
    [int]$Interval = 30,
    [string]$ReaperUrl = "http://localhost:8080"
)

$ErrorActionPreference = 'Stop'
$ws = $PSScriptRoot | Split-Path -Parent

# Python 실행 파일 찾기
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

if (-not $pythonExe) {
    Write-Host "❌ Python을 찾을 수 없습니다." -ForegroundColor Red
    exit 1
}

# 스크립트 경로
$script = "$ws\scripts\reaper_realtime_monitor.py"
if (-not (Test-Path -LiteralPath $script)) {
    Write-Host "❌ 스크립트를 찾을 수 없음: $script" -ForegroundColor Red
    exit 1
}

# 인자 구성
$scriptArgs = @()
$scriptArgs += "--url", $ReaperUrl
$scriptArgs += "--interval", $Interval

if ($Once) {
    $scriptArgs += "--once"
}

# 실행
Write-Host "🎵 Reaper 실시간 모니터 시작..." -ForegroundColor Cyan
& $pythonExe $script @scriptArgs
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "`n✅ 완료" -ForegroundColor Green
}
else {
    Write-Host "`n⚠️ 종료 코드: $exitCode" -ForegroundColor Yellow
}

exit $exitCode