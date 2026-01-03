#Requires -Version 5.1
<#
.SYNOPSIS
    AGI 자가 인식 컨텍스트 관리 시스템

.DESCRIPTION
    AGI가 스스로 채팅 컨텍스트 길이를 감지하고
    필요 시 자동으로 새 채팅창으로 전환합니다.

.PARAMETER MaxTokens
    최대 토큰 수 (기본: 100000)

.PARAMETER AutoSwitch
    자동 전환 실행 (기본: False, 상태만 체크)

.PARAMETER StatusOnly
    상태만 출력

.EXAMPLE
    .\agi_self_aware_context_manager.ps1
    # 컨텍스트 상태 체크

.EXAMPLE
    .\agi_self_aware_context_manager.ps1 -AutoSwitch
    # 필요 시 자동 전환

.EXAMPLE
    .\agi_self_aware_context_manager.ps1 -MaxTokens 50000 -AutoSwitch
    # 임계값 낮춰서 자동 전환
#>

[CmdletBinding()]
param(
    [Parameter()]
    [int]$MaxTokens = 100000,
    
    [Parameter()]
    [switch]$AutoSwitch,
    
    [Parameter()]
    [switch]$StatusOnly
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


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
    exit 1
}

# Python 스크립트 실행
$scriptPath = Join-Path $PSScriptRoot "check_context_overflow.py"

$pyArgs = @(
    $scriptPath,
    "--max-tokens", $MaxTokens
)

if ($StatusOnly) {
    $pyArgs += "--status-only"
}
elseif ($AutoSwitch) {
    $pyArgs += "--auto-switch"
}

Write-Host "🧠 AGI 자가 인식 컨텍스트 관리 시스템" -ForegroundColor Cyan
Write-Host ""

try {
    & $pythonExe @pyArgs
    
    $exitCode = $LASTEXITCODE
    
    if ($StatusOnly) {
        # JSON 출력만
        exit 0
    }
    elseif ($exitCode -eq 1 -and -not $AutoSwitch) {
        # 전환 필요 (수동 모드)
        Write-Host ""
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
        Write-Host "💡 새 채팅창 전환을 권장합니다" -ForegroundColor Yellow
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
        exit 1
    }
    else {
        # 정상 또는 자동 전환 완료
        exit 0
    }
}
catch {
    Write-Host ""
    Write-Host "❌ 오류 발생: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}