param(
    [string]$LunchTime = "12:30",
    [string]$DinnerTime = "18:30",
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

function Get-WorkspaceRoot {
    $here = $PSScriptRoot
    if (-not $here) { $here = Split-Path -Parent $MyInvocation.MyCommand.Path }
    return (Split-Path -Parent $here)
}

$root = Get-WorkspaceRoot
$registerBreak = Join-Path $root 'scripts/register_break_maintenance_task.ps1'

if (-not (Test-Path -LiteralPath $registerBreak)) {
    Write-Host "register_break_maintenance_task.ps1 not found" -ForegroundColor Red
    exit 1
}

Write-Host "Applying circadian rhythm schedule..." -ForegroundColor Cyan

# 1) Lunch maintenance
if ($DryRun) {
    Write-Host "[DryRun] Would register Lunch maintenance at $LunchTime" -ForegroundColor Yellow
}
else {
    & $registerBreak -Register -Time $LunchTime -TaskName 'BreakMaintenance_Lunch' -Description 'Light maintenance at lunch'
}

# 2) Dinner maintenance
if ($DryRun) {
    Write-Host "[DryRun] Would register Dinner maintenance at $DinnerTime" -ForegroundColor Yellow
}
else {
    & $registerBreak -Register -Time $DinnerTime -TaskName 'BreakMaintenance_Dinner' -Description 'Light maintenance at dinner'
}

# 3) Night maintenance window (already aligned around 03:05~03:25 by existing tasks)
Write-Host "Night maintenance tasks are already aligned around 03:05~03:25 via existing register_* scripts (no changes)." -ForegroundColor DarkGray

Write-Host "Done." -ForegroundColor Green
exit 0
