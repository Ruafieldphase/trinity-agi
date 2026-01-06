#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Autopoietic Scheduler 스모크 테스트 러너
.DESCRIPTION
    Original Data Phase 2 통합 검증: Scheduler 작업 등록 및 즉시 실행
    원본: <workspace_root>\original_data\scheduler.py
    구현: scripts/autopoietic_scheduler.py (순수 Python, 의존성 없음)
.NOTES
    Exit Code: 0=PASS, 1=FAIL
#>

param(
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "Autopoietic Scheduler Smoke Test" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host ""

# Python 경로 확인
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "FAIL: Python not found in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "[Info] Python: $($pythonCmd.Source)" -ForegroundColor Gray
Write-Host ""

# 스크립트 실행
$scriptPath = Join-Path $PSScriptRoot "autopoietic_scheduler.py"
if (-not (Test-Path $scriptPath)) {
    Write-Host "FAIL: Script not found: $scriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "[Running] $scriptPath" -ForegroundColor Cyan
Write-Host ""

try {
    & python $scriptPath
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Host "PASS: Autopoietic Scheduler smoke test succeeded" -ForegroundColor Green
        exit 0
    }
    else {
        Write-Host ""
        Write-Host "FAIL: Test returned exit code $exitCode" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host ""
    Write-Host "FAIL: $_" -ForegroundColor Red
    exit 1
}