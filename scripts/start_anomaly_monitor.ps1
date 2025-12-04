<#
.SYNOPSIS
Anomaly Detection Monitor 시작

.DESCRIPTION
시스템 메트릭을 주기적으로 수집하고 Anomaly Detection을 수행합니다.
이상 패턴이 감지되면 Alert를 생성합니다.

.PARAMETER IntervalSeconds
모니터링 주기 (초, 기본값: 60)

.PARAMETER KillExisting
기존 Anomaly Monitor 프로세스를 종료하고 재시작

.PARAMETER DryRun
실제 Alert 생성 없이 Dry-run 모드로 실행

.EXAMPLE
.\start_anomaly_monitor.ps1 -IntervalSeconds 60

.EXAMPLE
.\start_anomaly_monitor.ps1 -KillExisting -IntervalSeconds 120

.NOTES
Author: GitHub Copilot
Created: 2025-11-03
Phase: 7 (System Stabilization)
#>

param(
    [int]$IntervalSeconds = 60,
    [switch]$KillExisting,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$ws = $PSScriptRoot | Split-Path -Parent

# 1. 기존 프로세스 종료 (선택적)
if ($KillExisting) {
    Write-Host "🛑 Stopping existing Anomaly Monitor..." -ForegroundColor Yellow
    
    Get-Process -Name "python", "py" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*anomaly_detector.py*"
    } | ForEach-Object {
        Write-Host "   Killing PID $($_.Id)..." -ForegroundColor Yellow
        Stop-Process -Id $_.Id -Force
    }
    
    Start-Sleep -Seconds 2
}

# 2. Python 실행 파일 찾기
$pythonExe = $null

# 우선순위: fdo_agi_repo/.venv > LLM_Unified/.venv > system python
$venvPaths = @(
    "$ws\fdo_agi_repo\.venv\Scripts\python.exe",
    "$ws\LLM_Unified\.venv\Scripts\python.exe"
)

foreach ($path in $venvPaths) {
    if (Test-Path -LiteralPath $path) {
        $pythonExe = $path
        break
    }
}

if (-not $pythonExe) {
    # Fallback to system python
    $pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $pythonExe) {
        Write-Host "❌ Python not found. Please install Python or activate venv." -ForegroundColor Red
        exit 1
    }
}

Write-Host "🐍 Using Python: $pythonExe" -ForegroundColor Cyan

# 3. Baseline 확인
$baselinePath = "$ws\outputs\anomaly_baseline.json"
if (-not (Test-Path -LiteralPath $baselinePath)) {
    Write-Host "⚠️  Baseline not found. Creating now..." -ForegroundColor Yellow
    & $pythonExe "$ws\scripts\collect_anomaly_baseline.py" --days 7
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create baseline." -ForegroundColor Red
        exit 1
    }
}

# 4. Anomaly Detector 시작
Write-Host "`n🔍 Starting Anomaly Detection Monitor..." -ForegroundColor Green
Write-Host "   Interval: $IntervalSeconds seconds" -ForegroundColor Cyan
Write-Host "   Baseline: $baselinePath" -ForegroundColor Cyan

$scriptPath = "$ws\scripts\anomaly_detector.py"

if (-not (Test-Path -LiteralPath $scriptPath)) {
    Write-Host "❌ anomaly_detector.py not found. Please create it first." -ForegroundColor Red
    exit 1
}

# Build command
$cmd = @(
    $pythonExe,
    $scriptPath,
    "--interval", $IntervalSeconds.ToString(),
    "--baseline", $baselinePath
)

if ($DryRun) {
    $cmd += "--dry-run"
}

Write-Host "`n▶️  Command: $($cmd -join ' ')" -ForegroundColor Cyan
Write-Host "`n" + ("=" * 60) -ForegroundColor DarkGray
Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Yellow
Write-Host ("=" * 60) + "`n" -ForegroundColor DarkGray

# 5. 실행 (Foreground)
try {
    & $cmd[0] $cmd[1..($cmd.Length - 1)]
}
catch {
    Write-Host "❌ Anomaly Monitor failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Anomaly Monitor stopped." -ForegroundColor Green
exit 0
