#Requires -Version 5.1
<#
.SYNOPSIS
    Master AI Router - 사용자 메시지를 자동으로 적절한 시스템에 라우팅

.DESCRIPTION
    사용자가 Master에게 메시지를 전달하면, Master가 자동으로:
    1. 의도 파악 (Lumen/Binoche/Resonance/Master)
    2. 적절한 시스템에 라우팅
    3. 결과 통합 및 응답

.PARAMETER Message
    Master에게 전달할 메시지

.PARAMETER Json
    JSON 형식으로 출력

.EXAMPLE
    .\talk_to_master.ps1 "시스템 상태를 분석해줘"
    → Lumen으로 라우팅 → Trinity Cycle 실행

.EXAMPLE
    .\talk_to_master.ps1 "YouTube 영상 학습해줘"
    → Binoche로 라우팅 → RPA Worker 실행

.EXAMPLE
    .\talk_to_master.ps1 "현재 resonance 상태는?"
    → Resonance로 라우팅 → 메트릭 확인

.NOTES
    Author: AGI Master System
    Version: 1.0.0
#>

param(
    [Parameter(Mandatory = $true, Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$Message,
    
    [switch]$Json
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 작업 영역 루트
$WorkspaceRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)

# Python 경로 확인
$PythonPath = Join-Path $WorkspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $PythonPath)) {
    $PythonPath = "python"
}

# Master AI Router 경로
$RouterScript = Join-Path $WorkspaceRoot "scripts\master_ai_router.py"

# 메시지 조합
$UserMessage = $Message -join " "

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 58) -NoNewline -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan
Write-Host "  🧠 Master AI Router" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 58) -NoNewline -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan
Write-Host ""
Write-Host "  사용자: " -NoNewline -ForegroundColor Green
Write-Host $UserMessage
Write-Host ""

# Python 스크립트 실행
try {
    if ($Json) {
        & $PythonPath $RouterScript $Message --json
    }
    else {
        & $PythonPath $RouterScript $Message
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Router 실행 실패 (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}
catch {
    Write-Host "❌ Router 실행 중 오류:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 58) -NoNewline -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan
Write-Host ""
