#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Register Windows Scheduled Tasks for Cache Validation
.DESCRIPTION
    Creates scheduled tasks to run cache validation automatically at:
    - 12 hours after registration (first check)
    - 24 hours after registration (main check)
    - 7 days after registration (long-term check)
.PARAMETER Register
    Register the scheduled tasks
.PARAMETER Unregister
    Unregister (delete) the scheduled tasks
.PARAMETER Force
    Skip confirmation prompts
.EXAMPLE
    .\register_cache_validation_tasks.ps1 -Register
.EXAMPLE
    .\register_cache_validation_tasks.ps1 -Unregister -Force
#>

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Force
)

# UTF-8 console bootstrap
try { chcp 65001 > $null 2> $null } catch {}
try {
    [Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $OutputEncoding = New-Object System.Text.UTF8Encoding($false)
}
catch {}

$ErrorActionPreference = "Stop"

# Configuration
$TaskBaseName = "CacheValidation"
$RepoRoot = "C:\workspace\agi"
$ScriptPath = "$RepoRoot\scripts\auto_cache_validation.ps1"

# Task definitions
$Tasks = @(
    @{
        Name        = "${TaskBaseName}_12h"
        Description = "Cache validation - 12 hour check"
        Hours       = 12
        Interval    = 1
        Delay       = "PT12H"  # 12 hours from now
    },
    @{
        Name        = "${TaskBaseName}_24h"
        Description = "Cache validation - 24 hour check (MAIN)"
        Hours       = 24
        Interval    = 2
        Delay       = "PT24H"  # 24 hours from now
    },
    @{
        Name        = "${TaskBaseName}_7d"
        Description = "Cache validation - 7 day long-term check"
        Hours       = 168
        Interval    = 12
        Delay       = "P7D"  # 7 days from now
    }
)

function Register-Tasks {
    Write-Host "`n>> Registering Cache Validation Scheduled Tasks..." -ForegroundColor Cyan
    
    if (-not (Test-Path $ScriptPath)) {
        Write-Host "** Script not found: $ScriptPath" -ForegroundColor Red
        exit 1
    }
    
    $RegisterTime = Get-Date
    Write-Host "** Registration time: $($RegisterTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
    
    foreach ($task in $Tasks) {
        Write-Host "`n>> Creating task: $($task.Name)" -ForegroundColor Yellow
        Write-Host "   Description: $($task.Description)" -ForegroundColor Gray
        
        # Calculate execution time
        $ExecutionTime = $RegisterTime.Add([System.Xml.XmlConvert]::ToTimeSpan($task.Delay))
        Write-Host "   Will run at: $($ExecutionTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Cyan
        Write-Host "   Parameters: -Hours $($task.Hours) -Interval $($task.Interval)" -ForegroundColor Gray
        
        # Check if task already exists
        $existingTask = Get-ScheduledTask -TaskName $task.Name -ErrorAction SilentlyContinue
        if ($existingTask) {
            if (-not $Force) {
                $response = Read-Host "   -- Task already exists. Overwrite? (y/N)"
                if ($response -ne 'y' -and $response -ne 'Y') {
                    Write-Host "   ** Skipped" -ForegroundColor Yellow
                    continue
                }
            }
            Unregister-ScheduledTask -TaskName $task.Name -Confirm:$false
            Write-Host "   ** Removed existing task" -ForegroundColor Gray
        }
        
        # Create action
        $actionArgs = "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`" -Hours $($task.Hours) -Interval $($task.Interval) -SendNotification"
        $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $actionArgs
        
        # Create trigger (run once at specified delay from now)
        $trigger = New-ScheduledTaskTrigger -Once -At $ExecutionTime
        
        # Create settings
        $settings = New-ScheduledTaskSettingsSet `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -StartWhenAvailable `
            -RunOnlyIfNetworkAvailable:$false `
            -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
        
        # Create principal (run as current user)
        $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest
        
        # Register task
        try {
            Register-ScheduledTask `
                -TaskName $task.Name `
                -Description $task.Description `
                -Action $action `
                -Trigger $trigger `
                -Settings $settings `
                -Principal $principal `
                -Force | Out-Null
            
            Write-Host "   ** Task registered successfully" -ForegroundColor Green
        }
        catch {
            Write-Host "   ** Failed to register task: $_" -ForegroundColor Red
        }
    }
    
    Write-Host "`n** All tasks registered!" -ForegroundColor Green
    Write-Host "`n>> Schedule summary:" -ForegroundColor Cyan
    Write-Host "   * 12h check: $($RegisterTime.AddHours(12).ToString('yyyy-MM-dd HH:mm'))" -ForegroundColor White
    Write-Host "   * 24h check: $($RegisterTime.AddHours(24).ToString('yyyy-MM-dd HH:mm'))" -ForegroundColor White
    Write-Host "   * 7d check:  $($RegisterTime.AddDays(7).ToString('yyyy-MM-dd HH:mm'))" -ForegroundColor White
    
    Write-Host "`n>> Tips:" -ForegroundColor Yellow
    Write-Host "   * Results will be saved in: $RepoRoot\outputs\" -ForegroundColor Gray
    Write-Host "   * You'll get a notification when each check completes" -ForegroundColor Gray
    Write-Host "   * To view tasks: Task Scheduler > Task Scheduler Library" -ForegroundColor Gray
    Write-Host "   * To unregister: Run with -Unregister flag" -ForegroundColor Gray
}

