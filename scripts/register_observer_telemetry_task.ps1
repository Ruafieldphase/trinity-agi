#requires -Version 5.1
<#
.SYNOPSIS
    Register Windows Task Scheduler job for Stream Observer telemetry (auto-start at logon).
.DESCRIPTION
    Creates/removes a scheduled task that starts observer telemetry at user logon.
    Safe to run repeatedly (idempotent).
.PARAMETER Register
    Register the scheduled task
.PARAMETER Unregister
    Remove the scheduled task
.PARAMETER TaskName
    Name of the task (default: StreamObserverTelemetry)
.EXAMPLE
    .\register_observer_telemetry_task.ps1 -Register
    .\register_observer_telemetry_task.ps1 -Unregister
    .\register_observer_telemetry_task.ps1  # Show status
#>
param(
    [switch]$Register,
    [switch]$Unregister,
    [string]$TaskName = 'StreamObserverTelemetry'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$workspaceRoot = Split-Path -Parent $PSScriptRoot
$observerScript = Join-Path $PSScriptRoot 'ensure_observer_telemetry.ps1'

function Test-TaskExists {
    param([string]$name)
    try {
        $task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
        return ($null -ne $task)
    }
    catch { return $false }
}

function Show-TaskStatus {
    Write-Host "`n📊 Stream Observer Telemetry - Task Status" -ForegroundColor Cyan
    Write-Host "   Task Name: $TaskName" -ForegroundColor Gray
    
    if (Test-TaskExists $TaskName) {
        try {
            $task = Get-ScheduledTask -TaskName $TaskName
            $info = Get-ScheduledTaskInfo -TaskName $TaskName
            
            Write-Host "   Status: " -NoNewline -ForegroundColor Gray
            switch ($task.State) {
                'Ready' { Write-Host "READY ✓" -ForegroundColor Green }
                'Running' { Write-Host "RUNNING ✓" -ForegroundColor Green }
                'Disabled' { Write-Host "DISABLED" -ForegroundColor Yellow }
                default { Write-Host $task.State -ForegroundColor Yellow }
            }
            
            Write-Host "   Trigger: " -NoNewline -ForegroundColor Gray
            $triggers = $task.Triggers | Where-Object { $_ -ne $null }
            if ($triggers.Count -gt 0) {
                foreach ($trigger in $triggers) {
                    if ($trigger.CimClass.CimClassName -match 'LogonTrigger') {
                        Write-Host "At logon" -ForegroundColor Cyan
                    }
                    else {
                        Write-Host $trigger.CimClass.CimClassName -ForegroundColor Cyan
                    }
                }
            }
            else {
                Write-Host "None" -ForegroundColor Yellow
            }
            
            if ($info.LastRunTime) {
                $elapsed = (Get-Date) - $info.LastRunTime
                Write-Host "   Last Run: $($info.LastRunTime.ToString('yyyy-MM-dd HH:mm:ss')) ($([math]::Round($elapsed.TotalHours, 1))h ago)" -ForegroundColor Gray
            }
            
            if ($info.LastTaskResult -ne 0) {
                Write-Host "   Last Result: 0x$($info.LastTaskResult.ToString('X8'))" -ForegroundColor Yellow
            }
            else {
                Write-Host "   Last Result: Success (0x00000000)" -ForegroundColor Green
            }
        }
        catch {
            Write-Host "   Error retrieving task info: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    else {
        Write-Host "   Status: NOT REGISTERED" -ForegroundColor Yellow
        Write-Host "`n   💡 Tip: Use -Register to create the task" -ForegroundColor Gray
    }
}

# Main logic
if ($Unregister) {
    Write-Host "`n🗑️  Unregistering Stream Observer Telemetry task..." -ForegroundColor Yellow
    
    if (Test-TaskExists $TaskName) {
        try {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Host "   ✅ Task removed successfully." -ForegroundColor Green
        }
        catch {
            Write-Host "   ❌ Failed to remove task: $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    }
    else {
        Write-Host "   ℹ️  Task does not exist (nothing to remove)." -ForegroundColor Cyan
    }
    
    exit 0
}

if ($Register) {
    Write-Host "`n🔧 Registering Stream Observer Telemetry task..." -ForegroundColor Cyan
    
    # Validate observer script exists
    if (-not (Test-Path -LiteralPath $observerScript)) {
        Write-Host "   ❌ Error: Observer script not found: $observerScript" -ForegroundColor Red
        exit 1
    }
    
    # Remove existing task if present
    if (Test-TaskExists $TaskName) {
        Write-Host "   ⚠️  Task already exists - removing old version..." -ForegroundColor Yellow
        try {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        }
        catch {
            Write-Host "   ❌ Failed to remove existing task: $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    }
    
    # Create task action (with hidden window)
    $action = New-ScheduledTaskAction `
        -Execute 'powershell.exe' `
        -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$observerScript`"" `
        -WorkingDirectory $workspaceRoot
    
    # Create trigger (at logon, with 5 minute delay to avoid boot congestion)
    $trigger = New-ScheduledTaskTrigger -AtLogon
    $trigger.Delay = 'PT5M'  # 5 minute delay
    
    # Create settings (with hidden task)
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1) `
        -Hidden
    
    # Register task
    try {
        Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Description "Stream Observer telemetry collector (AGI system activity monitoring)" `
            -ErrorAction Stop | Out-Null
        
        Write-Host "   ✅ Task registered successfully!" -ForegroundColor Green
        Write-Host "`n   📋 Configuration:" -ForegroundColor Gray
        Write-Host "      Trigger: At user logon (5min delay)" -ForegroundColor Gray
        Write-Host "      Script: $observerScript" -ForegroundColor Gray
        Write-Host "      Auto-restart: Yes (up to 3 times, 1min interval)" -ForegroundColor Gray
        Write-Host "`n   💡 Tip: Use -Unregister to remove this task" -ForegroundColor Gray
    }
    catch {
        Write-Host "   ❌ Failed to register task: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
    
    exit 0
}

# Default: show status
Show-TaskStatus
exit 0
