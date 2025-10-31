<#
.SYNOPSIS
Register/Unregister Task Queue Server as a Windows Scheduled Task (At Logon)

.DESCRIPTION
Registers a scheduled task to automatically start Task Queue Server on user logon.
Server runs in background on port 8091 for Gitko Extension integration.

.EXAMPLE
.\register_task_queue_server.ps1 -Register
Register the task to start at logon

.EXAMPLE
.\register_task_queue_server.ps1 -Unregister
Remove the scheduled task

.EXAMPLE
.\register_task_queue_server.ps1 -Status
Check if task is registered
#>

[CmdletBinding(DefaultParameterSetName = 'Status')]
param(
    [Parameter(ParameterSetName = 'Register')]
    [switch]$Register,
    
    [Parameter(ParameterSetName = 'Unregister')]
    [switch]$Unregister,
    
    [Parameter(ParameterSetName = 'Status')]
    [switch]$Status,
    
    [string]$TaskName = "TaskQueueServer",
    
    [switch]$Force
)

# UTF-8 Bootstrap
chcp 65001 | Out-Null
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$ErrorActionPreference = 'Stop'

# Paths
$serverScript = Join-Path $PSScriptRoot "..\LLM_Unified\ion-mentoring\task_queue_server.py"
$serverScript = Resolve-Path $serverScript -ErrorAction Stop

# Check Python availability
$pythonCmd = "py -3"
try {
    & py -3 --version | Out-Null
}
catch {
    Write-Host "-- ERROR: Python 3 not found (py -3)" -ForegroundColor Red
    Write-Host "   Install Python from: https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

# Check FastAPI/Uvicorn
$checkImports = @"
import sys
try:
    import fastapi
    import uvicorn
    sys.exit(0)
except ImportError as e:
    print(f'Missing: {e.name}')
    sys.exit(1)
"@

$importCheck = $checkImports | & py -3 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "-- WARNING: FastAPI/Uvicorn not installed" -ForegroundColor Yellow
    Write-Host "   Installing dependencies..." -ForegroundColor Cyan
    & py -3 -m pip install fastapi uvicorn --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "-- ERROR: Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host "** Dependencies installed successfully" -ForegroundColor Green
}

# Main logic
try {
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    
    if ($PSCmdlet.ParameterSetName -eq 'Register' -or $Register) {
        Write-Host ">> Registering Task Queue Server (At Logon)" -ForegroundColor Cyan
        
        if ($existing -and -not $Force) {
            Write-Host "-- Task '$TaskName' already exists. Use -Force to recreate." -ForegroundColor Yellow
            exit 0
        }
        
        if ($existing -and $Force) {
            Write-Host "-- Removing existing task..." -ForegroundColor Yellow
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null
        }
        
        # Task action: Start Python server
        $pythonExe = (Get-Command py).Source
        $arguments = "-3 `"$serverScript`" --port 8091 --host 127.0.0.1"
        $action = New-ScheduledTaskAction -Execute $pythonExe -Argument $arguments
        
        # Trigger: At logon
        $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
        
        # Settings: Allow battery, don't stop, restart on failure
        $settings = New-ScheduledTaskSettingsSet `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -MultipleInstances Parallel `
            -RestartCount 3 `
            -RestartInterval (New-TimeSpan -Minutes 1) `
            -ExecutionTimeLimit (New-TimeSpan -Hours 0)  # No time limit
        
        # Register task
        Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Description "Task Queue Server for Gitko Extension (Port 8091)" | Out-Null
        
        Write-Host "** Task registered: $TaskName" -ForegroundColor Green
        Write-Host "   Server will start automatically at next logon" -ForegroundColor Gray
        Write-Host "" -ForegroundColor Gray
        Write-Host ">> Starting server now..." -ForegroundColor Cyan
        Start-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        
        # Verify server is running
        try {
            $response = Invoke-WebRequest -Uri 'http://localhost:8091/api/health' -TimeoutSec 3 -ErrorAction Stop
            Write-Host "** Task Queue Server is ONLINE" -ForegroundColor Green
            Write-Host "   Health check: $($response.StatusCode)" -ForegroundColor Gray
        }
        catch {
            Write-Host "-- Server starting (check status in 5 seconds)" -ForegroundColor Yellow
        }
        
        exit 0
    }
    elseif ($PSCmdlet.ParameterSetName -eq 'Unregister' -or $Unregister) {
        Write-Host ">> Unregistering Task Queue Server" -ForegroundColor Cyan
        
        if ($existing) {
            # Stop running instances
            Write-Host "-- Stopping server..." -ForegroundColor Yellow
            Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
            
            # Kill Python processes
            Get-Process python -ErrorAction SilentlyContinue | 
            Where-Object { $_.CommandLine -like '*task_queue_server*' } | 
            Stop-Process -Force -ErrorAction SilentlyContinue
            
            # Unregister task
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null
            Write-Host "** Task unregistered: $TaskName" -ForegroundColor Green
        }
        else {
            Write-Host "-- Task not found: $TaskName" -ForegroundColor Yellow
        }
        
        exit 0
    }
    else {
        # Status check
        Write-Host ">> Task Queue Server Status" -ForegroundColor Cyan
        Write-Host "" -ForegroundColor Gray
        
        if ($existing) {
            Write-Host "** Scheduled Task: REGISTERED" -ForegroundColor Green
            Write-Host "   Name: $TaskName" -ForegroundColor Gray
            Write-Host "   State: $($existing.State)" -ForegroundColor Gray
            Write-Host "" -ForegroundColor Gray
        }
        else {
            Write-Host "-- Scheduled Task: NOT REGISTERED" -ForegroundColor Yellow
            Write-Host "   Run: .\register_task_queue_server.ps1 -Register" -ForegroundColor Gray
            Write-Host "" -ForegroundColor Gray
        }
        
        # Check if server is running
        try {
            $response = Invoke-WebRequest -Uri 'http://localhost:8091/api/health' -TimeoutSec 2 -ErrorAction Stop
            Write-Host "** Server Status: ONLINE" -ForegroundColor Green
            Write-Host "   Port: 8091" -ForegroundColor Gray
            Write-Host "   Health: $($response.StatusCode)" -ForegroundColor Gray
        }
        catch {
            Write-Host "-- Server Status: OFFLINE" -ForegroundColor Red
            if ($existing) {
                Write-Host "   Start: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
            }
            else {
                Write-Host "   Register first, then start automatically at logon" -ForegroundColor Gray
            }
        }
        
        exit 0
    }
}
catch {
    Write-Host "-- ERROR: $_" -ForegroundColor Red
    exit 1
}
