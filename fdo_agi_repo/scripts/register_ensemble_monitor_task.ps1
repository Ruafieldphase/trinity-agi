# Register Windows Scheduled Task for Ensemble Success Monitor
# Monitors Phase 7 Ensemble performance continuously

param(
    [switch]$Register,
    [switch]$Unregister,
    [string]$Time = "03:15",  # Daily at 03:15 AM
    [int]$Hours = 24,  # Monitor last 24 hours
    [string]$TaskName = "BinocheEnsembleMonitor"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ScriptPath = Join-Path $RepoRoot "scripts\rune\binoche_success_monitor.py"
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$LogDir = Join-Path $RepoRoot "outputs\ensemble_monitor_logs"

# Ensure log directory exists
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Register-Task {
    Write-Host "[CONFIG] Registering Scheduled Task: $TaskName" -ForegroundColor Cyan
    Write-Host "   Schedule: Daily at $Time" -ForegroundColor Gray
    Write-Host "   Monitor window: Last $Hours hours" -ForegroundColor Gray
    
    # Check if Python exists
    if (-not (Test-Path $PythonExe)) {
        Write-Host "[ERROR] Python not found: $PythonExe" -ForegroundColor Red
        Write-Host "   Please create virtual environment first:" -ForegroundColor Yellow
        Write-Host "   cd $RepoRoot; python -m venv .venv" -ForegroundColor Yellow
        exit 1
    }
    
    # Check if script exists
    if (-not (Test-Path $ScriptPath)) {
        Write-Host "[ERROR] Monitor script not found: $ScriptPath" -ForegroundColor Red
        exit 1
    }
    
    # Create action
    $LogFile = Join-Path $LogDir "monitor_$(Get-Date -Format 'yyyyMMdd').log"
    $Action = New-ScheduledTaskAction `
        -Execute $PythonExe `
        -Argument "$ScriptPath --hours $Hours" `
        -WorkingDirectory $RepoRoot
    
    # Create trigger (daily at specified time)
    $Trigger = New-ScheduledTaskTrigger -Daily -At $Time
    
    # Create settings
    $Settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
    
    # Register task
    try {
        $Task = Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $Action `
            -Trigger $Trigger `
            -Settings $Settings `
            -Description "BQI Phase 6k: Daily Ensemble Success Rate Monitoring" `
            -Force
        
        Write-Host "[OK] Task registered successfully!" -ForegroundColor Green
        Write-Host "   Task Name: $TaskName" -ForegroundColor Gray
        Write-Host "   Next Run: $((Get-ScheduledTask -TaskName $TaskName).Triggers[0].StartBoundary)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "[INFO] To run manually:" -ForegroundColor Cyan
        Write-Host "   Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "[INFO] To check status:" -ForegroundColor Cyan
        Write-Host "   Get-ScheduledTask -TaskName '$TaskName' | Get-ScheduledTaskInfo" -ForegroundColor Yellow
        
    }
    catch {
        Write-Host "[ERROR] Failed to register task: $_" -ForegroundColor Red
        exit 1
    }
}

function Unregister-Task {
    Write-Host "🗑️ Unregistering Scheduled Task: $TaskName" -ForegroundColor Cyan
    
    try {
        $ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($ExistingTask) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Host "[OK] Task unregistered successfully!" -ForegroundColor Green
        }
        else {
            Write-Host "ℹ️ Task not found: $TaskName" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "[ERROR] Failed to unregister task: $_" -ForegroundColor Red
        exit 1
    }
}

function Show-Status {
    Write-Host "[METRICS] Scheduled Task Status: $TaskName" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        $Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($Task) {
            $Info = $Task | Get-ScheduledTaskInfo
            
            Write-Host "Task: $TaskName" -ForegroundColor White
            Write-Host "  State: $($Task.State)" -ForegroundColor Gray
            Write-Host "  Last Run: $($Info.LastRunTime)" -ForegroundColor Gray
            Write-Host "  Last Result: $($Info.LastTaskResult)" -ForegroundColor Gray
            Write-Host "  Next Run: $($Info.NextRunTime)" -ForegroundColor Gray
            Write-Host ""
            
            # Check recent logs
            $RecentLogs = Get-ChildItem $LogDir -Filter "monitor_*.log" -ErrorAction SilentlyContinue | 
            Sort-Object LastWriteTime -Descending | 
            Select-Object -First 3
            
            if ($RecentLogs) {
                Write-Host "📁 Recent Logs:" -ForegroundColor Cyan
                foreach ($Log in $RecentLogs) {
                    Write-Host "  $($Log.Name) - $($Log.LastWriteTime)" -ForegroundColor Gray
                }
            }
            
        }
        else {
            Write-Host "ℹ️ Task not registered: $TaskName" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "[INFO] To register:" -ForegroundColor Cyan
            Write-Host "   .\register_ensemble_monitor_task.ps1 -Register" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "[ERROR] Failed to get task status: $_" -ForegroundColor Red
        exit 1
    }
}

# Main logic
if ($Register) {
    Register-Task
}
elseif ($Unregister) {
    Unregister-Task
}
else {
    Show-Status
}
