# Setup AGI Daily Health Check Scheduled Task

$action = New-ScheduledTaskAction -Execute "D:\nas_backup\fdo_agi_repo\scripts\run_daily_health_check.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable

Register-ScheduledTask `
    -TaskName "AGI_Daily_Health_Check" `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description "Daily health check for AGI system - monitors corrections, replan rate, and quality metrics" `
    -Force

Write-Host "Scheduled task 'AGI_Daily_Health_Check' registered successfully!"
Write-Host "Task will run daily at 9:00 AM"
Write-Host ""
Write-Host "To test immediately, run:"
Write-Host "Start-ScheduledTask -TaskName 'AGI_Daily_Health_Check'"
