<#
Resilient Reboot Recovery - Smoke Test

Validates that outputs/resilient_reboot_recovery_summary.json exists and has a sane minimal shape.
If missing or when -Regenerate is provided, it will invoke scripts/resilient_reboot_recovery.ps1
in DryRun mode to generate it quickly.
#>
param(
    [string]$SummaryPath = '',
    [switch]$Regenerate,
    [switch]$Verbose
)

$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot

function Find-RepoRoot([string]$startDir) {
    try { $dir = Get-Item -LiteralPath $startDir } catch { return (Split-Path -Parent (Split-Path -Parent $startDir)) }
    for ($i = 0; $i -lt 6; $i++) {
        $p = Join-Path $dir.FullName 'scripts\resilient_reboot_recovery.ps1'
        if (Test-Path -LiteralPath $p) { return $dir.FullName }
        if (-not $dir.Parent) { break }
        $dir = $dir.Parent
    }
    return (Split-Path -Parent (Split-Path -Parent $startDir))
}

$root = Find-RepoRoot -startDir $here
$scriptsDir = Join-Path $root 'scripts'
if (-not $SummaryPath -or $SummaryPath.Trim().Length -eq 0) { $SummaryPath = Join-Path $root 'outputs/resilient_reboot_recovery_summary.json' }

function Write-Info([string]$m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Ok([string]$m) { Write-Host "[ OK ] $m" -ForegroundColor Green }
function Write-Warn([string]$m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err([string]$m) { Write-Host "[ERR ] $m" -ForegroundColor Red }

$recoveryPs1 = Join-Path $scriptsDir 'resilient_reboot_recovery.ps1'
if (-not (Test-Path -LiteralPath $recoveryPs1)) { Write-Err "Missing: $recoveryPs1"; exit 2 }

$needGen = $Regenerate -or (-not (Test-Path -LiteralPath $SummaryPath))
if ($needGen) {
    Write-Info "Generating recovery summary JSON (DryRun) -> $SummaryPath"
    & $recoveryPs1 -DryRun -DelaySeconds 0 | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Err "resilient_reboot_recovery.ps1 failed (code=$LASTEXITCODE)"; exit 2 }
}

if (-not (Test-Path -LiteralPath $SummaryPath)) { Write-Err "Missing JSON: $SummaryPath"; exit 2 }

try { $raw = Get-Content -LiteralPath $SummaryPath -Raw -Encoding UTF8 }
catch {
    $msg = $_.Exception.Message
    Write-Err ("Failed to read {0}: {1}" -f $SummaryPath, $msg)
    exit 2
}
if (-not $raw -or $raw.Trim().Length -eq 0) { Write-Err "Empty JSON: $SummaryPath"; exit 2 }

try { $obj = $raw | ConvertFrom-Json }
catch {
    $msg = $_.Exception.Message
    Write-Err ("Invalid JSON: {0}" -f $msg)
    exit 2
}

if ($null -eq $obj) { Write-Err "Parsed object is null"; exit 2 }

# Accept older minimal form and newer enriched form
# Required: timestamp (any case), steps (array), runMode or dryRun

$tsVal = $obj.timestamp
if ($null -eq $tsVal -and $null -ne $obj.Timestamp) { $tsVal = $obj.Timestamp }
if ($null -eq $tsVal) { Write-Err "Missing timestamp"; exit 2 }
try { [void][DateTime]::Parse($tsVal, [Globalization.CultureInfo]::InvariantCulture) } catch { Write-Err "timestamp not parseable: $tsVal"; exit 2 }

if ($null -eq $obj.steps -or -not ($obj.steps -is [System.Array]) -or $obj.steps.Count -lt 1) { Write-Err "steps missing or empty"; exit 2 }

# Check step entries have required fields
foreach ($s in $obj.steps) {
    if ($null -eq $s.name -or [string]::IsNullOrWhiteSpace([string]$s.name)) { Write-Err "step.name missing"; exit 2 }
    if ($null -eq $s.status -or [string]::IsNullOrWhiteSpace([string]$s.status)) { Write-Err "step.status missing"; exit 2 }
}

# Run mode coherence
$hasDry = ($null -ne $obj.dryRun)
$hasMode = ($null -ne $obj.runMode)
if ($hasDry -and $hasMode) {
    $expected = 'execute'
    if ($obj.dryRun) { $expected = 'dryrun' }
    if ([string]$obj.runMode -ne $expected) { Write-Err "runMode '$($obj.runMode)' inconsistent with dryRun=$($obj.dryRun)"; exit 2 }
}

# If success/errorCount present, verify coherence
if ($null -ne $obj.errorCount -and $null -ne $obj.success) {
    $ec = [int]$obj.errorCount
    $succ = [bool]$obj.success
    if (($ec -eq 0) -and (-not $succ)) { Write-Err "errorCount=0 but success=false"; exit 2 }
    if (($ec -gt 0) -and $succ) { Write-Err "errorCount>0 but success=true"; exit 2 }
    if ($ec -eq 0 -and $null -ne $obj.firstFailureStep -and [string]$obj.firstFailureStep -ne '') {
        Write-Err "firstFailureStep should be null/empty when errorCount=0"; exit 2
    }
}

# Duration sanity if present
if ($null -ne $obj.durationMs) {
    if ([int]$obj.durationMs -lt 0) { Write-Err "durationMs < 0"; exit 2 }
}

Write-Ok "resilient_reboot_recovery_summary.json looks sane at ${SummaryPath}. Steps=$($obj.steps.Count)"
exit 0
