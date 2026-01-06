#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Update AGI_FeedbackLoop scheduled task with adaptive interval
.DESCRIPTION
    Reads recommended interval from adaptive scheduler and updates
    the scheduled task trigger accordingly.
#>

param(
    [switch]$DryRun
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "WARN" { "Yellow" }
        "SUCCESS" { "Green" }
        default { "Cyan" }
    }
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
}

$taskName = "AGI_FeedbackLoop"
$recommendationPath = "$WorkspaceRoot\fdo_agi_repo\outputs\adaptive_feedback_interval.json"

# Check if recommendation exists
if (-not (Test-Path $recommendationPath)) {
    Write-Log "No recommendation found at: $recommendationPath" "WARN"
    Write-Log "Running adaptive scheduler..." "INFO"
    
    $py = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
    if (-not (Test-Path $py)) {
        $py = "python"
    }
    
    & $py "$WorkspaceRoot\fdo_agi_repo\scripts\rune\adaptive_feedback_scheduler.py"
    
    if (-not (Test-Path $recommendationPath)) {
        Write-Log "Failed to generate recommendation" "ERROR"
        exit 1
    }
}

# Read recommendation
$recommendation = Get-Content $recommendationPath | ConvertFrom-Json
$newInterval = $recommendation.interval_minutes
$reasoning = $recommendation.reasoning

Write-Log "Current recommendation: $newInterval minutes" "INFO"
Write-Log "  YouTube events (1h): $($reasoning.youtube_events_1h)" "INFO"
Write-Log "  RPA events (1h): $($reasoning.rpa_events_1h)" "INFO"
Write-Log "  CPU: $($reasoning.cpu_percent)%" "INFO"
Write-Log "  Memory: $($reasoning.memory_percent)%" "INFO"

# Get current task
try {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
}
catch {
    if ($DryRun) {
        Write-Log "Task '$taskName' not found (DryRun mode) — skipping update." "WARN"
        exit 0
    }
    Write-Log "Task '$taskName' not found" "ERROR"
    exit 1
}

# Get current trigger interval
$trigger = $task.Triggers[0]
if ($trigger.Repetition.Interval) {
    # Parse PT10M format
    if ($trigger.Repetition.Interval -match 'PT(\d+)M') {
        $currentInterval = [int]$Matches[1]
    }
    else {
        $currentInterval = 10  # default
    }
}
else {
    $currentInterval = 10
}

Write-Log "Current interval: $currentInterval minutes" "INFO"

if ($currentInterval -eq $newInterval) {
    Write-Log "No change needed" "SUCCESS"
    exit 0
}

Write-Log "Updating interval: $currentInterval → $newInterval minutes" "WARN"

if ($DryRun) {
    Write-Log "DRY RUN: Would update task trigger" "WARN"
    exit 0
}

# Update trigger
$newTrigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes $newInterval) `
    -RepetitionDuration (New-TimeSpan -Days 3650)

Set-ScheduledTask -TaskName $taskName -Trigger $newTrigger | Out-Null

Write-Log "Updated task trigger successfully" "SUCCESS"

# Show next run time
$info = Get-ScheduledTaskInfo -TaskName $taskName
Write-Log "Next run: $($info.NextRunTime)" "INFO"

exit 0