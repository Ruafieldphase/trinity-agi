# Stop Auto Recovery System
Write-Host "`n" -NoNewline
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "`n  Stopping Auto Recovery System`n" -ForegroundColor Yellow
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "`n"

$processes = Get-Process -Name "pwsh", "powershell" -ErrorAction SilentlyContinue | 
Where-Object { $_.CommandLine -like "*auto_recovery_system.ps1*" }

if ($processes) {
    Write-Host "Found $($processes.Count) recovery process(es)" -ForegroundColor Cyan
    $processes | Stop-Process -Force
    Write-Host "  All processes stopped" -ForegroundColor Green
}
else {
    Write-Host "  No recovery processes found" -ForegroundColor Yellow
}

# Also stop any background jobs
$jobs = Get-Job | Where-Object { $_.Command -like "*auto_recovery_system.ps1*" }
if ($jobs) {
    Write-Host "`nStopping $($jobs.Count) background job(s)..." -ForegroundColor Cyan
    $jobs | Stop-Job
    $jobs | Remove-Job
    Write-Host "  Jobs stopped" -ForegroundColor Green
}

Write-Host "`n" -NoNewline
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "`n  Auto Recovery System stopped`n" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "`n"
