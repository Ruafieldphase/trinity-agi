#requires -Version 5.1
# Flow Observer Validation Scheduler
# 30분 후 자동으로 Flow Observer를 실행하여 실제 데이터 검증
#
# Usage:
#   powershell -File scripts/schedule_flow_validation.ps1

param(
    [int]$DelayMinutes = 30,
    [switch]$OpenReport
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$WorkspaceRoot = Split-Path $PSScriptRoot -Parent

Write-Host "🌊 Flow Observer Validation Scheduler" -ForegroundColor Cyan
Write-Host ""
Write-Host "⏰ Scheduling validation in $DelayMinutes minutes..." -ForegroundColor Yellow

# Python 경로 찾기
$PythonPath = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $PythonPath)) {
    $PythonPath = "python"
}

$FlowObserverScript = "$WorkspaceRoot\fdo_agi_repo\copilot\flow_observer_integration.py"

# 백그라운드 작업 생성
$JobScript = {
    param($Minutes, $PythonExe, $Script, $OpenRpt)
    
    Start-Sleep -Seconds ($Minutes * 60)
    
    Write-Host ""
    Write-Host "🌊 Running Flow Observer Validation..." -ForegroundColor Cyan
    Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
    Write-Host ""
    
    & $PythonExe $Script
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Validation complete!" -ForegroundColor Green
        
        if ($OpenRpt) {
            $ReportPath = Join-Path (Split-Path $Script -Parent) "..\..\outputs\flow_observer_report_latest.json"
            if (Test-Path -LiteralPath $ReportPath) {
                Start-Process code $ReportPath
            }
        }
    } else {
        Write-Host ""
        Write-Host "❌ Validation failed!" -ForegroundColor Red
    }
}

$Job = Start-Job -ScriptBlock $JobScript -ArgumentList $DelayMinutes, $PythonPath, $FlowObserverScript, $OpenReport.IsPresent

Write-Host "✅ Validation scheduled!" -ForegroundColor Green
Write-Host "   Job ID: $($Job.Id)" -ForegroundColor Gray
Write-Host "   Will run at: $((Get-Date).AddMinutes($DelayMinutes).ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Cyan
Write-Host "   - Check status: Get-Job -Id $($Job.Id)" -ForegroundColor Gray
Write-Host "   - View output:  Receive-Job -Id $($Job.Id) -Keep" -ForegroundColor Gray
Write-Host "   - Stop job:     Stop-Job -Id $($Job.Id); Remove-Job -Id $($Job.Id)" -ForegroundColor Gray
Write-Host ""
Write-Host "🌊 Flow Observer is monitoring your activity..." -ForegroundColor Cyan
Write-Host "   Continue working naturally for best results!" -ForegroundColor Gray
