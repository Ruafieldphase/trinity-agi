<#
.SYNOPSIS
    Show current AGI system rhythm status

.DESCRIPTION
    Displays a quick overview of automated systems, scheduled tasks, and monitoring status.
    
.EXAMPLE
    .\show_rhythm_status.ps1
#>

param()

$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  🎵 AGI System Rhythm Status" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Morning Kickoff Task
Write-Host "📅 Morning Kickoff (Daily 10:00)" -ForegroundColor Yellow
try {
    $task = Get-ScheduledTask -TaskName "AGI_Morning_Kickoff" -ErrorAction Stop
    $info = Get-ScheduledTaskInfo -TaskName "AGI_Morning_Kickoff"
    
    $stateColor = if ($task.State -eq "Ready") { "Green" } else { "Yellow" }
    Write-Host "  Status: " -NoNewline -ForegroundColor Gray
    Write-Host $task.State -ForegroundColor $stateColor
    
    Write-Host "  Last Run: " -NoNewline -ForegroundColor Gray
    Write-Host $info.LastRunTime -ForegroundColor White
    
    $resultColor = if ($info.LastTaskResult -eq 0) { "Green" } else { "Red" }
    Write-Host "  Last Result: " -NoNewline -ForegroundColor Gray
    Write-Host "0x$($info.LastTaskResult.ToString('X'))" -ForegroundColor $resultColor
    
    Write-Host "  Next Run: " -NoNewline -ForegroundColor Gray
    Write-Host $info.NextRunTime -ForegroundColor White
} catch {
    Write-Host "  ⚠ NOT REGISTERED" -ForegroundColor Yellow
    Write-Host "  Run: .\scripts\register_morning_kickoff.ps1 -Register" -ForegroundColor Gray
}

Write-Host ""

# 2. Async Thesis Monitor
Write-Host "🔬 Async Thesis Monitor (Hourly)" -ForegroundColor Yellow
try {
    $task = Get-ScheduledTask -TaskName "AsyncThesisHealthMonitor" -ErrorAction Stop
    $info = Get-ScheduledTaskInfo -TaskName "AsyncThesisHealthMonitor"
    
    $stateColor = if ($task.State -eq "Ready") { "Green" } else { "Yellow" }
    Write-Host "  Status: " -NoNewline -ForegroundColor Gray
    Write-Host $task.State -ForegroundColor $stateColor
    
    Write-Host "  Last Run: " -NoNewline -ForegroundColor Gray
    Write-Host $info.LastRunTime -ForegroundColor White
    
    # Check latest report
    $reportPath = Join-Path $PSScriptRoot "..\outputs\async_thesis_health_latest.md"
    if (Test-Path $reportPath) {
        $reportAge = (Get-Date) - (Get-Item $reportPath).LastWriteTime
        Write-Host "  Latest Report: " -NoNewline -ForegroundColor Gray
        Write-Host "$([math]::Round($reportAge.TotalHours, 1))h ago" -ForegroundColor White
    }
} catch {
    Write-Host "  ⚠ NOT REGISTERED" -ForegroundColor Yellow
    Write-Host "  Observation period not started" -ForegroundColor Gray
}

Write-Host ""

# 3. Quick Health Check
Write-Host "🏥 System Health" -ForegroundColor Yellow
$healthPath = Join-Path $PSScriptRoot "..\outputs\system_health_latest.json"
if (Test-Path $healthPath) {
    try {
        $health = Get-Content $healthPath -Raw | ConvertFrom-Json
        $statusColor = switch ($health.StatusText) {
            "HEALTHY" { "Green" }
            { $_ -like "*WARNING*" } { "Yellow" }
            { $_ -like "*CRITICAL*" } { "Red" }
            default { "White" }
        }
        
        Write-Host "  Status: " -NoNewline -ForegroundColor Gray
        Write-Host $health.StatusText -ForegroundColor $statusColor
        
        Write-Host "  Pass Rate: " -NoNewline -ForegroundColor Gray
        Write-Host "$($health.PassRate)%" -ForegroundColor White
        
        Write-Host "  Passed: $($health.Passed) | " -NoNewline -ForegroundColor Gray
        Write-Host "Warning: $($health.Warning) | " -NoNewline -ForegroundColor Yellow
        Write-Host "Failed: $($health.Failed)" -ForegroundColor $(if ($health.Failed -gt 0) { "Red" } else { "Gray" })
        
        $age = (Get-Date) - (Get-Item $healthPath).LastWriteTime
        Write-Host "  Updated: " -NoNewline -ForegroundColor Gray
        Write-Host "$([math]::Round($age.TotalMinutes, 0))m ago" -ForegroundColor White
    } catch {
        Write-Host "  ⚠ Could not parse health status" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠ No health check available" -ForegroundColor Yellow
    Write-Host "  Run: .\scripts\system_health_check.ps1" -ForegroundColor Gray
}

Write-Host ""

# 4. Latest Task Performance
Write-Host "⚡ Latest Task Performance" -ForegroundColor Yellow
$ledgerPath = Join-Path $PSScriptRoot "..\fdo_agi_repo\memory\resonance_ledger.jsonl"
if (Test-Path $ledgerPath) {
    try {
        $recent = Get-Content $ledgerPath -Tail 100 | 
            Where-Object { $_ -match '"duration_sec"' } |
            Select-Object -Last 1
        
        if ($recent) {
            $entry = $recent | ConvertFrom-Json
            $latencyMs = [math]::Round($entry.duration_sec * 1000, 0)
            
            Write-Host "  Latency: " -NoNewline -ForegroundColor Gray
            $latencyColor = if ($latencyMs -lt 2000) { "Green" } elseif ($latencyMs -lt 5000) { "Yellow" } else { "Red" }
            Write-Host "${latencyMs}ms" -ForegroundColor $latencyColor
            
            if ($entry.ttft_sec) {
                $ttftMs = [math]::Round($entry.ttft_sec * 1000, 0)
                Write-Host "  TTFT: " -NoNewline -ForegroundColor Gray
                Write-Host "${ttftMs}ms" -ForegroundColor White
            }
        }
    } catch {
        Write-Host "  ⚠ Could not parse ledger" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠ No ledger found" -ForegroundColor Yellow
}

Write-Host ""

# 5. Monitoring Dashboard
Write-Host "📊 Monitoring Dashboard" -ForegroundColor Yellow
$dashboardPath = Join-Path $PSScriptRoot "..\outputs\monitoring_dashboard_latest.html"
if (Test-Path $dashboardPath) {
    $age = (Get-Date) - (Get-Item $dashboardPath).LastWriteTime
    Write-Host "  Available: " -NoNewline -ForegroundColor Gray
    Write-Host "monitoring_dashboard_latest.html" -ForegroundColor White
    Write-Host "  Updated: " -NoNewline -ForegroundColor Gray
    Write-Host "$([math]::Round($age.TotalHours, 1))h ago" -ForegroundColor White
    Write-Host "  Open: " -NoNewline -ForegroundColor Gray
    Write-Host "Start-Process $dashboardPath" -ForegroundColor Cyan
} else {
    Write-Host "  ⚠ Not generated yet" -ForegroundColor Yellow
    Write-Host "  Will be created at next Morning Kickoff (10:00)" -ForegroundColor Gray
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Next Actions:" -ForegroundColor Cyan
Write-Host "  • Wait for Morning Kickoff (tomorrow 10:00)" -ForegroundColor Gray
Write-Host "  • Monitor Async Thesis (7-day observation)" -ForegroundColor Gray
Write-Host "  • Review daily health snapshots" -ForegroundColor Gray
Write-Host "========================================`n" -ForegroundColor Cyan
