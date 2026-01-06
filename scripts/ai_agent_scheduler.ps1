# AI Agent Scheduler - Autonomous Background Monitoring
# Runs AI Performance Agent on a schedule for continuous monitoring

param(
    [int]$IntervalMinutes = 30,
    [int]$DurationMinutes = 1440,  # 24 hours default
    [switch]$AutoRecover,
    [switch]$KillExisting,
    [switch]$StopOnly
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$agentScript = Join-Path $scriptDir "ai_performance_agent.ps1"

$taskName = "AI_Performance_Agent_Monitor"

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "  AI Agent Scheduler" -ForegroundColor Cyan
Write-Host "======================================================================`n" -ForegroundColor Cyan

# Kill existing instances if requested
if ($KillExisting -or $StopOnly) {
    Write-Host "Stopping existing AI agent monitors..." -ForegroundColor Yellow
    $existing = Get-Process -Name 'pwsh', 'powershell' -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*ai_performance_agent.ps1*' -or
        $_.CommandLine -like '*ai_agent_scheduler*' -or
        $_.CommandLine -like '*ai_agent_monitor_*' }
    
    if ($existing) {
        $existing | Stop-Process -Force
        Write-Host "  Stopped $($existing.Count) agent process(es)" -ForegroundColor Green
    }
    else {
        Write-Host "  No existing agents found" -ForegroundColor Gray
    }
    
    if ($StopOnly) {
        Write-Host "`nAgent monitoring stopped." -ForegroundColor Green
        exit 0
    }
}

Write-Host "Starting AI Performance Agent monitor..." -ForegroundColor Cyan
Write-Host "  Interval: $IntervalMinutes minutes" -ForegroundColor Gray
Write-Host "  Duration: $DurationMinutes minutes" -ForegroundColor Gray
Write-Host "  Auto-Recovery: $(if ($AutoRecover) { 'ENABLED' } else { 'DISABLED' })" -ForegroundColor $(if ($AutoRecover) { 'Green' } else { 'Yellow' })
Write-Host ""

# Create monitoring loop script
$monitorScript = @"
`$ErrorActionPreference = 'Continue'
`$scriptDir = '$scriptDir'
`$agentScript = '$agentScript'
`$intervalSeconds = $IntervalMinutes * 60
`$endTime = (Get-Date).AddMinutes($DurationMinutes)
`$runCount = 0

Write-Host "[AI Agent Monitor] Started at `$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "[AI Agent Monitor] Will run until `$(`$endTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
Write-Host ""

while ((Get-Date) -lt `$endTime) {
    `$runCount++
    Write-Host "[Run #`$runCount] `$(Get-Date -Format 'HH:mm:ss') - Executing AI agent..." -ForegroundColor Cyan
    
    try {
        & "`$agentScript" $(if ($AutoRecover) { '-AutoRecover' }) -ErrorAction Stop
        Write-Host "[Run #`$runCount] Completed successfully" -ForegroundColor Green
    }
    catch {
        Write-Host "[Run #`$runCount] Error: `$(`$_.Exception.Message)" -ForegroundColor Red
    }
    
    if ((Get-Date) -lt `$endTime) {
        Write-Host "[Run #`$runCount] Next run in `$IntervalMinutes minutes..." -ForegroundColor Gray
        Start-Sleep -Seconds `$intervalSeconds
    }
}

Write-Host "`n[AI Agent Monitor] Completed `$runCount runs. Shutting down." -ForegroundColor Green
"@

# Save monitor script temporarily
$tempScript = Join-Path $env:TEMP "ai_agent_monitor_$([guid]::NewGuid()).ps1"
$monitorScript | Out-File -FilePath $tempScript -Encoding UTF8

# Start background monitoring
Write-Host "Launching background monitor..." -ForegroundColor Green

$proc = Start-Process powershell -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-WindowStyle", "Minimized",
    "-File", $tempScript
) -PassThru

# Write PID marker for diagnostics
try {
    $outputDir = Join-Path (Split-Path -Parent $scriptDir) "outputs"
    if (-not (Test-Path $outputDir)) { New-Item -ItemType Directory -Path $outputDir -Force | Out-Null }
    $pidFile = Join-Path $outputDir "ai_agent_monitor.pid"
    "PID=$($proc.Id); Started=$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); Script=$tempScript" | Out-File -FilePath $pidFile -Encoding UTF8
}
catch {
    Write-Host "Warning: Failed to write PID file: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "  AI Agent Monitor Started!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "The AI agent will run autonomously every $IntervalMinutes minutes." -ForegroundColor Cyan
Write-Host "Duration: $DurationMinutes minutes (~$([math]::Round($DurationMinutes / 60, 1)) hours)" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop the monitor:" -ForegroundColor Yellow
Write-Host "  powershell -NoProfile -ExecutionPolicy Bypass -File '$scriptDir\ai_agent_scheduler.ps1' -StopOnly" -ForegroundColor Gray
Write-Host ""

exit 0