# monitor_task_execution.ps1
# 예약 작업의 실행 시간과 상태를 모니터링

param(
    [Parameter(Mandatory = $false)]
    [string]$TaskName = "LumenFeedbackEmitter",
    
    [Parameter(Mandatory = $false)]
    [int]$Hours = 24,
    
    [Parameter(Mandatory = $false)]
    [string]$OutFile = ""
)

$ErrorActionPreference = "Stop"

Write-Host "=== Task Execution Monitor ===" -ForegroundColor Cyan
Write-Host "Task: $TaskName"
Write-Host "Period: Last $Hours hours"
Write-Host ""

# Get task info
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) {
    Write-Host "ERROR: Task '$TaskName' not found" -ForegroundColor Red
    exit 1
}

$taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName

Write-Host "Current Status:" -ForegroundColor Yellow
Write-Host "  State:           $($task.State)"
Write-Host "  Last Run:        $($taskInfo.LastRunTime)"
Write-Host "  Last Result:     $($taskInfo.LastTaskResult) $(if ($taskInfo.LastTaskResult -eq 0) { '(Success)' } elseif ($taskInfo.LastTaskResult -eq 267009) { '(Already Running)' } else { '(Error)' })"
Write-Host "  Next Run:        $($taskInfo.NextRunTime)"
Write-Host "  Missed Runs:     $($taskInfo.NumberOfMissedRuns)"
Write-Host ""

# Try to get running processes
Write-Host "Checking for running Python processes..." -ForegroundColor Yellow
$pythonProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue | 
Where-Object { $_.CommandLine -like "*emit_feedback_metrics*" }

if ($pythonProcesses) {
    Write-Host "  Found $($pythonProcesses.Count) running feedback processes:" -ForegroundColor Yellow
    foreach ($proc in $pythonProcesses) {
        $runtime = (Get-Date) - $proc.StartTime
        Write-Host "    PID $($proc.Id): Running for $([int]$runtime.TotalMinutes)m $($runtime.Seconds)s" -ForegroundColor Cyan
        Write-Host "      CPU Time: $($proc.TotalProcessorTime)"
        Write-Host "      Memory: $([math]::Round($proc.WorkingSet64/1MB, 2)) MB"
    }
}
else {
    Write-Host "  No running feedback processes found" -ForegroundColor Green
}
Write-Host ""

# Analyze execution history from Windows Event Log
Write-Host "Analyzing execution history..." -ForegroundColor Yellow

$startTime = (Get-Date).AddHours(-$Hours)
$executions = @()

