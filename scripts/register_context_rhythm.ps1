#Requires -Version 5.1
<#
.SYNOPSIS
    Register scheduled tasks for automatic context switching (daily rhythm).

.DESCRIPTION
    Creates Windows scheduled tasks to switch AGI contexts automatically:
    - 06:00: Wake up (Sleep -> Core)
    - 22:00: Go to sleep (Any -> Sleep)
    - On demand: Auto context detection every 30 minutes

.PARAMETER Register
    Register the rhythm tasks.

.PARAMETER Unregister
    Unregister all rhythm tasks.

.PARAMETER Status
    Show status of registered rhythm tasks.
#>

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$SwitchScript = Join-Path $WorkspaceRoot "scripts\switch_context.ps1"
$AutoScript = Join-Path $WorkspaceRoot "scripts\auto_context.ps1"

$Tasks = @{
    "AGI_WakeUp"      = @{
        Time        = "06:00"
        Action      = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$SwitchScript`" -To Core -Force"
        Description = "AGI daily wake up (Sleep -> Core)"
    }
    "AGI_Sleep"       = @{
        Time        = "22:00"
        Action      = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$SwitchScript`" -To Sleep -Force"
        Description = "AGI daily sleep (Any -> Sleep)"
    }
    "AGI_AutoContext" = @{
        Interval    = 30  # minutes
        Action      = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$AutoScript`""
        Description = "AGI auto context detection (every 30 min)"
    }
}

function Register-ContextRhythm {
    Write-Host "`n⏰ Registering AGI Context Rhythm Tasks..." -ForegroundColor Cyan
    
    foreach ($taskName in $Tasks.Keys) {
        $task = $Tasks[$taskName]
        
        Write-Host "  📅 $taskName" -ForegroundColor Yellow
        
        if ($task.Time) {
            # Daily scheduled task
            $trigger = New-ScheduledTaskTrigger -Daily -At $task.Time
        }
        elseif ($task.Interval) {
            # Repetitive task
            $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $task.Interval) -RepetitionDuration (New-TimeSpan -Days 9999)
        }
        
        $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command `"$($task.Action)`""
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
        
        try {
            $existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            if ($existing) {
                Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
                Write-Host "     Removed existing task" -ForegroundColor Gray
            }
            
            Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Settings $settings -Description $task.Description | Out-Null
            Write-Host "     ✅ Registered: $($task.Description)" -ForegroundColor Green
        }
        catch {
            Write-Host "     ❌ Failed: $_" -ForegroundColor Red
        }
    }
    
    Write-Host "`n✅ Rhythm tasks registered!" -ForegroundColor Green
    Write-Host "   🌅 Wake: 06:00 (Sleep → Core)" -ForegroundColor Cyan
    Write-Host "   🌙 Sleep: 22:00 (Any → Sleep)" -ForegroundColor Cyan
    Write-Host "   🔄 Auto: Every 30 minutes" -ForegroundColor Cyan
}

function Unregister-ContextRhythm {
    Write-Host "`n🗑️ Unregistering AGI Context Rhythm Tasks..." -ForegroundColor Yellow
    
    foreach ($taskName in $Tasks.Keys) {
        try {
            $existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            if ($existing) {
                Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
                Write-Host "  ✅ Removed: $taskName" -ForegroundColor Green
            }
            else {
                Write-Host "  ⏭️ Not found: $taskName" -ForegroundColor Gray
            }
        }
        catch {
            Write-Host "  ❌ Failed: $taskName - $_" -ForegroundColor Red
        }
    }
    
    Write-Host "`n✅ Rhythm tasks unregistered!" -ForegroundColor Green
}

function Show-ContextRhythmStatus {
    Write-Host "`n⏰ AGI Context Rhythm Status" -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Gray
    
    foreach ($taskName in $Tasks.Keys) {
        $task = $Tasks[$taskName]
        $scheduled = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        
        if ($scheduled) {
            $info = Get-ScheduledTaskInfo -TaskName $taskName
            $state = if ($scheduled.State -eq "Ready") { "[OK]" } else { "[WARN]" }
            
            Write-Host "`n$state $taskName" -ForegroundColor $(if ($scheduled.State -eq "Ready") { "Green" } else { "Yellow" })
            Write-Host "   Description: $($task.Description)" -ForegroundColor Gray
            Write-Host "   State: $($scheduled.State)" -ForegroundColor Gray
            Write-Host "   Last Run: $($info.LastRunTime)" -ForegroundColor Gray
            Write-Host "   Next Run: $($info.NextRunTime)" -ForegroundColor Gray
        }
        else {
            Write-Host "`n[NOT FOUND] $taskName" -ForegroundColor Red
            Write-Host "   Not registered" -ForegroundColor Gray
        }
    }
    
    Write-Host "`n" -NoNewline
    Write-Host ("=" * 60) -ForegroundColor Gray
}

# Main execution
if ($Register) {
    Register-ContextRhythm
}
elseif ($Unregister) {
    Unregister-ContextRhythm
}
elseif ($Status) {
    Show-ContextRhythmStatus
}
else {
    # Default: show status
    Show-ContextRhythmStatus
    Write-Host "`nUsage:" -ForegroundColor Cyan
    Write-Host "  Register:   .\register_context_rhythm.ps1 -Register" -ForegroundColor Gray
    Write-Host "  Unregister: .\register_context_rhythm.ps1 -Unregister" -ForegroundColor Gray
    Write-Host "  Status:     .\register_context_rhythm.ps1 -Status" -ForegroundColor Gray
}