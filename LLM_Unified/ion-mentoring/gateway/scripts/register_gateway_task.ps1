<#
.SYNOPSIS
    Register Lumen Gateway as Windows Scheduled Task for auto-start
    
.DESCRIPTION
    Creates a scheduled task to automatically start Gateway services
    when the system boots or user logs on.
    
.PARAMETER TaskName
    Name of the scheduled task (default: LumenGatewayAutoStart)
    
.PARAMETER Trigger
    When to start the task: Startup, Logon, or Daily
    Default: Startup (recommended for production)
    
.PARAMETER RunAsUser
    User account to run the task (default: current user)
    Use "SYSTEM" for system-level service
    
.PARAMETER Force
    Overwrite existing task without confirmation
    
.EXAMPLE
    .\register_gateway_task.ps1
    Register task with default settings (Startup trigger)
    
.EXAMPLE
    .\register_gateway_task.ps1 -Trigger Logon -RunAsUser $env:USERNAME
    Register task to start at user logon
    
.EXAMPLE
    .\register_gateway_task.ps1 -Force
    Force overwrite existing task
#>

param(
    [string]$TaskName = "LumenGatewayAutoStart",
    [ValidateSet("Startup", "Logon", "Daily")]
    [string]$Trigger = "Startup",
    [string]$RunAsUser = $env:USERNAME,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Paths
$GatewayRoot = Split-Path -Parent $PSScriptRoot
$StartScript = Join-Path $GatewayRoot "scripts\start_gateway.ps1"

# Verify script exists
if (-not (Test-Path $StartScript)) {
    Write-Host "❌ Error: start_gateway.ps1 not found at: $StartScript" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Lumen Gateway Task Registration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "⚠️  Task '$TaskName' already exists" -ForegroundColor Yellow
    
    if (-not $Force) {
        $response = Read-Host "Do you want to overwrite it? (y/N)"
        if ($response -notmatch '^[Yy]') {
            Write-Host "❌ Registration cancelled" -ForegroundColor Red
            exit 0
        }
    }
    
    Write-Host "🗑️  Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Task action
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$StartScript`" -KillExisting" `
    -WorkingDirectory (Split-Path $StartScript)

# Task trigger based on parameter
switch ($Trigger) {
    "Startup" {
        $triggerObj = New-ScheduledTaskTrigger -AtStartup
        Write-Host "📅 Trigger: At system startup" -ForegroundColor Gray
    }
    "Logon" {
        $triggerObj = New-ScheduledTaskTrigger -AtLogOn -User $RunAsUser
        Write-Host "📅 Trigger: At user logon ($RunAsUser)" -ForegroundColor Gray
    }
    "Daily" {
        # Daily at 12:00 AM (health check)
        $triggerObj = New-ScheduledTaskTrigger -Daily -At "12:00AM"
        Write-Host "📅 Trigger: Daily at 12:00 AM" -ForegroundColor Gray
    }
}

# Task settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0)  # No time limit

# Task principal (run as user or SYSTEM)
if ($RunAsUser -eq "SYSTEM") {
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    Write-Host "👤 Run as: SYSTEM (service account)" -ForegroundColor Gray
}
else {
    $principal = New-ScheduledTaskPrincipal -UserId $RunAsUser -LogonType Interactive -RunLevel Highest
    Write-Host "👤 Run as: $RunAsUser (interactive)" -ForegroundColor Gray
}

# Register task
Write-Host ""
Write-Host "📝 Registering scheduled task..." -ForegroundColor Cyan

try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $triggerObj `
        -Settings $settings `
        -Principal $principal `
        -Description "Automatically start Lumen Gateway Collector and Exporter services" `
        -ErrorAction Stop | Out-Null
    
    Write-Host "✅ Task registered successfully!" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to register task: $_" -ForegroundColor Red
    exit 1
}

# Verify registration
Write-Host ""
Write-Host "🔍 Verifying task registration..." -ForegroundColor Cyan

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($task) {
    Write-Host "✅ Task verified" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name:        $($task.TaskName)" -ForegroundColor White
    Write-Host "  State:       $($task.State)" -ForegroundColor White
    Write-Host "  Author:      $($task.Author)" -ForegroundColor White
    Write-Host "  Description: $($task.Description)" -ForegroundColor White
    
    # Show triggers
    Write-Host ""
    Write-Host "Triggers:" -ForegroundColor Cyan
    foreach ($t in $task.Triggers) {
        Write-Host "  - $($t.GetType().Name): Enabled=$($t.Enabled)" -ForegroundColor White
    }
    
    # Show actions
    Write-Host ""
    Write-Host "Actions:" -ForegroundColor Cyan
    foreach ($a in $task.Actions) {
        Write-Host "  - Execute: $($a.Execute)" -ForegroundColor White
        Write-Host "    Arguments: $($a.Arguments)" -ForegroundColor White
    }
}
else {
    Write-Host "⚠️  Task verification failed (task not found)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Next Steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Test the task manually:" -ForegroundColor White
Write-Host "   Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Check task status:" -ForegroundColor White
Write-Host "   Get-ScheduledTask -TaskName '$TaskName' | Select-Object TaskName,State,LastRunTime,NextRunTime" -ForegroundColor Gray
Write-Host ""
Write-Host "3. View task history:" -ForegroundColor White
Write-Host "   Get-ScheduledTask -TaskName '$TaskName' | Get-ScheduledTaskInfo" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Disable task (if needed):" -ForegroundColor White
Write-Host "   Disable-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host ""
Write-Host "5. Remove task:" -ForegroundColor White
Write-Host "   Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor Gray
Write-Host ""
Write-Host "✅ Registration complete!" -ForegroundColor Green
Write-Host ""
