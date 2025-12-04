#Requires -Version 5.1
<#
.SYNOPSIS
    Register/unregister a Windows Scheduled Task to run morning_kickoff.ps1.
.DESCRIPTION
    Schedules a daily morning kickoff (health + report + optional dashboard open).
.EXAMPLE
    .\register_morning_kickoff.ps1 -Status
.EXAMPLE
    .\register_morning_kickoff.ps1 -Register -Time "09:00" -Hours 1 -OpenHtml
.EXAMPLE
    .\register_morning_kickoff.ps1 -Unregister
#>

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [string]$TaskName = "AGI_Morning_Kickoff",
    [string]$Time = "10:00",
    [int]$Hours = 1,
    [switch]$OpenHtml
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$KickoffScript = Join-Path $WorkspaceRoot 'scripts\morning_kickoff.ps1'

function Show-Status {
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($task) {
            Write-Host "\nTask '$TaskName' is registered" -ForegroundColor Green
            Write-Host "  State: $($task.State)" -ForegroundColor Cyan
            Write-Host "  Schedule: Daily at $Time" -ForegroundColor Cyan
            Write-Host "  Script: $KickoffScript" -ForegroundColor Gray
            $info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue
            if ($info) {
                Write-Host "  Last Run: $($info.LastRunTime)" -ForegroundColor Gray
                Write-Host "  Last Result: $($info.LastTaskResult)" -ForegroundColor Gray
            }
        }
        else {
            Write-Host "\nTask '$TaskName' is NOT registered" -ForegroundColor Yellow
            Write-Host "  Run with -Register to enable morning kickoff" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "\nError checking status: $($_.Exception.Message)" -ForegroundColor Red
    }
}

if ($Status -or (-not $Register -and -not $Unregister)) { Show-Status; exit 0 }

if ($Unregister) {
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "\nTask '$TaskName' unregistered" -ForegroundColor Green
        exit 0
    }
    catch {
        Write-Host "\nFailed to unregister: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

if ($Register) {
    if (-not (Test-Path -LiteralPath $KickoffScript)) {
        Write-Host "\nError: kickoff script not found: $KickoffScript" -ForegroundColor Red
        exit 1
    }
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

    $argList = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", "`"$KickoffScript`"", "-Hours", "$Hours")
    if ($OpenHtml) { $argList += "-OpenHtml" }
    $argStr = ($argList -join ' ')

    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $argStr
    $trigger = New-ScheduledTaskTrigger -Daily -At $Time
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false `
        -DontStopOnIdleEnd `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 15)
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

    try {
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "AGI Morning Kickoff - Daily health/report at $Time" -Force | Out-Null
        Write-Host "\nTask '$TaskName' registered successfully" -ForegroundColor Green
        Write-Host "  Schedule: Daily at $Time" -ForegroundColor Cyan
        Write-Host "  Script: $KickoffScript" -ForegroundColor Gray
        Write-Host "  Args: $argStr" -ForegroundColor Gray
        Write-Host "\nTest now:" -ForegroundColor Yellow
        Write-Host "  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
        exit 0
    }
    catch {
        Write-Host "\nFailed to register: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

