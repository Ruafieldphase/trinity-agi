# Quantum Flow → Goal System 통합 실행 스크립트
[CmdletBinding()]
param(
    [switch]$OpenReport,
    [switch]$VerboseLog
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

Write-Host "🌊 Quantum Flow → Goal System 통합..." -ForegroundColor Cyan
Write-Host ""

# Python 실행 경로 결정
$pythonExe = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "⚠️  fdo_agi_repo venv not found, trying global python..." -ForegroundColor Yellow
    $pythonExe = "python"
}

# 통합 스크립트 실행
$scriptPath = "$WorkspaceRoot\scripts\integrate_quantum_flow_to_goals.py"

try {
    if ($VerboseLog) {
        & $pythonExe $scriptPath
    }
    else {
        & $pythonExe $scriptPath 2>&1 | Out-Host
    }
    
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Host "✅ 통합 완료!" -ForegroundColor Green
        
        # JSON 리포트 열기
        if ($OpenReport) {
            $latestJson = "$WorkspaceRoot\outputs\quantum_flow_latest.json"
            if (Test-Path $latestJson) {
                Write-Host "📄 Opening report: $latestJson" -ForegroundColor Cyan
                code $latestJson
            }
        }
        
        exit 0
    }
    else {
        Write-Host ""
        Write-Host "❌ 통합 실패 (Exit code: $exitCode)" -ForegroundColor Red
        exit $exitCode
    }
    
}
catch {
    Write-Host ""
    Write-Host "❌ Error: $_" -ForegroundColor Red
    exit 1
}
