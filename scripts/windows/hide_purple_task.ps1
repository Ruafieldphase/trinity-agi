# Hide "Purple" Scheduled Task with Admin Rights
# Run this script as Administrator

$taskName = "Purple"

try {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
    $task.Settings.Hidden = $true
    $task | Set-ScheduledTask | Out-Null
    Write-Host "✅ Successfully hidden '$taskName' task" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run this script as Administrator:" -ForegroundColor Yellow
    Write-Host "Right-click → Run as administrator" -ForegroundColor Yellow
}

Read-Host "`nPress Enter to exit"
