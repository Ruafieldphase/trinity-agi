#Requires -Version 5.1
<#
.SYNOPSIS
    Gateway Resonance Optimizer - Phase 8.5 최적화 실행

.DESCRIPTION
    역설적 공명(Paradoxical Resonance) 해결을 위한 3가지 최적화 전략 적용:
    1. 적응적 타임아웃 (시간대별 조정)
    2. 위상 동기화 스케줄러 (부하 기반)
    3. Off-peak 워밍업 (사전 로딩)

.PARAMETER DurationMinutes
    최적화 적용 시간 (분) - 기본값: 60

.PARAMETER DryRun
    드라이런 모드 (실제 변경 없이 시뮬레이션)

.PARAMETER ReportOnly
    현재 최적화 상태만 리포트

.EXAMPLE
    .\run_gateway_optimization.ps1 -DryRun
    
.EXAMPLE
    .\run_gateway_optimization.ps1 -DurationMinutes 120
#>

param(
    [int]$DurationMinutes = 60,
    [switch]$DryRun,
    [switch]$ReportOnly
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'

# 경로 설정
$WorkspaceRoot = $PSScriptRoot | Split-Path
$ScriptPath = Join-Path $WorkspaceRoot "fdo_agi_repo\scripts\optimize_gateway_resonance.py"
$ConfigPath = Join-Path $WorkspaceRoot "fdo_agi_repo\config\adaptive_gateway_config.json"
$VenvPython = Join-Path $WorkspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"

# Python 실행 파일 찾기
if (Test-Path $VenvPython) {
    $PythonExe = $VenvPython
}
else {
    $PythonExe = "python"
}

# 헤더
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  Gateway Resonance Optimizer - Phase 8.5" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 설정 확인
if (-not (Test-Path $ConfigPath)) {
    Write-Host "❌ Config file not found: $ConfigPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $ScriptPath)) {
    Write-Host "❌ Script not found: $ScriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "📋 Configuration:" -ForegroundColor White
Write-Host "  - Config: $ConfigPath" -ForegroundColor Gray
Write-Host "  - Python: $PythonExe" -ForegroundColor Gray
Write-Host "  - Duration: $DurationMinutes minutes" -ForegroundColor Gray
Write-Host "  - Mode: $(if ($DryRun) { 'DRY-RUN' } else { 'ACTIVE' })" -ForegroundColor $(if ($DryRun) { 'Yellow' } else { 'Green' })
Write-Host ""

# Python 인자 구성
$PythonArgs = @(
    $ScriptPath,
    "--config", $ConfigPath,
    "--duration", $DurationMinutes
)

if ($DryRun) {
    $PythonArgs += "--dry-run"
}

if ($ReportOnly) {
    $PythonArgs += "--report-only"
}

# 실행
Write-Host "🚀 Starting optimizer..." -ForegroundColor Cyan
Write-Host ""

try {
    & $PythonExe @PythonArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Optimization completed successfully" -ForegroundColor Green
        
        # 로그 파일 확인
        $LogFile = Join-Path $WorkspaceRoot "outputs\gateway_optimization_log.jsonl"
        if (Test-Path $LogFile) {
            $LogLines = (Get-Content $LogFile | Measure-Object -Line).Lines
            Write-Host "📊 Log entries: $LogLines" -ForegroundColor Cyan
            Write-Host "📁 Log file: $LogFile" -ForegroundColor Gray
        }
    }
    else {
        Write-Host ""
        Write-Host "❌ Optimization failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}
catch {
    Write-Host ""
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""