try {
    # Event ID 102: Task started
    # Event ID 201: Task completed
    $events = Get-WinEvent -FilterHashtable @{
        LogName   = 'Microsoft-Windows-TaskScheduler/Operational'
        StartTime = $startTime
    } -ErrorAction SilentlyContinue | 
    Where-Object { $_.Message -like "*$TaskName*" -and ($_.Id -eq 102 -or $_.Id -eq 201) }
    
    $startEvents = $events | Where-Object { $_.Id -eq 102 }
    $endEvents = $events | Where-Object { $_.Id -eq 201 }
    
    Write-Host "  Found $($startEvents.Count) start events, $($endEvents.Count) completion events"
    
    # Calculate execution times
    $durations = @()
    foreach ($start in $startEvents) {
        $matchingEnd = $endEvents | 
        Where-Object { $_.TimeCreated -gt $start.TimeCreated } | 
        Sort-Object TimeCreated | 
        Select-Object -First 1
        
        if ($matchingEnd) {
            $duration = ($matchingEnd.TimeCreated - $start.TimeCreated).TotalSeconds
            $durations += [PSCustomObject]@{
                StartTime       = $start.TimeCreated
                EndTime         = $matchingEnd.TimeCreated
                DurationSeconds = $duration
            }
        }
        else {
            # No matching end event - might still be running
            $durations += [PSCustomObject]@{
                StartTime       = $start.TimeCreated
                EndTime         = "Still running?"
                DurationSeconds = ((Get-Date) - $start.TimeCreated).TotalSeconds
            }
        }
    }
    
    if ($durations.Count -gt 0) {
        Write-Host ""
        Write-Host "Execution History (Last $Hours hours):" -ForegroundColor Cyan
        $durations | Sort-Object StartTime -Descending | Select-Object -First 20 | ForEach-Object {
            $status = if ($_.EndTime -eq "Still running?") { 
                "[RUNNING]" 
            }
            elseif ($_.DurationSeconds -gt 300) { 
                "[LONG]" 
            }
            else { 
                "[OK]" 
            }
            $color = if ($status -eq "[RUNNING]") { "Yellow" } elseif ($status -eq "[LONG]") { "Red" } else { "Green" }
            Write-Host "  $status $($_.StartTime.ToString('HH:mm:ss')) → Duration: $([math]::Round($_.DurationSeconds, 1))s" -ForegroundColor $color
        }
        
        Write-Host ""
        Write-Host "Statistics:" -ForegroundColor Yellow
        $completedDurations = $durations | Where-Object { $_.EndTime -ne "Still running?" }
        if ($completedDurations.Count -gt 0) {
            $avgDuration = ($completedDurations.DurationSeconds | Measure-Object -Average).Average
            $maxDuration = ($completedDurations.DurationSeconds | Measure-Object -Maximum).Maximum
            $minDuration = ($completedDurations.DurationSeconds | Measure-Object -Minimum).Minimum
            
            Write-Host "  Completed Runs:  $($completedDurations.Count)"
            Write-Host "  Avg Duration:    $([math]::Round($avgDuration, 1))s"
            Write-Host "  Min Duration:    $([math]::Round($minDuration, 1))s"
            Write-Host "  Max Duration:    $([math]::Round($maxDuration, 1))s"
            
            $longRuns = $completedDurations | Where-Object { $_.DurationSeconds -gt 300 }
            if ($longRuns.Count -gt 0) {
                Write-Host "  Long Runs (>5m): $($longRuns.Count)" -ForegroundColor Yellow
            }
            
            $runningCount = $durations.Count - $completedDurations.Count
            if ($runningCount -gt 0) {
                Write-Host "  Currently Running: $runningCount" -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "  No completed runs found" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "  No execution history found in last $Hours hours" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  Could not access Task Scheduler event log: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "  (This is normal if running without admin privileges)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Recommendations:" -ForegroundColor Cyan

if ($taskInfo.LastTaskResult -eq 267009) {
    Write-Host "  [!] Task overlap detected (error 267009)" -ForegroundColor Yellow
    Write-Host "      - Python script takes longer than 5-minute interval"
    Write-Host "      - Consider: Increasing interval to 10 minutes"
    Write-Host "      - Or: Add ExecutionTimeLimit to task definition"
    Write-Host "      - Or: Optimize Python script performance"
}

if ($pythonProcesses) {
    foreach ($proc in $pythonProcesses) {
        $runtime = (Get-Date) - $proc.StartTime
        if ($runtime.TotalMinutes -gt 10) {
            Write-Host "  [!] Process PID $($proc.Id) running for $([int]$runtime.TotalMinutes) minutes" -ForegroundColor Red
            Write-Host "      - Consider killing hung process: Stop-Process -Id $($proc.Id)"
        }
    }
}

# Save to file if requested
if ($OutFile) {
    $report = @{
        TaskName         = $TaskName
        GeneratedAt      = Get-Date -Format "o"
        CurrentStatus    = @{
            State          = $task.State
            LastRunTime    = $taskInfo.LastRunTime
            LastTaskResult = $taskInfo.LastTaskResult
            NextRunTime    = $taskInfo.NextRunTime
            MissedRuns     = $taskInfo.NumberOfMissedRuns
        }
        RunningProcesses = $pythonProcesses | ForEach-Object {
            @{
                PID            = $_.Id
                StartTime      = $_.StartTime
                RuntimeMinutes = ((Get-Date) - $_.StartTime).TotalMinutes
                CPUTime        = $_.TotalProcessorTime.ToString()
                MemoryMB       = [math]::Round($_.WorkingSet64 / 1MB, 2)
            }
        }
        ExecutionHistory = $durations | Select-Object -First 50
    }
    
    $report | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutFile -Encoding utf8
    Write-Host "Report saved to: $OutFile" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Monitor Complete ===" -ForegroundColor Cyan
