<#
.SYNOPSIS
    Flow Observer 데몬 중지

.DESCRIPTION
    실행 중인 Flow Observer 데몬을 안전하게 종료합니다.
#>

$ErrorActionPreference = 'Continue'

Write-Host "🛑 Stopping Flow Observer Daemon..." -ForegroundColor Cyan

# Main Job 중지
$mainJob = Get-Job -Name "FlowObserverDaemon" -ErrorAction SilentlyContinue
if ($mainJob) {
    Write-Host "   Stopping main daemon (Job ID: $($mainJob.Id))..." -ForegroundColor Gray
    Stop-Job -Name FlowObserverDaemon -ErrorAction SilentlyContinue
    Remove-Job -Name FlowObserverDaemon -ErrorAction SilentlyContinue
    Write-Host "✅ Main daemon stopped" -ForegroundColor Green
}
else {
    Write-Host "⚠️ Main daemon not found" -ForegroundColor Yellow
}

# Telemetry Job 중지
$telemetryJob = Get-Job -Name "FlowTelemetry" -ErrorAction SilentlyContinue
if ($telemetryJob) {
    Write-Host "   Stopping telemetry collector (Job ID: $($telemetryJob.Id))..." -ForegroundColor Gray
    Stop-Job -Name FlowTelemetry -ErrorAction SilentlyContinue
    Remove-Job -Name FlowTelemetry -ErrorAction SilentlyContinue
    Write-Host "✅ Telemetry collector stopped" -ForegroundColor Green
}
else {
    Write-Host "⚠️ Telemetry collector not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Flow Observer Daemon stopped" -ForegroundColor Green
