#Requires -Version 5.1
<#
.SYNOPSIS
    AGI Self-Aware Context Manager (게임 봇처럼 상태 인식)

.DESCRIPTION
    Level 1: 키보드 포커스 기반 (좌표 불필요)
    Level 2: 이미지 인식 (화면에서 UI 찾기)
    Level 3: OCR 상태 파악 (텍스트 읽기)

.PARAMETER InstallDeps
    Python 패키지 설치 (pyautogui, pyperclip, pillow)

.PARAMETER UseImage
    Level 2 (이미지 인식) 사용

.PARAMETER TestFocus
    Level 1 (포커스 감지) 테스트

.PARAMETER TestImage
    Level 2 (이미지 인식) 테스트

.PARAMETER CreateGuide
    UI 템플릿 생성 가이드

.PARAMETER Verbose
    상세 로그 출력

.EXAMPLE
    .\auto_switch_chat_wrapper.ps1
    # 기본: Level 1 (키보드 포커스)

.EXAMPLE
    .\auto_switch_chat_wrapper.ps1 -UseImage
    # Level 2: 이미지 인식 사용

.EXAMPLE
    .\auto_switch_chat_wrapper.ps1 -InstallDeps
    # 필요한 패키지 설치
#>

[CmdletBinding()]
param(
    [switch]$InstallDeps,
    [switch]$UseImage,
    [switch]$TestFocus,
    [switch]$TestImage,
    [switch]$CreateGuide,
    [switch]$Verbose
)

$ErrorActionPreference = 'Stop'
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

# Python 실행 파일 찾기
$pythonExe = $null
$pythonCandidates = @(
    "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe",
    "$WorkspaceRoot\LLM_Unified\.venv\Scripts\python.exe",
    "python"
)

foreach ($candidate in $pythonCandidates) {
    if (Test-Path -LiteralPath $candidate -ErrorAction SilentlyContinue) {
        $pythonExe = $candidate
        break
    }
    elseif ($candidate -eq "python") {
        try {
            $null = & python --version 2>&1
            $pythonExe = "python"
            break
        }
        catch {
            continue
        }
    }
}

if (-not $pythonExe) {
    Write-Host "❌ Python을 찾을 수 없습니다" -ForegroundColor Red
    Write-Host "   가상환경을 활성화하거나 Python을 설치하세요" -ForegroundColor Yellow
    exit 1
}

Write-Host "🐍 Python: $pythonExe" -ForegroundColor Cyan

# 패키지 설치
if ($InstallDeps) {
    Write-Host ""
    Write-Host "📦 필요한 패키지 설치 중..." -ForegroundColor Cyan
    
    try {
        & $pythonExe -m pip install --quiet --upgrade pyautogui pyperclip pillow
        Write-Host "✅ 패키지 설치 완료" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ 패키지 설치 실패: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "   수동으로 설치하세요: pip install pyautogui pyperclip pillow" -ForegroundColor White
    }
    Write-Host ""
}

# Python 스크립트 실행
$scriptPath = Join-Path $PSScriptRoot "auto_switch_chat.py"

$pyArgs = @(
    $scriptPath,
    "--delay", $Delay
)

if ($ContextFile) {
    $pyArgs += "--context-file"
    $pyArgs += $ContextFile
}

Write-Host "🚀 AGI 자동 채팅창 전환 시작..." -ForegroundColor Cyan
Write-Host ""

try {
    & $pythonExe @pyArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
        Write-Host "🎉 완전 자동 전환 성공!" -ForegroundColor Green
        Write-Host "   새 채팅창에서 작업이 시작되었습니다" -ForegroundColor White
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
        exit 0
    }
    else {
        Write-Host ""
        Write-Host "❌ 자동 전환 실패 (Exit code: $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}
catch {
    Write-Host ""
    Write-Host "❌ 오류 발생: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
