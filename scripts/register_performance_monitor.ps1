# Register Performance Monitoring Task
# Sets up scheduled task to collect benchmarks and update dashboard periodically

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [int]$IntervalMinutes = 30,
    [string]$TaskName = "AGI_Performance_Monitor"
)

$ErrorActionPreference = "Stop"

$scriptRoot = "C:\workspace\agi"
$benchmarkScript = "$scriptRoot\scripts\save_performance_benchmark.ps1"
$dashboardScript = "$scriptRoot\scripts\generate_unified_dashboard.ps1"
$visualScript = "$scriptRoot\scripts\generate_visual_dashboard.ps1"

# Status check
if ($Status -or (-not $Register -and -not $Unregister)) {
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "Performance Monitor Status" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host ""
    
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
        Write-Host "✓ Task exists: $TaskName" -ForegroundColor Green
        Write-Host "  State: $($task.State)" -ForegroundColor $(if ($task.State -eq 'Ready') { 'Green' }else { 'Yellow' })
        Write-Host "  Last Run: $($task.LastRunTime)" -ForegroundColor DarkGray
        Write-Host "  Next Run: $($task.NextRunTime)" -ForegroundColor DarkGray
        
        $info = Get-ScheduledTaskInfo -TaskName $TaskName
        Write-Host "  Last Result: $($info.LastTaskResult)" -ForegroundColor $(if ($info.LastTaskResult -eq 0) { 'Green' }else { 'Red' })
    }
    catch {
        Write-Host "✗ Task not found: $TaskName" -ForegroundColor Yellow
        Write-Host "  Run with -Register to create it" -ForegroundColor White
    }
    
    Write-Host ""
    exit 0
}

# Unregister
if ($Unregister) {
    Write-Host "🗑️ Unregistering performance monitor..." -ForegroundColor Yellow
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
        Write-Host "✓ Task removed successfully" -ForegroundColor Green
    }
    catch {
        Write-Host "✗ Failed to remove task: $_" -ForegroundColor Red
        exit 1
    }
    exit 0
}

# Register
if ($Register) {
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "Registering Performance Monitor" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host ""
    
    # Remove existing task if present
    try {
        $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($existing) {
            Write-Host "  Removing existing task..." -ForegroundColor Yellow
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        }
    }
    catch {}
    
    # Create command script that chains all operations
    $chainedCommand = @"
# Performance Monitor Chain
Write-Host '🔄 Running performance benchmark...' -ForegroundColor Cyan
& '$benchmarkScript' -Warmup -Iterations 3 -MaxTokens 64 -Append -RunAnalysis -OptimizePolicy

if (`$LASTEXITCODE -eq 0) {
    Write-Host '📊 Updating unified dashboard...' -ForegroundColor Cyan
    & '$dashboardScript'
    
    if (`$LASTEXITCODE -eq 0) {
        Write-Host '🎨 Generating visual dashboard...' -ForegroundColor Cyan
        & '$visualScript'
    }
}

Write-Host '✓ Performance monitor cycle completed' -ForegroundColor Green
"@
    
    $tempScript = "$scriptRoot\scripts\.temp_perf_monitor_chain.ps1"
    $chainedCommand | Set-Content -Path $tempScript -Encoding UTF8
    
    # Create scheduled task
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$tempScript`""
    
    # Trigger: every N minutes, indefinitely
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)
    
    # Settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Hours 1)
    
    # Principal (run as current user)
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
    
    # Register
    try {
        Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Principal $principal `
            -Description "Collects performance benchmarks and updates dashboards every $IntervalMinutes minutes" `
            -ErrorAction Stop | Out-Null
        
        Write-Host "✓ Task registered successfully" -ForegroundColor Green
        Write-Host ""
        Write-Host "Configuration:" -ForegroundColor Cyan
        Write-Host "  Interval: Every $IntervalMinutes minutes" -ForegroundColor White
        Write-Host "  Runs as: $env:USERNAME" -ForegroundColor White
        Write-Host "  Network: Required" -ForegroundColor White
        Write-Host ""
        Write-Host "⚠️  Note: Task will start at next interval trigger" -ForegroundColor Yellow
        Write-Host "   To run immediately, use: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
        Write-Host ""
    }
    catch {
        Write-Host "❌ Failed to register task: $_" -ForegroundColor Red
        exit 1
    }
}
