# Realtime Resonance Bridge - PowerShell Runner
# 목적: Ledger 메트릭 → Resonance 시뮬레이션 실시간 연동

param(
    [int]$WindowHours = 24,
    [int]$MinEvents = 10,
    [string]$Output = "$PSScriptRoot\..\outputs\realtime_resonance_latest.json",
    [switch]$OpenJson,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Realtime Resonance Bridge - Ledger to Resonance Integration

Usage:
  scripts\run_realtime_resonance.ps1 [options]

Options:
  -WindowHours <int>   Time window for event loading (default: 24)
  -MinEvents <int>     Minimum events required (default: 10)
  -Output <path>       Output JSON path
  -OpenJson            Open result JSON in VS Code
  -Help                Show this help

Examples:
  # 기본 실행 (24시간 윈도우)
  scripts\run_realtime_resonance.ps1

  # 12시간 윈도우로 실행 후 결과 열기
  scripts\run_realtime_resonance.ps1 -WindowHours 12 -OpenJson

  # 최소 50 이벤트 요구
  scripts\run_realtime_resonance.ps1 -MinEvents 50

Exit Code:
  0 = Success
  1 = Failure
"@
    exit 0
}

$ErrorActionPreference = "Stop"

# 작업 공간 루트
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

# Python 실행 파일 찾기
$PythonExe = $null
if (Test-Path "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe") {
    $PythonExe = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
}
elseif (Test-Path "$WorkspaceRoot\.venv\Scripts\python.exe") {
    $PythonExe = "$WorkspaceRoot\.venv\Scripts\python.exe"
}
else {
    $PythonExe = "python"
}

Write-Host "=== Realtime Resonance Bridge ===" -ForegroundColor Cyan
Write-Host "Window: $WindowHours hours" -ForegroundColor Gray
Write-Host "Min Events: $MinEvents" -ForegroundColor Gray
Write-Host "Output: $Output" -ForegroundColor Gray
Write-Host ""

# Python 스크립트 실행
$BridgeScript = "$PSScriptRoot\realtime_resonance_bridge.py"
$LedgerPath = "$WorkspaceRoot\fdo_agi_repo\memory\resonance_ledger.jsonl"

& $PythonExe $BridgeScript `
    --ledger $LedgerPath `
    --window-hours $WindowHours `
    --min-events $MinEvents `
    --output $Output

$ExitCode = $LASTEXITCODE

if ($ExitCode -eq 0) {
    Write-Host ""
    Write-Host "✓ Bridge completed successfully" -ForegroundColor Green
    
    if ($OpenJson -and (Test-Path $Output)) {
        Write-Host "Opening result: $Output" -ForegroundColor Gray
        code $Output
    }
}
else {
    Write-Host ""
    Write-Host "✗ Bridge failed (exit: $ExitCode)" -ForegroundColor Red
}

exit $ExitCode
