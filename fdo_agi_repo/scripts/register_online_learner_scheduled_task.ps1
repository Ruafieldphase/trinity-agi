param(
    [ValidateSet('Register', 'Unregister', 'Status')]
    [string]$Action = 'Status',
    [string]$Time = '03:22',
    [int]$WindowHours = 24,
    [double]$LearningRate = 0.01
)

$ErrorActionPreference = 'Stop'

$TaskName = 'BQI_Online_Learner_Daily'
$workspace = Split-Path -Parent $PSCommandPath | Split-Path -Parent | Split-Path -Parent
$scriptPath = Join-Path $workspace 'fdo_agi_repo\scripts\rune\binoche_online_learner.py'
$pythonExe = Join-Path $workspace 'fdo_agi_repo\.venv\Scripts\python.exe'

function Register-Task {
    if (!(Test-Path $pythonExe)) {
        throw "Python venv not found: $pythonExe"
    }

    if (!(Test-Path $scriptPath)) {
        throw "Script not found: $scriptPath"
    }

    # Build command line
    $argList = @(
        "`"$scriptPath`"",
        "--window-hours", "$WindowHours",
        "--learning-rate", "$LearningRate"
    )
    $cmdLine = "`"$pythonExe`" " + ($argList -join ' ')

    Write-Host "[Register] BQI Online Learner: $Time daily" -ForegroundColor Cyan
    Write-Host "  Command: $cmdLine" -ForegroundColor DarkGray

    $action = New-ScheduledTaskAction -Execute $pythonExe -Argument ($argList -join ' ')
    $trigger = New-ScheduledTaskTrigger -Daily -At $Time
    $settings = New-ScheduledTaskSettingsSet `
$settings.Hidden = $true
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -DontStopOnIdleEnd

    # Register without RequireAdministrator (current user context)
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "BQI Online Learner: Adaptive ensemble weight tuning (daily $Time)" `
        -Force | Out-Null

    Write-Host "[OK] Registered: $TaskName" -ForegroundColor Green
    Write-Host "  Next run: $Time daily (user context)" -ForegroundColor Green
}

function Unregister-Task {
    Write-Host "[Unregister] $TaskName" -ForegroundColor Yellow
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
        Write-Host "[OK] Unregistered: $TaskName" -ForegroundColor Green
    }
    catch {
        Write-Host "[Info] Task not found or already removed" -ForegroundColor Gray
    }
}

function Show-Status {
    Write-Host "=== BQI Online Learner Scheduler Status ===" -ForegroundColor Cyan
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
        Write-Host "  Task: $TaskName" -ForegroundColor Green
        Write-Host "  State: $($task.State)" -ForegroundColor $(if ($task.State -eq 'Ready') { 'Green' } else { 'Yellow' })
        
        $info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($info) {
            Write-Host "  Last Run: $($info.LastRunTime)" -ForegroundColor Gray
            Write-Host "  Last Result: $($info.LastTaskResult)" -ForegroundColor $(if ($info.LastTaskResult -eq 0) { 'Green' } else { 'Red' })
            Write-Host "  Next Run: $($info.NextRunTime)" -ForegroundColor Cyan
        }
    }
    catch {
        Write-Host "  [Not Registered]" -ForegroundColor Yellow
        Write-Host "  Run with -Action Register to schedule daily online learning" -ForegroundColor Gray
    }
}

switch ($Action) {
    'Register' { Register-Task }
    'Unregister' { Unregister-Task }
    'Status' { Show-Status }
}
