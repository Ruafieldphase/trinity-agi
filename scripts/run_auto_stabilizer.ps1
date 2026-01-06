#Requires -Version 5.1
<#
.SYNOPSIS
    Auto-Stabilizer 래퍼 스크립트

.DESCRIPTION
    Python 기반 Auto-Stabilizer를 호출하는 PowerShell 래퍼
    - Fear 신호 기반 자동 복구 절차 실행
    - Micro-Reset / Active Cooldown 자동 선택

.PARAMETER DryRun
    실제 실행 없이 시뮬레이션

.EXAMPLE
    .\scripts\run_auto_stabilizer.ps1
    .\scripts\run_auto_stabilizer.ps1 -DryRun
#>

[CmdletBinding()]
param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# Python 실행 파일 찾기
$pythonExe = $null
$candidates = @(
    "fdo_agi_repo/.venv/Scripts/python.exe",
    "LLM_Unified/.venv/Scripts/python.exe",
    "python"
)

foreach ($candidate in $candidates) {
    if ($candidate -eq "python") {
        if (Get-Command python -ErrorAction SilentlyContinue) {
            $pythonExe = "python"
            break
        }
    }
    elseif (Test-Path $candidate) {
        $pythonExe = $candidate
        break
    }
}

if (!$pythonExe) {
    Write-Host "❌ Python을 찾을 수 없습니다" -ForegroundColor Red
    exit 1
}

# Auto-Stabilizer 실행
$scriptArgs = @("scripts/auto_stabilizer.py")
if ($DryRun) {
    $scriptArgs += "--dry-run"
}

Write-Host "🔧 Auto-Stabilizer 실행 중..." -ForegroundColor Cyan
& $pythonExe $scriptArgs

exit $LASTEXITCODE