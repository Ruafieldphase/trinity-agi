#requires -Version 5.1
<#
.SYNOPSIS
Pre-reboot snapshot aggregator (safe to run manually or via scheduled task)

.DESCRIPTION
Runs the existing `pre_reboot_safety_check.ps1`, captures core health, then
adds supplemental continuity artifacts (goal tracker copy, ledger summary,
recent autonomous goals if present). Produces consolidated JSON + Markdown:
  outputs/pre_reboot_snapshot_latest.json
  outputs/pre_reboot_snapshot_latest.md

Return code is 0 unless an unexpected fatal error occurs. Safety degradation
is recorded in the JSON/MD but does not force non‑zero exit (so the task still
completes cleanly during shutdown).

.PARAMETER HoursLedger
Lookback window (hours) for ledger summary (default 12)

.PARAMETER OpenMd
Open the generated markdown in VS Code.

.NOTES
Designed to be invoked quickly during logoff/shutdown. Avoids any heavy
operations; Python ledger summarization is optional and skipped if unavailable.
#>
param(
    [int]$HoursLedger = 12,
    [switch]$OpenMd,
    [string]$OutJson = "${PSScriptRoot}/../outputs/pre_reboot_snapshot_latest.json",
    [string]$OutMd = "${PSScriptRoot}/../outputs/pre_reboot_snapshot_latest.md"
)

$ErrorActionPreference = 'Continue'

