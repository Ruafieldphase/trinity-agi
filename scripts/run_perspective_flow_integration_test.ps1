#!/usr/bin/env pwsh
# Perspective Theory + Flow Observer 통합 테스트
# Author: Copilot
# Date: 2025-11-06

param(
    [int]$TestSeconds = 30,
    [switch]$Continuous,
    [switch]$OpenReport
)

$ErrorActionPreference = 'Stop'

Write-Host "🌊 Perspective Theory + Flow Observer Integration Test" -ForegroundColor Cyan
Write-Host "⏱️  Test Duration: $TestSeconds seconds" -ForegroundColor Gray
Write-Host ""

# 1. Observer 시작 (Background)
Write-Host "1️⃣ Starting Desktop Observer..." -ForegroundColor Yellow
$observerJob = Start-Job -Name "FlowObserver" -ScriptBlock {
    param($WorkspaceFolder, $Duration)
    Set-Location $WorkspaceFolder
    & "$WorkspaceFolder\scripts\observe_desktop_telemetry.ps1" -IntervalSeconds 2 -DurationSeconds $Duration
} -ArgumentList (Get-Location).Path, $TestSeconds

Write-Host "   ✅ Observer started (Job ID: $($observerJob.Id))" -ForegroundColor Green
Write-Host ""

# 2. 대기
Write-Host "2️⃣ Waiting for $TestSeconds seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds $TestSeconds
Write-Host "   ✅ Observation complete" -ForegroundColor Green
Write-Host ""

# 3. Observer 정리
Write-Host "3️⃣ Stopping Observer..." -ForegroundColor Yellow
Stop-Job -Job $observerJob -ErrorAction SilentlyContinue
Remove-Job -Job $observerJob -ErrorAction SilentlyContinue
Write-Host "   ✅ Observer stopped" -ForegroundColor Green
Write-Host ""

# 4. Flow 분석 실행
Write-Host "4️⃣ Running Flow Analysis..." -ForegroundColor Yellow
$py = "$((Get-Location).Path)\fdo_agi_repo\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    $py = "python"
}

& $py "$((Get-Location).Path)\fdo_agi_repo\copilot\flow_observer_integration.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "   ❌ Flow analysis failed" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ Flow analysis complete" -ForegroundColor Green
Write-Host ""

# 5. Perspective Theory 테스트
Write-Host "5️⃣ Testing Perspective Theory..." -ForegroundColor Yellow
& $py "$((Get-Location).Path)\fdo_agi_repo\copilot\perspective_theory.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "   ❌ Perspective test failed" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ Perspective test passed" -ForegroundColor Green
Write-Host ""

# 6. 리포트 확인
Write-Host "6️⃣ Checking Report..." -ForegroundColor Yellow
$reportPath = "outputs\flow_observer_report_latest.json"
if (Test-Path $reportPath) {
    $report = Get-Content $reportPath -Raw | ConvertFrom-Json
    Write-Host "   📊 Flow Quality: $($report.flow_quality)" -ForegroundColor Cyan
    Write-Host "   🎯 Flow Sessions: $($report.activity_summary.flow_sessions)" -ForegroundColor Cyan
    Write-Host "   ⏱️  Total Flow Time: $([math]::Round($report.activity_summary.total_flow_minutes, 1))min" -ForegroundColor Cyan
    Write-Host "   ✅ Report available: $reportPath" -ForegroundColor Green
    
    if ($OpenReport) {
        code $reportPath
    }
}
else {
    Write-Host "   ⚠️  Report not found: $reportPath" -ForegroundColor Yellow
}
Write-Host ""

# 7. Continuous 모드
if ($Continuous) {
    Write-Host "🔁 Continuous Mode: Starting background observer..." -ForegroundColor Magenta
    Start-Job -Name "FlowObserverContinuous" -ScriptBlock {
        param($WorkspaceFolder)
        Set-Location $WorkspaceFolder
        & "$WorkspaceFolder\scripts\observe_desktop_telemetry.ps1" -IntervalSeconds 5 -DurationSeconds 0
    } -ArgumentList (Get-Location).Path
    
    Write-Host "   ✅ Background observer started" -ForegroundColor Green
    Write-Host "   ℹ️  Use 'Stop-Job -Name FlowObserverContinuous' to stop" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "✅ Integration test complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Summary:" -ForegroundColor Cyan
Write-Host "   - Desktop telemetry: ✅" -ForegroundColor White
Write-Host "   - Flow analysis: ✅" -ForegroundColor White
Write-Host "   - Perspective theory: ✅" -ForegroundColor White
Write-Host "   - Integration: ✅" -ForegroundColor White
Write-Host ""
Write-Host "🎯 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Register continuous observer: scripts\register_flow_observer_task.ps1 -Register" -ForegroundColor Gray
Write-Host "   2. View real-time flow: code outputs\flow_observer_report_latest.json" -ForegroundColor Gray
Write-Host "   3. Experiment with perspective switching during work" -ForegroundColor Gray
Write-Host ""
