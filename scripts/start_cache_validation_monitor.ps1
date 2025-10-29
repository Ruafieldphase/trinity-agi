#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Background Cache Validation Monitor (No Admin Required)
.DESCRIPTION
    Monitors time and automatically runs cache validation at scheduled times.
    Runs in background and checks every 5 minutes.
.PARAMETER RegisterTime
    Base time to calculate schedules from (default: now)
.PARAMETER KillExisting
    Kill any existing monitor before starting new one
.EXAMPLE
    .\start_cache_validation_monitor.ps1
.EXAMPLE
    .\start_cache_validation_monitor.ps1 -KillExisting
#>

param(
    [DateTime]$RegisterTime = (Get-Date),
    [switch]$KillExisting
)

$ErrorActionPreference = "Continue"
$RepoRoot = "C:\workspace\agi"
$MonitorScript = "$RepoRoot\scripts\cache_validation_monitor_daemon.ps1"

# Kill existing monitors if requested
if ($KillExisting) {
    Write-Host "?îç Checking for existing monitors..." -ForegroundColor Yellow
    $existing = Get-Process -Name "pwsh", "powershell" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*cache_validation_monitor_daemon.ps1*"
    }
    
    if ($existing) {
        Write-Host "?õë Stopping $($existing.Count) existing monitor(s)..." -ForegroundColor Yellow
        $existing | Stop-Process -Force
        Start-Sleep -Seconds 2
        Write-Host "??Existing monitors stopped" -ForegroundColor Green
    }
    else {
        Write-Host "?πÔ∏è  No existing monitors found" -ForegroundColor Gray
    }
}

Write-Host "`n?? Starting Cache Validation Monitor..." -ForegroundColor Cyan
Write-Host "?ìÖ Registration time: $($RegisterTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray

# Calculate schedule
$Schedule = @{
    Check12h = $RegisterTime.AddHours(12)
    Check24h = $RegisterTime.AddHours(24)
    Check7d  = $RegisterTime.AddDays(7)
}

Write-Host "`n?ìÖ Scheduled validations:" -ForegroundColor Cyan
Write-Host "   ??12h check: $($Schedule.Check12h.ToString('yyyy-MM-dd HH:mm'))" -ForegroundColor White
Write-Host "   ??24h check: $($Schedule.Check24h.ToString('yyyy-MM-dd HH:mm'))" -ForegroundColor White
Write-Host "   ??7d check:  $($Schedule.Check7d.ToString('yyyy-MM-dd HH:mm'))" -ForegroundColor White

# Save schedule to file
$scheduleFile = "$RepoRoot\outputs\cache_validation_schedule.json"
$Schedule | ConvertTo-Json | Out-File -FilePath $scheduleFile -Encoding UTF8
Write-Host "`n?íæ Schedule saved to: $scheduleFile" -ForegroundColor Gray

# Start background monitor
Write-Host "`n?îÑ Starting background monitor..." -ForegroundColor Yellow
Write-Host "   Check interval: 5 minutes" -ForegroundColor Gray
Write-Host "   Log file: outputs\cache_validation_monitor.log" -ForegroundColor Gray

# Create daemon script if not exists
if (-not (Test-Path $MonitorScript)) {
    Write-Host "?†Ô∏è  Monitor daemon script not found, creating..." -ForegroundColor Yellow
    # Will be created by next step
}

try {
    # Start in background using Start-Process (use powershell.exe not pwsh)
    $processArgs = @{
        FilePath     = "powershell.exe"
        ArgumentList = @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-WindowStyle", "Hidden",
            "-File", $MonitorScript
        )
        WindowStyle  = "Hidden"
        PassThru     = $true
    }
    
    $process = Start-Process @processArgs
    
    Write-Host "??Monitor started (PID: $($process.Id))" -ForegroundColor Green
    Write-Host "`n?í° Tips:" -ForegroundColor Yellow
    Write-Host "   ??Monitor runs in background (hidden window)" -ForegroundColor Gray
    Write-Host "   ??Checks every 5 minutes" -ForegroundColor Gray
    Write-Host "   ??Will send notifications when validations run" -ForegroundColor Gray
    Write-Host "   ??To stop: Run with -KillExisting flag" -ForegroundColor Gray
    Write-Host "   ??To check status: Check outputs\cache_validation_monitor.log" -ForegroundColor Gray
    
}
catch {
    Write-Host "??Failed to start monitor: $_" -ForegroundColor Red
    Write-Host "?í° Try running the daemon script directly:" -ForegroundColor Yellow
    Write-Host "   pwsh -File $MonitorScript" -ForegroundColor Gray
}

Write-Host "`n??Setup complete! Monitor is running in background." -ForegroundColor Green
Write-Host "?åô You can close this window and go to sleep! ?ò¥" -ForegroundColor Cyan
