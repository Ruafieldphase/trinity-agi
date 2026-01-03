#Requires -Version 5.1
#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Quick fix for StreamObserverTelemetry - re-register with updated script
#>


. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot
$taskName = 'StreamObserverTelemetry'
$workspaceRoot = "$WorkspaceRoot"
$registerScript = Join-Path $workspaceRoot 'scripts\register_observer_telemetry_task.ps1'

Write-Host "🔧 Re-registering $taskName..." -ForegroundColor Cyan

# First unregister (need admin)
try {
    $existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "   🗑️  Removing old task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
        Write-Host "   ✅ Old task removed" -ForegroundColor Green
    }
}
catch {
    Write-Host "   ❌ Failed to remove: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Re-register
Write-Host "   📝 Registering with updated script..." -ForegroundColor Cyan
try {
    & $registerScript -Register
    Write-Host "`n✅ StreamObserverTelemetry re-registered successfully!" -ForegroundColor Green
    Write-Host "   The new -WindowStyle Hidden fix is now active." -ForegroundColor Gray
}
catch {
    Write-Host "   ❌ Failed to register: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}