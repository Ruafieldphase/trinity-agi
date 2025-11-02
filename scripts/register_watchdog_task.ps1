#Requires -Version 5.1
param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [int]$DelayMinutes = 1,
    [string]$TaskName = "AgiWatchdog"
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspace = Split-Path -Parent $here
$watchdog = Join-Path $workspace "scripts\self_healing_watchdog.ps1"

function Get-UserSid {
    (New-Object System.Security.Principal.NTAccount($env:USERNAME)).Translate([System.Security.Principal.SecurityIdentifier]).Value
}

if ($Register) {
    if (-not (Test-Path $watchdog)) { throw "Watchdog script not found: $watchdog" }

    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$watchdog`""
    # Trigger at logon with optional delay
    $trigger = New-ScheduledTaskTrigger -AtLogOn

    $principal = New-ScheduledTaskPrincipal -UserId (Get-UserSid) -LogonType Interactive -RunLevel Limited

    $task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings (New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew)

    try {
        Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null
        Write-Host "Registered scheduled task '$TaskName' (logon + ${DelayMinutes}m delay)" -ForegroundColor Green
        exit 0
    }
    catch {
        Write-Host "Failed to register task '$TaskName': $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

if ($Unregister) {
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
        Write-Host "Unregistered scheduled task '$TaskName'" -ForegroundColor Yellow
        exit 0
    }
    catch {
        Write-Host "No task to unregister or failed: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

if ($Status) {
    try {
        $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
        $state = ($t | Get-ScheduledTaskInfo).State
        Write-Host "Task '$TaskName' exists. State: $state" -ForegroundColor Cyan
        exit 0
    }
    catch {
        Write-Host "Task '$TaskName' not found." -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "Specify -Register, -Unregister, or -Status" -ForegroundColor Yellow
exit 2
