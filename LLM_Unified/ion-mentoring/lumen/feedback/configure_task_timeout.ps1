# configure_task_timeout.ps1
# 예약 작업에 실행 시간 제한 추가

param(
    [Parameter(Mandatory = $false)]
    [string]$TaskName = "LumenFeedbackEmitter",
    
    [Parameter(Mandatory = $false)]
    [int]$TimeoutMinutes = 4,
    
    [Parameter(Mandatory = $false)]
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "=== Configure Task Timeout ===" -ForegroundColor Cyan
Write-Host "Task: $TaskName"
Write-Host "Timeout: $TimeoutMinutes minutes"
Write-Host ""

# Get existing task
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) {
    Write-Host "ERROR: Task '$TaskName' not found" -ForegroundColor Red
    exit 1
}

Write-Host "Current Configuration:" -ForegroundColor Yellow
Write-Host "  State: $($task.State)"
Write-Host "  Actions: $($task.Actions.Count)"

# Get current settings
$currentSettings = $task.Settings
Write-Host "  Current ExecutionTimeLimit: $($currentSettings.ExecutionTimeLimit)"
Write-Host "  Current MultipleInstances: $($currentSettings.MultipleInstances)"
Write-Host "  Current AllowHardTerminate: $($currentSettings.AllowHardTerminate)"
Write-Host "  Current StopIfGoingOnBatteries: $($currentSettings.StopIfGoingOnBatteries)"
Write-Host "  Current DisallowStartIfOnBatteries: $($currentSettings.DisallowStartIfOnBatteries)"
Write-Host ""

# Create new settings
$newTimeLimit = "PT$($TimeoutMinutes)M"

Write-Host "Proposed Changes:" -ForegroundColor Yellow
Write-Host "  ExecutionTimeLimit: $newTimeLimit (was: $($currentSettings.ExecutionTimeLimit))"
Write-Host "  MultipleInstances: IgnoreNew (was: $($currentSettings.MultipleInstances))"
Write-Host "  AllowHardTerminate: True (was: $($currentSettings.AllowHardTerminate))"
Write-Host "  StopIfGoingOnBatteries: False (was: $($currentSettings.StopIfGoingOnBatteries))"
Write-Host "  DisallowStartIfOnBatteries: False (was: $($currentSettings.DisallowStartIfOnBatteries))"
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] Would update task settings" -ForegroundColor Cyan
    Write-Host "Run without -DryRun to apply changes" -ForegroundColor Gray
}
else {
    Write-Host "Applying changes..." -ForegroundColor Cyan
    
    # Create settings object (compatible with PowerShell 5.1)
    $settings = New-ScheduledTaskSettingsSet `
        -ExecutionTimeLimit (New-TimeSpan -Minutes $TimeoutMinutes) `
        -MultipleInstances IgnoreNew
    
    # Set additional properties
    $settings.AllowHardTerminate = $true
    $settings.StopIfGoingOnBatteries = $false
    $settings.DisallowStartIfOnBatteries = $false
    
    # Update task
    try {
        Set-ScheduledTask -TaskName $TaskName -Settings $settings | Out-Null
        Write-Host "SUCCESS: Task settings updated" -ForegroundColor Green
        
        # Verify
        $updatedTask = Get-ScheduledTask -TaskName $TaskName
        $updatedSettings = $updatedTask.Settings
        
        Write-Host ""
        Write-Host "Verification:" -ForegroundColor Yellow
        Write-Host "  ExecutionTimeLimit: $($updatedSettings.ExecutionTimeLimit)"
        Write-Host "  MultipleInstances: $($updatedSettings.MultipleInstances)"
        Write-Host "  AllowHardTerminate: $($updatedSettings.AllowHardTerminate)"
        Write-Host "  StopIfGoingOnBatteries: $($updatedSettings.StopIfGoingOnBatteries)"
        Write-Host "  DisallowStartIfOnBatteries: $($updatedSettings.DisallowStartIfOnBatteries)"
        
        Write-Host ""
        Write-Host "Benefits:" -ForegroundColor Cyan
        Write-Host "  ✓ Task will auto-terminate after $TimeoutMinutes minutes"
        Write-Host "  ✓ Prevents task overlap (no more error 267009)"
        Write-Host "  ✓ Ensures next scheduled run can start on time"
        Write-Host "  ✓ Works on laptop/battery power"
        
    }
    catch {
        Write-Host "ERROR: Failed to update task" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "=== Configuration Complete ===" -ForegroundColor Cyan
