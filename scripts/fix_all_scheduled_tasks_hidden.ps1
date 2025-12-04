# Fix all AGI scheduled tasks to run hidden
# This script updates all AGI-related scheduled tasks to:
# 1. Set Hidden = $true
# 2. Add -WindowStyle Hidden to PowerShell arguments

param(
    [switch]$DryRun,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Success($msg) { Write-Host "[SUCCESS] $msg" -ForegroundColor Green }
function Write-Err($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

# Get all AGI-related tasks
$agiTasks = Get-ScheduledTask | Where-Object { 
    $_.TaskName -like "AGI*" -or 
    $_.TaskName -like "Monitoring*" -or
    $_.TaskName -like "Binoche*" -or
    $_.TaskName -like "Bqi*" -or
    $_.TaskName -like "BQI*" -or
    $_.TaskName -like "AsyncThesis*" -or
    $_.TaskName -like "CacheValidation*" -or
    $_.TaskName -like "ReplanTrend*" -or
    $_.TaskName -like "AutoDream*" -or
    $_.TaskName -like "YouTubeLearner*" -or
    $_.TaskName -like "TaskQueue*" -or
    $_.TaskName -like "IonInbox*" -or
    $_.TaskName -like "BreakMaintenance*" -or
    $_.TaskName -like "Autopoietic*"
}

Write-Info "Found $($agiTasks.Count) AGI-related tasks"

$updated = 0
$failed = 0
$skipped = 0

foreach ($task in $agiTasks) {
    $taskName = $task.TaskName
    Write-Info "Processing: $taskName"
    
    try {
        $needsUpdate = $false
        
        # Check if Hidden is false
        if (-not $task.Settings.Hidden) {
            Write-Warn "  - Hidden is currently False"
            $needsUpdate = $true
        }
        
        # Check if -WindowStyle Hidden is missing from PowerShell arguments
        if ($task.Actions.Count -gt 0 -and $task.Actions[0].Execute -like "*powershell*") {
            $taskArgs = $task.Actions[0].Arguments
            if ($taskArgs -and $taskArgs -notlike "*-WindowStyle Hidden*") {
                Write-Warn "  - Missing -WindowStyle Hidden in arguments"
                $needsUpdate = $true
            }
        }
        
        if (-not $needsUpdate) {
            Write-Info "  - Already configured correctly"
            $skipped++
            continue
        }
        
        if ($DryRun) {
            Write-Info "  - Would update (DRY RUN)"
            $updated++
            continue
        }
        
        # Update the task
        $task.Settings.Hidden = $true
        
        if ($task.Actions.Count -gt 0 -and $task.Actions[0].Execute -like "*powershell*") {
            $taskArgs = $task.Actions[0].Arguments
            if ($taskArgs -and $taskArgs -notlike "*-WindowStyle Hidden*") {
                # Add -WindowStyle Hidden after -ExecutionPolicy Bypass
                $newArgs = $taskArgs -replace '(-ExecutionPolicy\s+Bypass)', '$1 -WindowStyle Hidden'
                $task.Actions[0].Arguments = $newArgs
            }
        }
        
        Set-ScheduledTask -TaskName $taskName -Action $task.Actions -Settings $task.Settings -ErrorAction Stop | Out-Null
        Write-Success "  - Updated successfully"
        $updated++
    }
    catch {
        Write-Err "  - Failed: $($_.Exception.Message)"
        if ($_.Exception.Message -like "*Access is denied*") {
            Write-Warn "  - Try running this script as Administrator"
        }
        $failed++
    }
}

Write-Host ""
Write-Info "Summary:"
Write-Success "  Updated: $updated"
Write-Warn "  Skipped: $skipped"
Write-Err "  Failed: $failed"

if ($failed -gt 0 -and -not $Force) {
    Write-Host ""
    Write-Warn "Some tasks failed to update. You may need to run this script as Administrator."
    Write-Info "To automatically retry with elevated privileges, run:"
    Write-Host "  Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"' -Verb RunAs" -ForegroundColor Cyan
}
