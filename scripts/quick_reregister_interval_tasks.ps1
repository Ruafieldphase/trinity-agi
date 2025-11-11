#requires -Version 5.1
<#
.SYNOPSIS
    Quick fix: Re-register 3 main interval tasks (5min, 30sec)
.DESCRIPTION
    Re-registers only the main interval tasks that show windows every 5 minutes
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Check admin rights
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (!$isAdmin) {
    Write-Host "`n⚠️  Administrator rights required for task registration" -ForegroundColor Yellow
    Write-Host "`n💡 Quick solution:" -ForegroundColor Cyan
    Write-Host "   Right-click PowerShell → Run as Administrator" -ForegroundColor Gray
    Write-Host "   Then run: cd C:\workspace\agi; .\scripts\quick_reregister_interval_tasks.ps1`n" -ForegroundColor Gray
    
    # Open admin prompt with the command
    $command = "cd C:\workspace\agi; .\scripts\quick_reregister_interval_tasks.ps1; pause"
    Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command `"$command`""
    
    Write-Host "   🚀 Admin PowerShell opened. Check that window!`n" -ForegroundColor Green
    exit 0
}

$workspaceRoot = Split-Path -Parent $PSScriptRoot

Write-Host "`n╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Quick Re-register: 3 Main Interval Tasks        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Task 1: MonitoringCollector (5분)
Write-Host "🔄 Re-registering: MonitoringCollector (5min)" -ForegroundColor Cyan
try {
    & "$workspaceRoot\scripts\register_monitoring_collector_task.ps1" -Register -IntervalMinutes 5
    Write-Host "   ✅ SUCCESS`n" -ForegroundColor Green
}
catch {
    Write-Host "   ❌ FAILED: $($_.Exception.Message)`n" -ForegroundColor Red
}

# Task 2: StreamObserverTelemetry (logon)
Write-Host "🔄 Re-registering: StreamObserverTelemetry" -ForegroundColor Cyan
try {
    & "$workspaceRoot\scripts\register_observer_telemetry_task.ps1" -Register
    Write-Host "   ✅ SUCCESS`n" -ForegroundColor Green
}
catch {
    Write-Host "   ❌ FAILED: $($_.Exception.Message)`n" -ForegroundColor Red
}

# Task 3: MetaObserver (30초)
Write-Host "🔄 Re-registering: MetaObserver (30sec)" -ForegroundColor Cyan
try {
    & "$workspaceRoot\scripts\register_meta_observer_task.ps1" -Register
    Write-Host "   ✅ SUCCESS`n" -ForegroundColor Green
}
catch {
    Write-Host "   ❌ FAILED: $($_.Exception.Message)`n" -ForegroundColor Red
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "`n✨ Re-registration complete!" -ForegroundColor Green
Write-Host "`n💡 What changed:" -ForegroundColor Cyan
Write-Host "   • All tasks now run with -WindowStyle Hidden" -ForegroundColor Gray
Write-Host "   • Task Scheduler will hide them properly" -ForegroundColor Gray
Write-Host "`n🧪 Test:" -ForegroundColor Cyan
Write-Host "   Wait 5 minutes and verify no windows appear" -ForegroundColor Gray
Write-Host "`n📊 Check status:" -ForegroundColor Cyan
Write-Host "   Get-ScheduledTask | Where-Object State -eq 'Running'`n" -ForegroundColor Gray
