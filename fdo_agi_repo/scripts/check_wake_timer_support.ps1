#Requires -Version 5.1
<#
.SYNOPSIS
    Check if Wake Timer is supported and enabled on this system.

.DESCRIPTION
    Verifies:
    1. If system supports wake timers (BIOS/UEFI setting)
    2. If any devices are armed to wake the computer
    3. Current power scheme wake timer settings

.EXAMPLE
    .\check_wake_timer_support.ps1
#>

$ErrorActionPreference = "Continue"

Write-Host "`n=== Wake Timer Support Check ===" -ForegroundColor Cyan

# 1. Check if any devices can wake the computer
Write-Host "`n[1] Devices armed to wake computer:" -ForegroundColor Yellow
try {
    $wakeArmed = powercfg /devicequery wake_armed
    if ($wakeArmed -and $wakeArmed.Count -gt 0) {
        $wakeArmed | ForEach-Object { Write-Host "   ✅ $_" -ForegroundColor Green }
    }
    else {
        Write-Host "   ⚠️  No devices armed to wake" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "   ❌ Failed to query: $_" -ForegroundColor Red
}

# 2. Check current power scheme wake timer settings
Write-Host "`n[2] Power scheme wake timer settings:" -ForegroundColor Yellow
try {
    $activeScheme = powercfg /getactivescheme
    if ($activeScheme -match 'GUID: ([a-f0-9-]+)') {
        $schemeGuid = $matches[1]
        Write-Host "   Active scheme: $schemeGuid" -ForegroundColor Gray
        
        # Check wake timer settings (AC and DC)
        $wakeTimerAC = powercfg /query $schemeGuid SUB_SLEEP RTCWAKE | Select-String "Current AC Power Setting Index:"
        $wakeTimerDC = powercfg /query $schemeGuid SUB_SLEEP RTCWAKE | Select-String "Current DC Power Setting Index:"
        
        if ($wakeTimerAC -match '0x([0-9a-f]+)') {
            $acValue = [int]"0x$($matches[1])"
            $acStatus = if ($acValue -eq 0) { "❌ Disabled" } elseif ($acValue -eq 1) { "✅ Enabled" } else { "⚠️  Important timers only" }
            Write-Host "   AC (Plugged in):  $acStatus" -ForegroundColor $(if ($acValue -eq 0) { "Red" } else { "Green" })
        }
        
        if ($wakeTimerDC -match '0x([0-9a-f]+)') {
            $dcValue = [int]"0x$($matches[1])"
            $dcStatus = if ($dcValue -eq 0) { "❌ Disabled" } elseif ($dcValue -eq 1) { "✅ Enabled" } else { "⚠️  Important timers only" }
            Write-Host "   DC (Battery):     $dcStatus" -ForegroundColor $(if ($dcValue -eq 0) { "Red" } else { "Green" })
        }
    }
}
catch {
    Write-Host "   ⚠️  Could not query power scheme: $_" -ForegroundColor Yellow
}

# 3. Check for scheduled tasks with wake timers
Write-Host "`n[3] Scheduled tasks with wake timers:" -ForegroundColor Yellow
try {
    $wakeTasks = Get-ScheduledTask | Where-Object { 
        $_.Settings.WakeToRun -eq $true 
    } | Select-Object TaskName, TaskPath, State
    
    if ($wakeTasks) {
        $wakeTasks | ForEach-Object {
            Write-Host "   ✅ $($_.TaskName) [$($_.State)]" -ForegroundColor Green
        }
    }
    else {
        Write-Host "   ⚠️  No tasks configured to wake computer" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "   ⚠️  Could not query scheduled tasks: $_" -ForegroundColor Yellow
}

# 4. Recommendations
Write-Host "`n[4] Recommendations:" -ForegroundColor Yellow

$hasWakeDevice = $wakeArmed -and $wakeArmed.Count -gt 0
$hasWakeTask = $wakeTasks -and $wakeTasks.Count -gt 0

if (-not $hasWakeDevice) {
    Write-Host "   ⚠️  Enable 'Wake Timers' in BIOS/UEFI settings" -ForegroundColor Yellow
    Write-Host "      (Usually under Power Management or ACPI settings)" -ForegroundColor Gray
}

if (-not $hasWakeTask) {
    Write-Host "   💡 No tasks with -WakeToRun enabled yet" -ForegroundColor Cyan
    Write-Host "      Run: .\register_bqi_phase6_scheduled_task.ps1 -Register" -ForegroundColor Gray
}

Write-Host "`n💡 Alternative: Use 'Start When Available' instead" -ForegroundColor Cyan
Write-Host "   Task will run when you next wake/boot the computer" -ForegroundColor Gray
Write-Host "   No BIOS changes or admin privileges required`n" -ForegroundColor Gray

exit 0
