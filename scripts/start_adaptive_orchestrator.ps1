#Requires -Version 5.1
<#
.SYNOPSIS
    Adaptive Rhythm Orchestrator - PowerShell Wrapper
    
.DESCRIPTION
    생명체처럼 리듬을 감지하고 자원을 재분배하는 메타층 관찰자.
    
    동작 원리:
    1. Rhythm Detector: 시스템 리듬 감지 (NORMAL/BUSY/EMERGENCY/LEARNING)
    2. Resource Allocator: 리듬에 맞는 자원 예산 계산
    3. System Applier: 실제 시스템에 예산 적용
    
.EXAMPLE
    # 한 번 실행
    .\start_adaptive_orchestrator.ps1 -Once
    
.EXAMPLE
    # 지속 실행 (10초 간격)
    .\start_adaptive_orchestrator.ps1 -IntervalSeconds 10
    
.EXAMPLE
    # 지속 실행 (5분간)
    .\start_adaptive_orchestrator.ps1 -IntervalSeconds 10 -DurationSeconds 300
    
.EXAMPLE
    # 백그라운드 실행
    .\start_adaptive_orchestrator.ps1 -Background
#>

param(
    [Parameter(HelpMessage = "한 번만 실행")]
    [switch]$Once,
    
    [Parameter(HelpMessage = "지속 실행 시 간격 (초)")]
    [int]$IntervalSeconds = 10,
    
    [Parameter(HelpMessage = "지속 실행 시 최대 시간 (초)")]
    [int]$DurationSeconds = 0,
    
    [Parameter(HelpMessage = "백그라운드 실행")]
    [switch]$Background,
    
    [Parameter(HelpMessage = "강제로 특정 모드 사용 (테스트용)")]
    [ValidateSet("", "NORMAL", "BUSY", "EMERGENCY", "LEARNING")]
    [string]$ForceMode = "",
    
    [Parameter(HelpMessage = "상세 로그 출력")]
    [switch]$VerboseLog
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$RepoRoot = Join-Path $WorkspaceRoot "fdo_agi_repo"
$OrchestratorScript = Join-Path $RepoRoot "orchestrator\adaptive_orchestrator.py"
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"

# Python 실행 파일 찾기
if (Test-Path -LiteralPath $VenvPython) {
    $Python = $VenvPython
}
else {
    $Python = "python"
}

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "🎵 Adaptive Rhythm Orchestrator" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# 인수 구성
$PythonArgs = @()

if ($Once) {
    Write-Host "Mode: One-shot execution" -ForegroundColor Yellow
    $PythonArgs += "--once"
}
else {
    Write-Host "Mode: Continuous execution" -ForegroundColor Yellow
    Write-Host "  Interval: $IntervalSeconds seconds" -ForegroundColor Gray
    $PythonArgs += "--interval", $IntervalSeconds
    
    if ($DurationSeconds -gt 0) {
        Write-Host "  Duration: $DurationSeconds seconds" -ForegroundColor Gray
        $PythonArgs += "--duration", $DurationSeconds
    }
}

if ($ForceMode) {
    Write-Host "⚠️  Force Mode: $ForceMode (Testing only!)" -ForegroundColor Magenta
    # 강제 모드는 별도 스크립트로 처리
}

Write-Host ""

# 백그라운드 실행
if ($Background) {
    Write-Host "🚀 Starting in background..." -ForegroundColor Green
    
    $Job = Start-Job -ScriptBlock {
        param($Python, $Script, $PythonArgs)
        & $Python $Script @PythonArgs
    } -ArgumentList $Python, $OrchestratorScript, $PythonArgs -Name "AdaptiveOrchestrator"
    
    Write-Host "✅ Background job started: $($Job.Id)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Cyan
    Write-Host "  Get-Job                  # Check job status" -ForegroundColor Gray
    Write-Host "  Receive-Job -Id $($Job.Id) -Keep  # View output" -ForegroundColor Gray
    Write-Host "  Stop-Job -Id $($Job.Id)          # Stop job" -ForegroundColor Gray
    Write-Host "  Remove-Job -Id $($Job.Id)        # Remove job" -ForegroundColor Gray
    Write-Host ""
    
    exit 0
}

# 포그라운드 실행
try {
    & $Python $OrchestratorScript @PythonArgs
    
    if ($LASTEXITCODE -ne 0) {
        throw "Orchestrator failed with exit code: $LASTEXITCODE"
    }
    
    Write-Host ""
    Write-Host "=" * 70 -ForegroundColor Green
    Write-Host "✅ Adaptive Orchestrator completed successfully" -ForegroundColor Green
    Write-Host "=" * 70 -ForegroundColor Green
    Write-Host ""
    
    # 최신 상태 파일 보기
    $RhythmStateFile = Join-Path $RepoRoot "outputs\rhythm_state_latest.json"
    $BudgetFile = Join-Path $RepoRoot "outputs\resource_budget_latest.json"
    
    if (Test-Path -LiteralPath $RhythmStateFile) {
        Write-Host "📊 Current Rhythm State:" -ForegroundColor Cyan
        $RhythmState = Get-Content -LiteralPath $RhythmStateFile -Raw -Encoding UTF8 | ConvertFrom-Json
        Write-Host "   Mode: $($RhythmState.mode)" -ForegroundColor Yellow
        Write-Host "   Confidence: $([math]::Round($RhythmState.confidence * 100))%" -ForegroundColor Gray
        Write-Host "   Reason: $($RhythmState.reason)" -ForegroundColor Gray
        Write-Host ""
    }
    
    if (Test-Path -LiteralPath $BudgetFile) {
        Write-Host "💰 Current Resource Budget:" -ForegroundColor Cyan
        $Budget = Get-Content -LiteralPath $BudgetFile -Raw -Encoding UTF8 | ConvertFrom-Json
        Write-Host "   Budget Usage: $($Budget.budget_usage_percent)%" -ForegroundColor Yellow
        Write-Host "   Target Latency: $($Budget.target_latency_sec)s" -ForegroundColor Gray
        Write-Host "   Direct Mode: $(if ($Budget.direct_mode) { '✅ YES' } else { '❌ NO' })" -ForegroundColor Gray
        Write-Host ""
    }
    
}
catch {
    Write-Host ""
    Write-Host "=" * 70 -ForegroundColor Red
    Write-Host "❌ Error running Adaptive Orchestrator" -ForegroundColor Red
    Write-Host "=" * 70 -ForegroundColor Red
    Write-Host ""
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    exit 1
}