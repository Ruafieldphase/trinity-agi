<#
.SYNOPSIS
    Flow Observer 데몬 상태 확인

.DESCRIPTION
    실행 중인 Flow Observer 데몬의 상태를 확인하고 최근 로그를 표시합니다.
#>

$ErrorActionPreference = 'Continue'
$workspaceRoot = Split-Path -Parent $PSScriptRoot
$logPath = Join-Path $workspaceRoot "outputs\flow_observer_daemon.log"

Write-Host "🔍 Flow Observer Daemon Status" -ForegroundColor Cyan
Write-Host ""

# Job 상태 확인
$mainJob = Get-Job -Name "FlowObserverDaemon" -ErrorAction SilentlyContinue
$telemetryJob = Get-Job -Name "FlowTelemetry" -ErrorAction SilentlyContinue

if ($mainJob) {
    Write-Host "✅ Main Daemon:" -ForegroundColor Green
    $mainJob | Format-List Id, Name, State, PSBeginTime, PSEndTime
    
    # 최근 출력
    Write-Host "📋 Recent Output:" -ForegroundColor Cyan
    $output = Receive-Job -Name FlowObserverDaemon -Keep
    if ($output) {
        $output | Select-Object -Last 10 | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
    }
    else {
        Write-Host "   (No output yet)" -ForegroundColor Gray
    }
    Write-Host ""
}
else {
    Write-Host "❌ Main Daemon: Not running" -ForegroundColor Red
    Write-Host ""
}

if ($telemetryJob) {
    Write-Host "✅ Telemetry Collector:" -ForegroundColor Green
    $telemetryJob | Format-List Id, Name, State, PSBeginTime
}
else {
    Write-Host "❌ Telemetry Collector: Not running" -ForegroundColor Red
}

Write-Host ""

# 로그 파일 확인
if (Test-Path $logPath) {
    Write-Host "📄 Recent Log Entries:" -ForegroundColor Cyan
    $logContent = Get-Content $logPath -Tail 15 -ErrorAction SilentlyContinue
    
    foreach ($line in $logContent) {
        $color = "Gray"
        if ($line -match '\[ERROR\]') { $color = "Red" }
        elseif ($line -match '\[ALERT\]') { $color = "Yellow" }
        elseif ($line -match '\[WARN\]') { $color = "DarkYellow" }
        
        Write-Host "   $line" -ForegroundColor $color
    }
    
    Write-Host ""
    Write-Host "📁 Full log: $logPath" -ForegroundColor Gray
}
else {
    Write-Host "⚠️ No log file found" -ForegroundColor Yellow
}

Write-Host ""

# 최근 리포트 확인
$reportPath = Join-Path $workspaceRoot "outputs\flow_observer_report_latest.json"
if (Test-Path $reportPath) {
    $report = Get-Content $reportPath -Raw | ConvertFrom-Json
    
    Write-Host "📊 Latest Flow Report:" -ForegroundColor Cyan
    Write-Host "   Generated: $($report.generated_at)" -ForegroundColor Gray
    Write-Host "   Current State: $($report.current_state.state)" -ForegroundColor Gray
    Write-Host "   Confidence: $($report.current_state.confidence)" -ForegroundColor Gray
    Write-Host "   Flow Quality: $($report.flow_quality)" -ForegroundColor Gray
    Write-Host "   Flow Sessions: $($report.activity_summary.flow_sessions)" -ForegroundColor Gray
    Write-Host "   Total Flow Time: $($report.activity_summary.total_flow_minutes) min" -ForegroundColor Gray
}
else {
    Write-Host "⚠️ No report generated yet" -ForegroundColor Yellow
}
