# Quick Replan Rate Check Script
# 최근 N개 task의 실시간 ReplanRate 측정

param(
    [int]$LastTasks = 10,
    [string]$WorkspaceRoot = "C:\workspace\agi"
)

$ErrorActionPreference = 'Stop'
$ledger = Join-Path $WorkspaceRoot "fdo_agi_repo\memory\resonance_ledger.jsonl"

Write-Host "`n=== Quick ReplanRate Check (Last $LastTasks tasks) ===" -ForegroundColor Cyan

# Get last N tasks
$lines = Get-Content $ledger -Tail 500
$events = $lines | ForEach-Object { 
    try { $_ | ConvertFrom-Json } catch { $null }
} | Where-Object { $_ -ne $null }

# Find unique task completions
$completedTasks = $events | 
Where-Object { $_.event -eq 'task_end' } |
Select-Object -Last $LastTasks

Write-Host "Found $($completedTasks.Count) recent task completions`n"

$secondPassCount = 0
$totalTasks = $completedTasks.Count

foreach ($task in $completedTasks) {
    $taskId = $task.task_id
    $timestamp = $task.timestamp
    
    # Check if this task had second_pass
    $hadSecondPass = $events | Where-Object { 
        $_.task_id -eq $taskId -and $_.event -eq 'second_pass'
    }
    
    if ($hadSecondPass) {
        $secondPassCount++
        Write-Host "  ⚠️  $taskId - Had second_pass" -ForegroundColor Yellow
    }
    else {
        Write-Host "  ✅ $taskId - No replan" -ForegroundColor Green
    }
}

$replanRate = if ($totalTasks -gt 0) { 
    [math]::Round(($secondPassCount / $totalTasks) * 100, 2) 
}
else { 
    0 
}

Write-Host "`n=== Results ===" -ForegroundColor Cyan
Write-Host "Total tasks analyzed: $totalTasks"
Write-Host "Second pass occurred: $secondPassCount"
Write-Host "ReplanRate: $replanRate%" -ForegroundColor $(
    if ($replanRate -lt 10) { 'Green' }
    elseif ($replanRate -lt 20) { 'Yellow' }
    else { 'Red' }
)

Write-Host "`nComparison:" -ForegroundColor Cyan
Write-Host "  Previous (overall): 32.66%"
Write-Host "  Current (last $LastTasks): $replanRate%"
Write-Host "  Improvement: $([math]::Round(32.66 - $replanRate, 2))%" -ForegroundColor Green

exit 0
