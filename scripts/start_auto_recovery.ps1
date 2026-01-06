# Start Auto Recovery System in Background
param(
    [int]$CheckIntervalSeconds = 300,
    [switch]$KillExisting,
    [switch]$Status
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$recoveryScript = Join-Path $scriptDir "auto_recovery_system.ps1"

# Status check
if ($Status) {
    Write-Host "`nAuto Recovery System Status`n" -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Gray
    
    $processes = Get-Process -Name "pwsh", "powershell" -ErrorAction SilentlyContinue | 
    Where-Object { $_.CommandLine -like "*auto_recovery_system.ps1*" }
    
    if ($processes) {
        Write-Host "  Status: RUNNING" -ForegroundColor Green
        Write-Host "`n  Processes:" -ForegroundColor Cyan
        $processes | Format-Table Id, ProcessName, CPU, @{Label = "Memory(MB)"; Expression = { [math]::Round($_.WorkingSet64 / 1MB, 2) } } -AutoSize
    }
    else {
        Write-Host "  Status: NOT RUNNING" -ForegroundColor Yellow
    }
    
    Write-Host ("=" * 60) -ForegroundColor Gray
    Write-Host ""
    exit 0
}

# Kill existing
if ($KillExisting) {
    Write-Host "Stopping existing recovery processes..." -ForegroundColor Yellow
    Get-Process -Name "pwsh", "powershell" -ErrorAction SilentlyContinue | 
    Where-Object { $_.CommandLine -like "*auto_recovery_system.ps1*" } | 
    Stop-Process -Force
    Write-Host "  Done" -ForegroundColor Green
    Write-Host ""
}

# Start new
Write-Host "`n" -NoNewline
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "`n  Starting Auto Recovery System`n" -ForegroundColor Yellow
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "`n"

Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Check Interval: ${CheckIntervalSeconds}s" -ForegroundColor Gray
Write-Host "  Script: $recoveryScript" -ForegroundColor Gray
Write-Host ""

# Start in background job
$job = Start-Job -ScriptBlock {
    param($Script, $Interval)
    & $Script -CheckIntervalSeconds $Interval -SendAlert
} -ArgumentList $recoveryScript, $CheckIntervalSeconds

Write-Host "Auto Recovery System started!" -ForegroundColor Green
Write-Host "  Job ID: $($job.Id)" -ForegroundColor Cyan
Write-Host "  Job Name: $($job.Name)" -ForegroundColor Cyan
Write-Host ""

Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "`nUsage:" -ForegroundColor Yellow
Write-Host "  Check status:  .\start_auto_recovery.ps1 -Status" -ForegroundColor Gray
Write-Host "  Stop system:   .\stop_auto_recovery.ps1" -ForegroundColor Gray
Write-Host "  View logs:     Get-Content ..\outputs\auto_recovery_log.jsonl -Tail 10" -ForegroundColor Gray
Write-Host "`n"