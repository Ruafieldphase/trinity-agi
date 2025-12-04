#requires -Version 5.1
Param(
    [int]$WarnCpuPercent = 90,
    [int]$WarnMinAvailMB = 512,
    [int]$MinWorkers = 1,
    [switch]$RequireWatchdog,
    [string]$OutJson = "${PSScriptRoot}/../outputs/pre_reboot_check_latest.json",
    [string]$OutMd = "${PSScriptRoot}/../outputs/pre_reboot_check_latest.md",
    [switch]$OpenMd
)

$ErrorActionPreference = 'Continue'

function Invoke-Step($Name, [scriptblock]$Block) {
    Write-Host ("==> " + $Name) -ForegroundColor Cyan
    try { & $Block } catch { Write-Host ("   ERROR: " + $_.Exception.Message) -ForegroundColor Red }
}

$ws = Resolve-Path "$PSScriptRoot/.." | Select-Object -ExpandProperty Path
$outputs = Join-Path $ws 'outputs'
if (!(Test-Path -LiteralPath $outputs)) { New-Item -ItemType Directory -Path $outputs -Force | Out-Null }

$report = [ordered]@{
    timestamp = (Get-Date).ToString('s')
    workspace = $ws
    core      = $null
    queue     = $null
    system    = $null
    summary   = @()
}

Invoke-Step 'Core process check' {
    $coreJson = & "$PSScriptRoot/check_core_processes.ps1" -WarnCpuPercent $WarnCpuPercent -WarnMinAvailMB $WarnMinAvailMB -MinWorkers $MinWorkers -RequireWatchdog:$RequireWatchdog
    $core = $coreJson | ConvertFrom-Json
    $report.core = $core
    if ($core.status -ne 'ok') { $report.summary += "Core degraded: $($core.issues -join '; ')" }
}

Invoke-Step 'Task Queue health' {
    $queueHealth = & "$ws/scripts/queue_health_check.ps1"
    $report.queue = @{ raw = $queueHealth }
}

Invoke-Step 'Unified quick status' {
    $sys = & "$ws/scripts/quick_status.ps1"
    $report.system = @{ raw = $sys }
}

# Save JSON
($report | ConvertTo-Json -Depth 6) | Out-File -LiteralPath $OutJson -Encoding UTF8
Write-Host "Saved JSON: $OutJson" -ForegroundColor Green

# Build Markdown summary
$md = @()
$md += "# Pre-Reboot Safety Check"
$md += "- Timestamp: $($report.timestamp)"
$md += "- Workspace: $($report.workspace)"
$md += ""
$md += "## Core Processes"
if ($report.core) {
    $md += "- Status: **$($report.core.status)**"
    $md += "- RPA Workers: $($report.core.counts.rpa_workers)"
    $md += "- Watchdogs: $($report.core.counts.watchdogs)"
    $md += "- Monitors: $($report.core.counts.monitors)"
    $md += "- CPU: $($report.core.host.cpu_percent_total)%  |  Free RAM: $($report.core.host.mem_available_mb) MB"
    if ($report.core.issues.Count -gt 0) { $md += ("- Issues: " + ($report.core.issues -join '; ')) }
}
$md += ""
$md += "## Task Queue Health"
$md += '```
'+ ($report.queue.raw | Out-String).Trim() + '
```'
$md += ""
$md += "## Unified Status"
$md += '```
'+ ($report.system.raw | Out-String).Trim() + '
```'
$md += ""
if ($report.summary.Count -gt 0) {
    $md += "## Summary"
    foreach ($s in $report.summary) { $md += "- $s" }
}

$mdText = ($md -join "`r`n")
$mdText | Out-File -LiteralPath $OutMd -Encoding UTF8
Write-Host "Saved MD: $OutMd" -ForegroundColor Green

if ($OpenMd) { Start-Process code $OutMd }

if ($report.core -and $report.core.status -ne 'ok') { exit 2 } else { exit 0 }
param(
    [string]$OutJson = "${PSScriptRoot}/../outputs/pre_reboot_check_latest.json",
    [string]$OutMd = "${PSScriptRoot}/../outputs/pre_reboot_check_latest.md",
    [int]$WarnCpuPercent = 90,
    [int]$WarnMinAvailMB = 512,
    [int]$MinWorkers = 1,
    [switch]$RequireWatchdog
)

$ErrorActionPreference = 'SilentlyContinue'

function Invoke-Step {
    param([string]$Name, [scriptblock]$Block)
    Write-Host "[CHECK] $Name" -ForegroundColor Cyan
    try { & $Block } catch { Write-Host "  -> $($_.Exception.Message)" -ForegroundColor Yellow }
}

$report = [ordered]@{
    timestamp = (Get-Date).ToString('s')
    checks    = @{}
}

# 1) Core processes and host pressure
Invoke-Step 'Core Processes' {
    $core = & "${PSScriptRoot}/check_core_processes.ps1" -WarnCpuPercent $WarnCpuPercent -WarnMinAvailMB $WarnMinAvailMB -MinWorkers $MinWorkers -RequireWatchdog:$RequireWatchdog
    $report.checks.core = $core | ConvertFrom-Json
}

# 2) System health (built-in)
Invoke-Step 'System Health (Full)' {
    $sys = & "${PSScriptRoot}/system_health_check.ps1" -Full 2>$null
    $report.checks.system_health = $sys
}

# 3) Queue health (8091)
Invoke-Step 'Queue Health' {
    $queue = & "${PSScriptRoot}/queue_health_check.ps1" 2>$null
    $report.checks.queue_health = $queue
}

# 4) Quick unified status (AGI + Lumen)
Invoke-Step 'Unified Quick Status' {
    $qs = & "${PSScriptRoot}/quick_status.ps1" 2>$null
    $report.checks.quick_status = $qs
}

# 5) Optional Original Data API (8093) health if server seems online
Invoke-Step 'Original Data API (8093) Health' {
    try {
        $resp = Invoke-RestMethod -Uri 'http://127.0.0.1:8093/health' -TimeoutSec 2
        $report.checks.original_data_api = $resp
    }
    catch {
        $report.checks.original_data_api = @{ status = 'offline' }
    }
}

# Decide status + write outputs
$issues = @()
if ($report.checks.core.status -ne 'ok') { $issues += 'Core processes degraded' }
$overall = if ($issues.Count -gt 0) { 'needs-attention' } else { 'ok' }
$report.status = $overall
$report.issues = $issues

New-Item -ItemType Directory -Path (Split-Path -Parent $OutJson) -Force | Out-Null
$report | ConvertTo-Json -Depth 8 | Out-File -FilePath $OutJson -Encoding UTF8

$md = @()
$md += "# Pre-Reboot Safety Check"
$md += "- Timestamp: $($report.timestamp)"
$md += "- Status: $overall"
if ($issues.Count -gt 0) { $md += "- Issues: `n  - " + ($issues -join "`n  - ") } else { $md += "- Issues: None" }
$md += "\n## Core Processes"
$md += ( $report.checks.core | ConvertTo-Json -Depth 6 )
$md += "\n## Queue Health"
$md += ( $report.checks.queue_health | Out-String )
$md += "\n## Quick Status"
$md += ( $report.checks.quick_status | Out-String )
$md += "\n## Original Data API (8093)"
$md += ( $report.checks.original_data_api | ConvertTo-Json -Depth 6 )

$md -join "`n" | Out-File -FilePath $OutMd -Encoding UTF8

Write-Host "Pre-reboot check completed -> JSON: $OutJson, MD: $OutMd" -ForegroundColor Green
if ($overall -ne 'ok') { exit 2 } else { exit 0 }
