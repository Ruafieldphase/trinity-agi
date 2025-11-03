#Requires -Version 5.1
<#
.SYNOPSIS
    Emotion-Triggered Stabilizer 실행 (Realtime Pipeline + Auto-Stabilizer 통합)

.DESCRIPTION
    Phase 5: Auto-Stabilizer Integration
    - Realtime Pipeline에서 Lumen 감정 신호 모니터링
    - Fear 레벨별 자동 안정화 트리거
    - Emotion-aware maintenance scheduling

.PARAMETER CheckInterval
    체크 주기 (초, 기본값: 300 = 5분)

.PARAMETER DryRun
    Dry-run 모드 (실제 실행 없음)

.PARAMETER AutoExecute
    자동 실행 모드 (Fear 레벨별 자동 안정화)

.PARAMETER Once
    한 번만 실행하고 종료

.EXAMPLE
    .\start_emotion_stabilizer.ps1
    # 5분마다 체크 (dry-run)

.EXAMPLE
    .\start_emotion_stabilizer.ps1 -CheckInterval 600 -AutoExecute
    # 10분마다 체크 (자동 실행)

.EXAMPLE
    .\start_emotion_stabilizer.ps1 -Once
    # 한 번만 실행
#>

param(
    [int]$CheckInterval = 300,
    [switch]$DryRun,
    [switch]$AutoExecute,
    [switch]$Once
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$PythonExe = Join-Path $WorkspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"
$Script = Join-Path $WorkspaceRoot "scripts\emotion_triggered_stabilizer.py"

# Check Python
if (-not (Test-Path $PythonExe)) {
    Write-Host "⚠️  Python venv not found, using system Python" -ForegroundColor Yellow
    $PythonExe = "python"
}

# Build command
$cmd = @($PythonExe, $Script, "--check-interval", $CheckInterval)

if ($DryRun) {
    $cmd += "--dry-run"
}

if ($AutoExecute) {
    $cmd += "--auto-execute"
}

if ($Once) {
    $cmd += "--once"
}

# Run
Write-Host "🎭 Starting Emotion-Triggered Stabilizer..." -ForegroundColor Cyan
Write-Host "   Interval: $CheckInterval seconds" -ForegroundColor Gray
Write-Host "   DryRun: $DryRun" -ForegroundColor Gray
Write-Host "   AutoExecute: $AutoExecute" -ForegroundColor Gray
Write-Host ""

& $cmd[0] $cmd[1..($cmd.Length - 1)]

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Stabilizer failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "✅ Stabilizer completed" -ForegroundColor Green