function Unregister-Tasks {
    Write-Host "`n>> Unregistering Cache Validation Scheduled Tasks..." -ForegroundColor Cyan
    
    $removedCount = 0
    foreach ($task in $Tasks) {
        $existingTask = Get-ScheduledTask -TaskName $task.Name -ErrorAction SilentlyContinue
        if ($existingTask) {
            if (-not $Force) {
                $response = Read-Host "Remove task '$($task.Name)'? (y/N)"
                if ($response -ne 'y' -and $response -ne 'Y') {
                    Write-Host "** Skipped: $($task.Name)" -ForegroundColor Yellow
                    continue
                }
            }
            
            try {
                Unregister-ScheduledTask -TaskName $task.Name -Confirm:$false
                Write-Host "** Removed: $($task.Name)" -ForegroundColor Green
                $removedCount++
            }
            catch {
                Write-Host "** Failed to remove: $($task.Name) - $_" -ForegroundColor Red
            }
        }
        else {
            Write-Host "-- Not found: $($task.Name)" -ForegroundColor Gray
        }
    }
    
    if ($removedCount -gt 0) {
        Write-Host "`n** Unregistered $removedCount task(s)" -ForegroundColor Green
    }
    else {
        Write-Host "`n-- No tasks were removed" -ForegroundColor Gray
    }
}

function Show-Status {
    Write-Host "`n>> Current Cache Validation Tasks:" -ForegroundColor Cyan
    
    $foundAny = $false
    foreach ($task in $Tasks) {
        $existingTask = Get-ScheduledTask -TaskName $task.Name -ErrorAction SilentlyContinue
        if ($existingTask) {
            $foundAny = $true
            $info = Get-ScheduledTaskInfo -TaskName $task.Name
            Write-Host "`n** $($task.Name)" -ForegroundColor Green
            Write-Host "   State: $($existingTask.State)" -ForegroundColor Gray
            Write-Host "   Next Run: $($info.NextRunTime)" -ForegroundColor Cyan
            Write-Host "   Last Run: $($info.LastRunTime)" -ForegroundColor Gray
            Write-Host "   Last Result: $($info.LastTaskResult)" -ForegroundColor Gray
        }
    }
    
    if (-not $foundAny) {
        Write-Host "`n-- No cache validation tasks found" -ForegroundColor Gray
        Write-Host ">> Run with -Register to create them" -ForegroundColor Yellow
    }
}

# Main execution
if ($Register -and $Unregister) {
    Write-Host "** Cannot use -Register and -Unregister together" -ForegroundColor Red
    exit 1
}

if ($Register) {
    Register-Tasks
}
elseif ($Unregister) {
    Unregister-Tasks
}
else {
    Show-Status
    Write-Host "`n>> Usage:" -ForegroundColor Yellow
    Write-Host "   Register tasks:   .\register_cache_validation_tasks.ps1 -Register" -ForegroundColor Gray
    Write-Host "   Unregister tasks: .\register_cache_validation_tasks.ps1 -Unregister" -ForegroundColor Gray
    Write-Host "   Show status:      .\register_cache_validation_tasks.ps1" -ForegroundColor Gray
}
