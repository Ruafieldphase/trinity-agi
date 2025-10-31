<#
.SYNOPSIS
Register/Unregister Worker Monitor as a Windows Scheduled Task (At Logon)

.DESCRIPTION
Registers a scheduled task to automatically start the RPA Worker Monitor on user logon.
The monitor enforces a maximum number of worker processes and auto-recovers the task
queue server when health checks fail.

.EXAMPLE
./register_worker_monitor_task.ps1 -Register
Register the monitor to start at logon and start it now

.EXAMPLE
./register_worker_monitor_task.ps1 -Unregister
Remove the scheduled task and stop running monitors

.EXAMPLE
./register_worker_monitor_task.ps1 -Status
Show registration and basic runtime status
#>

[CmdletBinding(DefaultParameterSetName = 'Status')]
param(
    [Parameter(ParameterSetName = 'Register')]
    [switch]$Register,

    [Parameter(ParameterSetName = 'Unregister')]
    [switch]$Unregister,

    [Parameter(ParameterSetName = 'Status')]
    [switch]$Status,

    [string]$TaskName = 'WorkerMonitor',

    [string]$Server = 'http://127.0.0.1:8091',
    [int]$IntervalSeconds = 5,
    [int]$MaxWorkers = 2,
    [string]$LogFile = $null,

    [switch]$Force
)

# UTF-8 Bootstrap
chcp 65001 | Out-Null
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$ErrorActionPreference = 'Stop'

# Paths
# Resolve script root robustly
$scriptRoot = if ($PSScriptRoot -and $PSScriptRoot.Trim() -ne '') { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
if (-not $LogFile -or $LogFile.Trim() -eq '') { $LogFile = Join-Path (Join-Path $scriptRoot '..') 'outputs\worker_monitor.log' }

$startScript = Join-Path $scriptRoot 'start_worker_monitor.ps1'
$startScript = Resolve-Path $startScript -ErrorAction Stop

try {
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

    if ($PSCmdlet.ParameterSetName -eq 'Register' -or $Register) {
        Write-Host ">> Registering Worker Monitor (At Logon)" -ForegroundColor Cyan

        if ($existing -and -not $Force) {
            Write-Host "-- Task '$TaskName' already exists. Use -Force to recreate." -ForegroundColor Yellow
            exit 0
        }
        if ($existing -and $Force) {
            Write-Host "-- Removing existing task..." -ForegroundColor Yellow
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null
        }

        # Ensure log directory exists
        $logDir = Split-Path -Parent $LogFile
        if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

        # Task action: launch monitor starter
        $pwsh = (Get-Command powershell).Source
        $psArgs = "-NoProfile -ExecutionPolicy Bypass -File `"$startScript`" -KillExisting -Server `"$Server`" -IntervalSeconds $IntervalSeconds -LogFile `"$LogFile`" -MaxWorkers $MaxWorkers"
        $action = New-ScheduledTaskAction -Execute $pwsh -Argument $psArgs

        # Trigger: At logon
        $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

        # Settings: resilient
        $settings = New-ScheduledTaskSettingsSet `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -MultipleInstances Parallel `
            -RestartCount 3 `
            -RestartInterval (New-TimeSpan -Minutes 1) `
            -ExecutionTimeLimit (New-TimeSpan -Hours 0)

        Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Description "RPA Worker Monitor (auto-enforce MaxWorkers, server self-heal)" | Out-Null

        Write-Host "** Task registered: $TaskName" -ForegroundColor Green
        Write-Host "   Monitor will start automatically at next logon" -ForegroundColor Gray
        Write-Host "" -ForegroundColor Gray
        Write-Host ">> Starting monitor now..." -ForegroundColor Cyan
        Start-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2

        # Show brief status
        if (Test-Path -LiteralPath $LogFile) {
            Write-Host "-- Log tail:" -ForegroundColor Gray
            Get-Content -LiteralPath $LogFile -Tail 10 | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
        }
        exit 0
    }
    elseif ($PSCmdlet.ParameterSetName -eq 'Unregister' -or $Unregister) {
        Write-Host ">> Unregistering Worker Monitor" -ForegroundColor Cyan

        if ($existing) {
            Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null
            Write-Host "** Task unregistered: $TaskName" -ForegroundColor Green
        }
        else {
            Write-Host "-- Task not found: $TaskName" -ForegroundColor Yellow
        }

        # Stop running job instances and related PowerShells
        Get-Job -Name 'RPA_Worker_Monitor' -ErrorAction SilentlyContinue | ForEach-Object {
            try { Stop-Job -Id $_.Id -Force -ErrorAction SilentlyContinue } catch {}
            try { Remove-Job -Id $_.Id -Force -ErrorAction SilentlyContinue } catch {}
        }
        Get-Process powershell -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*worker_monitor*' } | Stop-Process -Force -ErrorAction SilentlyContinue

        exit 0
    }
    else {
        Write-Host ">> Worker Monitor Status" -ForegroundColor Cyan
        Write-Host "" -ForegroundColor Gray

        if ($existing) {
            Write-Host "** Scheduled Task: REGISTERED" -ForegroundColor Green
            Write-Host "   Name: $TaskName" -ForegroundColor Gray
            Write-Host "   State: $($existing.State)" -ForegroundColor Gray
        }
        else {
            Write-Host "-- Scheduled Task: NOT REGISTERED" -ForegroundColor Yellow
            Write-Host "   Run: .\register_worker_monitor_task.ps1 -Register" -ForegroundColor Gray
        }

        # Check log presence / tail
        if (Test-Path -LiteralPath $LogFile) {
            Write-Host "" -ForegroundColor Gray
            Write-Host "-- Log tail:" -ForegroundColor Gray
            Get-Content -LiteralPath $LogFile -Tail 10 | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
        }

        # Quick server health
        try {
            $resp = Invoke-WebRequest -Uri ("$Server/api/health") -TimeoutSec 2 -ErrorAction Stop
            Write-Host "" -ForegroundColor Gray
            Write-Host "** Server Status: ONLINE ($($resp.StatusCode))" -ForegroundColor Green
        }
        catch {
            Write-Host "" -ForegroundColor Gray
            Write-Host "-- Server Status: OFFLINE" -ForegroundColor Red
        }

        exit 0
    }
}
catch {
    Write-Host "-- ERROR: $_" -ForegroundColor Red
    exit 1
}
