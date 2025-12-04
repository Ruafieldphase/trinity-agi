#!/usr/bin/env pwsh
<#
.SYNOPSIS
    시스템 통합 진단 실행

.DESCRIPTION
    전체 AGI 시스템의 모듈 간 통합 상태를 진단하고 리포트를 생성합니다.
    
.PARAMETER OpenReport
    진단 완료 후 리포트를 자동으로 엽니다

.EXAMPLE
    .\run_system_integration_diagnostic.ps1
    
.EXAMPLE
    .\run_system_integration_diagnostic.ps1 -OpenReport
#>

param(
    [switch]$OpenReport
)

$ErrorActionPreference = "Stop"
$workspaceRoot = Split-Path -Parent $PSScriptRoot

# Python 실행 파일 찾기
$pythonExe = $null
$venvPython = Join-Path $workspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $pythonExe = $venvPython
}
else {
    $pythonExe = "python"
}

Write-Host "🔍 시스템 통합 진단 시작..." -ForegroundColor Cyan
Write-Host ""

# 진단 스크립트 실행
$diagnosticScript = Join-Path $PSScriptRoot "system_integration_diagnostic.py"

try {
    & $pythonExe $diagnosticScript
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 진단 실패 (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    
    Write-Host ""
    Write-Host "✅ 진단 완료!" -ForegroundColor Green
    
    # 리포트 파일 경로
    $jsonReport = Join-Path $workspaceRoot "outputs\system_integration_diagnostic_latest.json"
    $mdReport = Join-Path $workspaceRoot "outputs\system_integration_diagnostic_latest.md"
    
    if ($OpenReport) {
        if (Test-Path $mdReport) {
            Write-Host "📄 Markdown 리포트 열기..." -ForegroundColor Cyan
            code $mdReport
        }
        elseif (Test-Path $jsonReport) {
            Write-Host "📊 JSON 리포트 열기..." -ForegroundColor Cyan
            code $jsonReport
        }
    }
    else {
        Write-Host ""
        Write-Host "📊 리포트 위치:" -ForegroundColor Yellow
        if (Test-Path $mdReport) {
            Write-Host "  - Markdown: $mdReport" -ForegroundColor White
        }
        if (Test-Path $jsonReport) {
            Write-Host "  - JSON: $jsonReport" -ForegroundColor White
        }
        Write-Host ""
        Write-Host "💡 리포트를 열려면: .\run_system_integration_diagnostic.ps1 -OpenReport" -ForegroundColor Gray
    }
    
}
catch {
    Write-Host "❌ 오류: $_" -ForegroundColor Red
    exit 1
}
