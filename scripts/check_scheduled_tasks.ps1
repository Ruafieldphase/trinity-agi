# Check_scheduled_tasks.ps1
# List all scheduled tasks related to Ion, Core, Monitor, Canary

$tasks = Get-ScheduledTask | Where-Object { 
    $_.TaskName -match 'Ion|Core|Monitor|Canary|Inbox|Watcher' 
}

if ($tasks) {
    Write-Host "Found scheduled tasks:" -ForegroundColor Cyan
    $tasks | Select-Object TaskName, State, TaskPath | Format-Table -AutoSize
}
else {
    Write-Host "No matching scheduled tasks found." -ForegroundColor Yellow
}

Write-Host "`nAll scheduled tasks in root:" -ForegroundColor Cyan
Get-ScheduledTask | Where-Object { $_.TaskPath -eq '\' } | Select-Object TaskName, State | Format-Table -AutoSize