<#
.SYNOPSIS
Verify all AGI scheduled tasks registration status

.DESCRIPTION
Checks all 22+ registered tasks and shows their schedule
#>

$ErrorActionPreference = 'Continue'

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  AGI Scheduled Tasks Verification                          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Get all AGI-related tasks
$tasks = Get-ScheduledTask | Where-Object { 
    $_.TaskPath -like "*\" -and 
    ($_.TaskName -match "AGI|Ion|BQI|Monitor|Cache|Trinity|Backup|Context|Lumen|Meta|Async|Evening|MidDay|Morning|Sleep|WakeUp|YouTube|Inbox")
} | Sort-Object TaskName

$registered = 0
$running = 0
$disabled = 0

Write-Host "📊 All Registered Tasks:`n" -ForegroundColor Yellow

foreach ($task in $tasks) {
    $registered++
    
    $statusColor = switch ($task.State) {
        "Ready" { "Green" }
        "Running" { "Cyan"; $running++ }
        "Disabled" { "Red"; $disabled++ }
        default { "Yellow" }
    }
    
    Write-Host "  [$($task.State)]" -ForegroundColor $statusColor -NoNewline
    Write-Host " $($task.TaskName)" -ForegroundColor White
    
    # Show trigger info
    $triggers = $task.Triggers
    if ($triggers) {
        foreach ($trigger in $triggers) {
            if ($trigger.StartBoundary) {
                $time = ([DateTime]$trigger.StartBoundary).ToString("HH:mm")
                Write-Host "      ⏰ $time" -ForegroundColor Gray
            }
            if ($trigger.Repetition.Interval) {
                Write-Host "      🔄 Every $($trigger.Repetition.Interval)" -ForegroundColor Gray
            }
        }
    }
    
    # Show next run
    if ($task.State -eq "Ready" -and $task.NextRunTime) {
        Write-Host "      ⏭️  Next: $($task.NextRunTime)" -ForegroundColor DarkGray
    }
}

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "📈 Summary:" -ForegroundColor Yellow
Write-Host "  Total Registered: $registered tasks" -ForegroundColor White
Write-Host "  Running: $running tasks" -ForegroundColor Cyan
Write-Host "  Ready: $($registered - $running - $disabled) tasks" -ForegroundColor Green
if ($disabled -gt 0) {
    Write-Host "  Disabled: $disabled tasks" -ForegroundColor Red
}

Write-Host "`n🎯 Expected Total: ~22 tasks" -ForegroundColor Gray
if ($registered -ge 20) {
    Write-Host "✅ Registration looks complete!" -ForegroundColor Green
}
elseif ($registered -ge 17) {
    Write-Host "⚠️  Close to complete (missing ~$($22 - $registered) tasks)" -ForegroundColor Yellow
}
else {
    Write-Host "❌ Many tasks missing (need ~$($22 - $registered) more)" -ForegroundColor Red
}

Write-Host "`n💡 Check specific tasks:" -ForegroundColor Cyan
Write-Host "  Get-ScheduledTask -TaskName 'Trinity*'" -ForegroundColor Gray
Write-Host "  Get-ScheduledTask -TaskName '*Backup*'" -ForegroundColor Gray
Write-Host "  Get-ScheduledTask -TaskName '*Cache*'" -ForegroundColor Gray
