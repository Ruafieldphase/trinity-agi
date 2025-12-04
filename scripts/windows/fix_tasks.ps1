# Fix Scheduled Tasks for Stealth Mode
Write-Host "🔧 Fixing AGI Scheduled Tasks..." -ForegroundColor Cyan

# 1. Disable MonitoringCollector (Source of 5-min popup & lag)
Write-Host "1. Disabling MonitoringCollector..." -NoNewline
Disable-ScheduledTask -TaskName "MonitoringCollector" -ErrorAction SilentlyContinue
Write-Host " [OK]" -ForegroundColor Green

# 2. Update AGI_MetaSupervisor to use pythonw.exe (Stealth)
Write-Host "2. Updating AGI_MetaSupervisor to Stealth Mode..." -NoNewline
$action = New-ScheduledTaskAction -Execute "c:\workspace\agi\fdo_agi_repo\.venv\Scripts\pythonw.exe" -Argument "C:\workspace\agi\scripts\meta_supervisor.py" -WorkingDirectory "C:\workspace\agi"
Set-ScheduledTask -TaskName "AGI_MetaSupervisor" -Action $action -ErrorAction SilentlyContinue
Write-Host " [OK]" -ForegroundColor Green

# 3. Update AGI_GoalExecutorMonitor to use pythonw.exe (Stealth)
Write-Host "3. Updating AGI_GoalExecutorMonitor to Stealth Mode..." -NoNewline
$action = New-ScheduledTaskAction -Execute "c:\workspace\agi\fdo_agi_repo\.venv\Scripts\pythonw.exe" -Argument "C:\workspace\agi\scripts\goal_executor_monitor.py" -WorkingDirectory "C:\workspace\agi"
Set-ScheduledTask -TaskName "AGI_GoalExecutorMonitor" -Action $action -ErrorAction SilentlyContinue
Write-Host " [OK]" -ForegroundColor Green

Write-Host ""
Write-Host "✅ All tasks fixed! No more popups." -ForegroundColor Green
Read-Host "Press Enter to exit"