function Write-Info($m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Warn($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err($m) { Write-Host "[ERR ] $m" -ForegroundColor Red }

$workspace = Resolve-Path "$PSScriptRoot/.." | Select-Object -ExpandProperty Path
$outputs = Join-Path $workspace 'outputs'
if (!(Test-Path -LiteralPath $outputs)) { New-Item -ItemType Directory -Path $outputs -Force | Out-Null }

$result = [ordered]@{
    timestamp         = (Get-Date).ToString('s')
    workspace         = $workspace
    safety_check      = $null
    safety_exit       = $null
    goal_tracker      = $null
    ledger_summary_md = $null
    goals_recent      = $null
    degraded          = $false
    notes             = @()
}

Write-Info "Running pre_reboot_safety_check.ps1"
$safetyScript = Join-Path $PSScriptRoot 'pre_reboot_safety_check.ps1'
if (Test-Path -LiteralPath $safetyScript) {
    $safetyTempJson = Join-Path $outputs 'pre_reboot_check_latest.json'
    try {
        & $safetyScript -OutJson $safetyTempJson -OutMd (Join-Path $outputs 'pre_reboot_check_latest.md') | Out-Null
        $exitCode = $LASTEXITCODE
        $result.safety_exit = $exitCode
        if (Test-Path -LiteralPath $safetyTempJson) {
            $result.safety_check = Get-Content -LiteralPath $safetyTempJson -Raw | ConvertFrom-Json
            if ($exitCode -ne 0) { $result.degraded = $true; $result.notes += "Safety check exit code $exitCode" }
        }
        else { Write-Warn "Safety JSON not found"; $result.notes += 'Safety JSON missing' }
    }
    catch {
        Write-Err $_
        $result.notes += 'Safety script failed'
        $result.degraded = $true
    }
}
else {
    Write-Warn "pre_reboot_safety_check.ps1 not found; skipping core safety block"
    $result.notes += 'Safety script missing'
}

# Goal tracker copy
$goalTracker = Join-Path $workspace 'fdo_agi_repo/memory/goal_tracker.json'
if (Test-Path -LiteralPath $goalTracker) {
    try {
        $gtJson = Get-Content -LiteralPath $goalTracker -Raw | ConvertFrom-Json
        $result.goal_tracker = $gtJson
        Copy-Item -LiteralPath $goalTracker -Destination (Join-Path $outputs 'goal_tracker_pre_reboot.json') -Force
    }
    catch { Write-Warn "Goal tracker parse failed: $($_.Exception.Message)"; $result.notes += 'Goal tracker parse failed' }
}
else { Write-Warn 'Goal tracker not found'; $result.notes += 'Goal tracker missing' }

# Autonomous goals (recent)
$goalsFile = Join-Path $outputs 'autonomous_goals_latest.json'
if (Test-Path -LiteralPath $goalsFile) {
    try { $result.goals_recent = Get-Content -LiteralPath $goalsFile -Raw | ConvertFrom-Json } catch { Write-Warn 'Failed to parse autonomous_goals_latest.json' }
}

# Ledger summary (Python optional)
$py = $null
foreach ($candidate in @(
        (Join-Path $workspace 'fdo_agi_repo/.venv/Scripts/python.exe'),
        (Join-Path $workspace 'LLM_Unified/.venv/Scripts/python.exe'),
        'python'
    )) { if (Test-Path -LiteralPath $candidate) { $py = $candidate; break } }

$ledgerSummaryFile = Join-Path $outputs 'ledger_pre_reboot_summary.md'
if ($py) {
    $summarizeScript = Join-Path $workspace 'fdo_agi_repo/scripts/summarize_ledger.py'
    if (Test-Path -LiteralPath $summarizeScript) {
        Write-Info "Generating ledger summary ($HoursLedger h)"
        try {
            & $py $summarizeScript --last-hours $HoursLedger 2>$null | Out-Null
            if (Test-Path -LiteralPath (Join-Path $workspace 'fdo_agi_repo/outputs/ledger_summary_latest.md')) {
                Copy-Item -LiteralPath (Join-Path $workspace 'fdo_agi_repo/outputs/ledger_summary_latest.md') -Destination $ledgerSummaryFile -Force
                $result.ledger_summary_md = Get-Content -LiteralPath $ledgerSummaryFile -Raw
            }
        }
        catch { Write-Warn "Ledger summary failed: $($_.Exception.Message)"; $result.notes += 'Ledger summary failed' }
    }
    else { Write-Warn 'summarize_ledger.py not found'; $result.notes += 'Ledger summarize script missing' }
}
else { Write-Warn 'Python not available; skipping ledger summary'; $result.notes += 'Python missing' }

# Consolidated JSON
($result | ConvertTo-Json -Depth 8) | Out-File -LiteralPath $OutJson -Encoding UTF8

# Consolidated Markdown
$md = @()
$md += '# Pre-Reboot Snapshot'
$md += "- Timestamp: $($result.timestamp)"
$md += "- Workspace: $workspace"
$md += "- Degraded: $($result.degraded)"
if ($result.notes.Count -gt 0) { $md += "- Notes:"; foreach ($n in $result.notes) { $md += "  - $n" } }
$md += ''
$md += '## Safety Check (raw JSON excerpt)'
if ($result.safety_check) { $md += '```json'; $md += ($result.safety_check | ConvertTo-Json -Depth 4); $md += '```' } else { $md += '_No safety data_' }
$md += ''
$md += '## Goal Tracker (keys)'
if ($result.goal_tracker) { $md += (($result.goal_tracker.PSObject.Properties.Name | Sort-Object) -join ', ') } else { $md += '_Missing_' }
$md += ''
if ($result.goals_recent) {
    $md += '## Autonomous Goals (recent summary)'
    $recentTitles = @()
    foreach ($g in $result.goals_recent.goals) { if ($recentTitles.Count -ge 5) { break }; $recentTitles += $g.title }
    if ($recentTitles.Count -gt 0) { $md += "- Top goals: " + ($recentTitles -join '; ') }
}
$md += ''
$md += '## Ledger Summary (truncated)'
if ($result.ledger_summary_md) {
    $trunc = ($result.ledger_summary_md -split "`r?`n") | Select-Object -First 40
    $md += '```md'; $md += $trunc; $md += '```'
}
else { $md += '_No ledger summary_' }
$md += ''
$mdText = $md -join "`r`n"
$mdText | Out-File -LiteralPath $OutMd -Encoding UTF8
Write-Info "Snapshot written: $OutMd"; Write-Info "JSON: $OutJson"

if ($OpenMd) { try { Start-Process code $OutMd } catch {} }

exit 0