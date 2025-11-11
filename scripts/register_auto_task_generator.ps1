# Auto Task Generator Scheduler
# Purpose: 정기적으로 학습/테스트 작업을 자동 생성
# Usage: .\register_auto_task_generator.ps1 -Register|-Unregister|-Status

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [string]$TaskName = "AGI_AutoTaskGenerator",
    [string]$IntervalMinutes = "30"
)

$ErrorActionPreference = "Stop"

$scriptPath = "C:\workspace\agi\scripts\idle_task_generator.ps1"
$wsFolder = "C:\workspace\agi"

# Status check
if ($Status -or (-not $Register -and -not $Unregister)) {
    Write-Host "📊 Auto Task Generator Status" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
        Write-Host "✅ Task: $TaskName" -ForegroundColor Green
        Write-Host "   State: $($task.State)" -ForegroundColor Yellow
        Write-Host "   Interval: Every $IntervalMinutes minutes" -ForegroundColor Gray
        Write-Host ""
        
        $info = Get-ScheduledTaskInfo -TaskName $TaskName
        Write-Host "   Last Run: $($info.LastRunTime)" -ForegroundColor Gray
        Write-Host "   Next Run: $($info.NextRunTime)" -ForegroundColor Gray
        Write-Host "   Last Result: 0x$($info.LastTaskResult.ToString('X'))" -ForegroundColor Gray
        
    }
    catch {
        Write-Host "❌ Task not registered: $TaskName" -ForegroundColor Red
        Write-Host "   Run with -Register to create it" -ForegroundColor Yellow
    }
    
    exit 0
}

# Unregister
if ($Unregister) {
    Write-Host "🗑️  Unregistering Auto Task Generator..." -ForegroundColor Yellow
    
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
        Write-Host "✅ Unregistered: $TaskName" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Failed to unregister: $_" -ForegroundColor Red
        exit 1
    }
    
    exit 0
}

# Register
if ($Register) {
    Write-Host "📝 Registering Auto Task Generator..." -ForegroundColor Cyan
    Write-Host "   Interval: Every $IntervalMinutes minutes" -ForegroundColor Gray
    Write-Host "   Script: $scriptPath" -ForegroundColor Gray
    Write-Host ""
    
    # Check if script exists
    if (-not (Test-Path $scriptPath)) {
        Write-Host "❌ Script not found: $scriptPath" -ForegroundColor Red
        exit 1
    }
    
    # Unregister existing task
    try {
        $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
        Write-Host "⚠️  Task already exists. Unregistering..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    catch {
        # Task doesn't exist, this is fine
    }
    
    # Create action
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -IdleThresholdMinutes 30"
    
    # Create trigger (repeating every N minutes)
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)
    
    # Create settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false `
        -DontStopOnIdleEnd `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 5)
    
    # Register task
    try {
        Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Description "자동으로 시스템이 idle 상태일 때 작업을 생성합니다 (AGI 시스템 유지)" | Out-Null
        
        Write-Host "✅ Registered: $TaskName" -ForegroundColor Green
        Write-Host "   Interval: Every $IntervalMinutes minutes" -ForegroundColor Green
        Write-Host "   First run: in ~1 minute" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "💡 Check status: .\register_auto_task_generator.ps1 -Status" -ForegroundColor Gray
        
    }
    catch {
        Write-Host "❌ Failed to register task: $_" -ForegroundColor Red
        exit 1
    }
    
    exit 0
}

Write-Host "❌ No action specified. Use -Register, -Unregister, or -Status" -ForegroundColor Red
exit 1
