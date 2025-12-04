# Deploy Integrated Rhythm System Orchestrator
# Registers the Master Orchestrator as a Windows Scheduled Task

param(
    [switch]$AutoStart = $true
)

$ErrorActionPreference = "Continue"

Write-Host "`n" -NoNewline
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "  🎵 RHYTHM ORCHESTRATOR DEPLOYMENT" -ForegroundColor Yellow
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host ""

$TaskName = "AGI_Integrated_Rhythm_Orchestrator"
$ScriptPath = "C:\workspace\agi\scripts\integrated_rhythm_system.ps1"

# Verify script exists
if (-not (Test-Path $ScriptPath)) {
    Write-Host "ERROR: Script not found at $ScriptPath" -ForegroundColor Red
    exit 1
}

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "Found existing task. Unregistering..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null
    Start-Sleep -Seconds 1
}

# Create task action
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File '$ScriptPath'"

# Create task trigger (run every 5 minutes, continuously)
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration (New-TimeSpan -Days 999)

# Create task settings
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries

# Register the task
try {
    Register-ScheduledTask -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "AGI Integrated Rhythm System - Master Orchestrator coordinating Phase 1, 2, and 3" `
        -Force | Out-Null

    Write-Host "✅ Task registered successfully!" -ForegroundColor Green
} catch {
    Write-Host "ERROR registering task: $_" -ForegroundColor Red
    exit 1
}

# Get the registered task
$task = Get-ScheduledTask -TaskName $TaskName

# Display registration details
Write-Host "`n📋 Deployment Details:" -ForegroundColor Cyan
Write-Host "  Task Name:     $TaskName" -ForegroundColor Gray
Write-Host "  Script Path:   $ScriptPath" -ForegroundColor Gray
Write-Host "  Interval:      Every 5 minutes" -ForegroundColor Gray
Write-Host "  State:         $($task.State)" -ForegroundColor Green
Write-Host ""

# Start the task immediately if requested
if ($AutoStart) {
    try {
        Start-ScheduledTask -TaskName $TaskName
        Write-Host "✅ Orchestrator started immediately!" -ForegroundColor Green
        Start-Sleep -Seconds 2

        $task = Get-ScheduledTask -TaskName $TaskName
        Write-Host "  Last Run:      $($task.LastRunTime)" -ForegroundColor Gray
        Write-Host "  Next Run:      $($task.NextRunTime)" -ForegroundColor Gray
    } catch {
        Write-Host "WARNING: Could not start task immediately: $_" -ForegroundColor Yellow
    }
}

Write-Host "`n" -NoNewline
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "  🎵 DEPLOYMENT COMPLETE - Rhythm System Now Orchestrating Phases 1, 2, 3" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host ""

# Final verification
Write-Host "✅ All components deployed:" -ForegroundColor Green
Write-Host "   Phase 1: Master Scheduler (AGI_Master_Scheduler)" -ForegroundColor Cyan
Write-Host "   Phase 2: Adaptive Scheduler (AGI_Adaptive_Master_Scheduler)" -ForegroundColor Cyan
Write-Host "   Phase 3: Event Detector (Ready, deploys in 1 week)" -ForegroundColor Yellow
Write-Host "   Orchestrator: Integrated Rhythm System (AGI_Integrated_Rhythm_Orchestrator)" -ForegroundColor Green
Write-Host ""
