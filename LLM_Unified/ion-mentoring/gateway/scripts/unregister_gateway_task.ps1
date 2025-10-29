<#
.SYNOPSIS
    Unregister Lumen Gateway scheduled task
    
.DESCRIPTION
    Removes the scheduled task for Gateway auto-start
    
.PARAMETER TaskName
    Name of the scheduled task to remove (default: LumenGatewayAutoStart)
    
.PARAMETER Force
    Skip confirmation prompt
    
.EXAMPLE
    .\unregister_gateway_task.ps1
    Remove task with confirmation
    
.EXAMPLE
    .\unregister_gateway_task.ps1 -Force
    Remove task without confirmation
#>

param(
    [string]$TaskName = "LumenGatewayAutoStart",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Lumen Gateway Task Unregistration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if task exists
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if (-not $task) {
    Write-Host "⚠️  Task '$TaskName' not found" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Available tasks:" -ForegroundColor Cyan
    Get-ScheduledTask | Where-Object { $_.TaskName -like "*Gateway*" -or $_.TaskName -like "*Lumen*" } | 
    Format-Table TaskName, State, LastRunTime -AutoSize
    exit 0
}

Write-Host "Found task: $TaskName" -ForegroundColor White
Write-Host "  State:        $($task.State)" -ForegroundColor Gray
Write-Host "  Last Run:     $($task.LastRunTime)" -ForegroundColor Gray
Write-Host "  Next Run:     $($task.NextRunTime)" -ForegroundColor Gray
Write-Host ""

# Confirmation
if (-not $Force) {
    $response = Read-Host "Are you sure you want to remove this task? (y/N)"
    if ($response -notmatch '^[Yy]') {
        Write-Host "❌ Unregistration cancelled" -ForegroundColor Red
        exit 0
    }
}

# Stop task if running
Write-Host "🛑 Stopping task if running..." -ForegroundColor Cyan
try {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Write-Host "✅ Task stopped" -ForegroundColor Green
}
catch {
    Write-Host "⚠️  Task was not running" -ForegroundColor Yellow
}

# Unregister task
Write-Host ""
Write-Host "🗑️  Removing scheduled task..." -ForegroundColor Cyan

try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
    Write-Host "✅ Task removed successfully!" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to remove task: $_" -ForegroundColor Red
    exit 1
}

# Verify removal
Write-Host ""
Write-Host "🔍 Verifying removal..." -ForegroundColor Cyan

$verifyTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($verifyTask) {
    Write-Host "⚠️  Task still exists (removal may have failed)" -ForegroundColor Yellow
}
else {
    Write-Host "✅ Task removed successfully (verified)" -ForegroundColor Green
}

Write-Host ""
Write-Host "✅ Unregistration complete!" -ForegroundColor Green
Write-Host ""
