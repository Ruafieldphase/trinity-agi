# Daily Briefing Scheduler
# Registers a scheduled task to generate daily briefing every morning

param(
    [switch]$Register,
    [switch]$Unregister,
    [string]$Time = "07:00"
)

$ErrorActionPreference = "Stop"

$TaskName = "AGI_Daily_Briefing"
$ScriptPath = "$PSScriptRoot\generate_daily_briefing.ps1"

if ($Unregister) {
    Write-Host "`nUnregistering daily briefing task...`n" -ForegroundColor Yellow
    
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "Task unregistered successfully!`n" -ForegroundColor Green
    }
    catch {
        Write-Host "Task not found or already unregistered.`n" -ForegroundColor Gray
    }
    
    exit 0
}

if ($Register) {
    Write-Host "`nRegistering daily briefing task...`n" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Gray
    
    # Check if task already exists
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "Task already exists. Unregistering...`n" -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # Create action
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument `
        "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`" -OpenReport"
    
    # Create trigger (daily at specified time)
    $trigger = New-ScheduledTaskTrigger -Daily -At $Time
    
    # Create settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false
    
    # Register task
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "Generate daily briefing for AGI systems" `
        -User $env:USERNAME `
        -RunLevel Highest
    
    Write-Host "`n" + ("=" * 60) -ForegroundColor Gray
    Write-Host "Daily briefing task registered successfully!`n" -ForegroundColor Green
    
    Write-Host "Configuration:" -ForegroundColor Cyan
    Write-Host "  Task Name:  $TaskName" -ForegroundColor Gray
    Write-Host "  Run Time:   $Time daily" -ForegroundColor Gray
    Write-Host "  Script:     $ScriptPath`n" -ForegroundColor Gray
    
    Write-Host "The briefing will be generated and opened automatically every day at $Time.`n" -ForegroundColor Yellow
    
    exit 0
}

# Status check (default)
Write-Host "`nDaily Briefing Scheduler Status`n" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($task) {
    Write-Host "Status: REGISTERED`n" -ForegroundColor Green
    
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name:       $($task.TaskName)" -ForegroundColor Gray
    Write-Host "  State:      $($task.State)" -ForegroundColor Gray
    Write-Host "  Trigger:    $($task.Triggers[0].StartBoundary)`n" -ForegroundColor Gray
    
    Write-Host "Actions:" -ForegroundColor Yellow
    Write-Host "  To unregister: .\register_daily_briefing.ps1 -Unregister`n" -ForegroundColor Gray
}
else {
    Write-Host "Status: NOT REGISTERED`n" -ForegroundColor Yellow
    
    Write-Host "To register:" -ForegroundColor Cyan
    Write-Host "  Default time (7:00 AM): .\register_daily_briefing.ps1 -Register" -ForegroundColor Gray
    Write-Host "  Custom time:            .\register_daily_briefing.ps1 -Register -Time `"08:30`"`n" -ForegroundColor Gray
}