[CmdletBinding()]
param(
    [int]$ProbeTimeoutSec = 8,
    [int]$ProbeAttempts = 3,
    [int]$ProbeBackoffMs = 300,
    [int]$SummaryHours = 24,
    [int]$DashboardDays = 7
)

$ErrorActionPreference = 'Continue'

try { chcp 65001 > $null 2> $null } catch {}
try {
    [Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false, $false)
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false, $false)
    $global:OutputEncoding = New-Object System.Text.UTF8Encoding($false, $false)
} catch {}

$root = Split-Path -Parent $PSScriptRoot

Write-Host "=== Core Probe (latest) ===" -ForegroundColor Cyan
& (Join-Path $root 'scripts/run_core_probe.ps1') -TimeoutSec $ProbeTimeoutSec -Attempts $ProbeAttempts -BackoffMs $ProbeBackoffMs -Tag 'quick-scan' -OpenLatest

Write-Host "`n=== Core Probe Summary (${SummaryHours}h) ===" -ForegroundColor Cyan
& (Join-Path $root 'scripts/generate_core_probe_summary.ps1') -Hours $SummaryHours -OpenMd

Write-Host "`n=== Performance Dashboard (${DashboardDays}d) ===" -ForegroundColor Cyan
& (Join-Path $root 'scripts/generate_performance_dashboard.ps1') -Days $DashboardDays -ExportJson -WriteLatest -OpenDashboard

Write-Host "`nQuick scan complete." -ForegroundColor Green
exit 0
