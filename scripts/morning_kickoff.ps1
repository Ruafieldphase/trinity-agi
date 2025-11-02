#Requires -Version 5.1
<#
.SYNOPSIS
    Morning kickoff: quick health + monitoring report + optional dashboard open.
.EXAMPLE
    .\morning_kickoff.ps1 -Hours 1 -OpenHtml
#>

param(
    [int]$Hours = 1,
    [switch]$OpenHtml,
    [switch]$WithStatus
)

$ErrorActionPreference = "Continue"
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::UTF8 } catch {}

Write-Host "`n===============================================" -ForegroundColor Cyan
Write-Host "|   Morning Kickoff                           |" -ForegroundColor Cyan
Write-Host "===============================================`n" -ForegroundColor Cyan

$root = Split-Path -Parent $PSScriptRoot
$dashboardPath = Join-Path $root 'outputs\monitoring_dashboard_latest.html'

function Invoke-ScriptIfExists {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [string[]]$Args
    )
    if (Test-Path -LiteralPath $Path) {
        & $Path @Args
        return $true
    }
    return $false
}

# 1) Quick health/status
Write-Host "[1/3] Running quick health/status..." -ForegroundColor Yellow
$ran = $false
$ran = Invoke-ScriptIfExists -Path (Join-Path $PSScriptRoot 'quick_status.ps1') -Args @()
if (-not $ran) { $ran = Invoke-ScriptIfExists -Path (Join-Path $PSScriptRoot 'system_health_check.ps1') -Args @() }
if ($ran) { Write-Host "  Health/status complete." -ForegroundColor Green } else { Write-Host "  Skipped (no script found)." -ForegroundColor Gray }

# 2) Monitoring report (JSON/MD/HTML)
Write-Host "`n[2/3] Generating monitoring report..." -ForegroundColor Yellow
$reportScript = Join-Path $PSScriptRoot 'generate_monitoring_report.ps1'
if (Test-Path -LiteralPath $reportScript) {
    $ok = $true
    try {
        & $reportScript -Hours $Hours
        if ($LASTEXITCODE -ne 0) { $ok = $false }
    } catch { $ok = $false }
    if ($ok) {
        Write-Host "  Monitoring report generated." -ForegroundColor Green
        if ($OpenHtml -and (Test-Path -LiteralPath $dashboardPath)) {
            try { Start-Process -FilePath $dashboardPath } catch {}
            Write-Host "  Opened: $dashboardPath" -ForegroundColor Gray
        }
    }
    else {
        Write-Host "  Warning: report generation failed (see console)." -ForegroundColor Yellow
    }
}
else {
    Write-Host "  Skipped (generate_monitoring_report.ps1 not found)." -ForegroundColor Gray
}

# 3) Summary
if ($WithStatus) {
    Write-Host "`n[3/4] Resonance quick status..." -ForegroundColor Yellow
    $rs = Join-Path $PSScriptRoot 'quick_resonance_status.ps1'
    if (Test-Path -LiteralPath $rs) {
        try { & $rs -ShowLedger | Out-Host } catch { Write-Host "  quick_resonance_status errored: $($_.Exception.Message)" -ForegroundColor Yellow }
    } else { Write-Host "  Skipped (quick_resonance_status.ps1 not found)." -ForegroundColor Gray }

    Write-Host "`n[4/4] Last task latency summary..." -ForegroundColor Yellow
    $py = if (Test-Path "$root/.venv/Scripts/python.exe") { "$root/.venv/Scripts/python.exe" } else { 'python' }
    $sum = Join-Path $PSScriptRoot 'summarize_last_task_latency.py'
    if (Test-Path -LiteralPath $sum) {
        try { & $py $sum | Out-Host } catch { Write-Host "  summarize_last_task_latency errored: $($_.Exception.Message)" -ForegroundColor Yellow }
    } else { Write-Host "  Skipped (summarize_last_task_latency.py not found)." -ForegroundColor Gray }
}

Write-Host "`n[3/3] Summary" -ForegroundColor Yellow
Write-Host ("  Time Window: Last {0} hour(s)" -f $Hours) -ForegroundColor Gray
if (Test-Path -LiteralPath (Join-Path $root 'outputs\monitoring_metrics_latest.json')) {
    Write-Host "  Metrics: outputs\\monitoring_metrics_latest.json" -ForegroundColor Gray
}
if (Test-Path -LiteralPath (Join-Path $root 'outputs\monitoring_report_latest.md')) {
    Write-Host "  Report:  outputs\\monitoring_report_latest.md" -ForegroundColor Gray
}
if (Test-Path -LiteralPath $dashboardPath) {
    Write-Host "  Dashboard: $dashboardPath" -ForegroundColor Gray
}

Write-Host "`nMorning kickoff complete." -ForegroundColor Cyan

exit 0
