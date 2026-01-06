param(
    [switch]$VerboseOutput
)

$ErrorActionPreference = "Stop"

# Resolve paths
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$outDir   = Join-Path $repoRoot 'outputs'

function Fail($msg) {
    Write-Host "[FAIL] $msg" -ForegroundColor Red
    exit 1
}

function Ok($msg) {
    Write-Host "[OK]   $msg" -ForegroundColor Green
}

function Normalize-Band {
    param([Parameter(Mandatory=$true)][string]$Band)
    switch ($Band) {
        'NoData' { 'No Data'; break }
        'Needs'  { 'Needs Attention'; break }
        default  { $Band }
    }
}

if (-not (Test-Path $outDir)) { Fail "Outputs directory not found: $outDir" }

# JSON: performance_metrics_latest.json
$jsonLatest = Join-Path $outDir 'performance_metrics_latest.json'
if (-not (Test-Path $jsonLatest)) { Fail "Missing JSON latest: $jsonLatest" }

try {
    $j = Get-Content $jsonLatest -Raw | ConvertFrom-Json
}
catch {
    Fail ("Invalid JSON in {0}: {1}" -f $jsonLatest, $_.Exception.Message)
}

# Required fields
$requiredJsonFields = @('Generated','Period','OverallSuccessRate','OverallEffectiveSuccessRate','Systems','SystemsConsidered','Filters','Sort','TopAttentionCount')
foreach ($f in $requiredJsonFields) {
    if (-not ($j.PSObject.Properties.Name -contains $f)) { Fail "JSON missing field: $f" }
}

# New enriched fields
if (-not ($j.PSObject.Properties.Name -contains 'SystemsFiltered')) { Fail "JSON missing field: SystemsFiltered" }
if (-not ($j.PSObject.Properties.Name -contains 'VisibleSystems')) { Fail "JSON missing field: VisibleSystems" }

# Numeric sanity
if (-not ([double]::TryParse([string]$j.OverallSuccessRate, [ref]([double]0)))) { Fail "OverallSuccessRate not numeric" }
if (-not ([double]::TryParse([string]$j.OverallEffectiveSuccessRate, [ref]([double]0)))) { Fail "OverallEffectiveSuccessRate not numeric" }

Ok "JSON fields validated: $jsonLatest"

# CSV: performance_metrics_latest.csv
$csvLatest = Join-Path $outDir 'performance_metrics_latest.csv'
if (-not (Test-Path $csvLatest)) { Fail "Missing CSV latest: $csvLatest" }

try {
    $rows = Import-Csv $csvLatest
}
catch {
    Fail ("Invalid CSV in {0}: {1}" -f $csvLatest, $_.Exception.Message)
}

if ($rows.Count -gt 0) {
    $headers = $rows[0].PSObject.Properties.Name
    foreach ($h in @('System','Band','TotalRuns','Passed','Failed','Skipped','SuccessRate','EffectiveRuns','EffectiveSuccessRate','LastStatus')) {
        if (-not ($headers -contains $h)) { Fail "CSV missing column: $h" }
    }
}
else {
    Write-Host "CSV has no rows; header validation skipped" -ForegroundColor Yellow
}

Ok "CSV columns validated: $csvLatest"

# BandsConsidered semantics (when present)
if ($j.PSObject.Properties.Name -contains 'BandsConsidered') {
    $expectedBands = @()
    if ($j.Filters -and $j.Filters.Bands) {
        foreach ($b in @($j.Filters.Bands)) { if ($b) { $expectedBands += (Normalize-Band -Band [string]$b) } }
    }
    $actualBands = @()
    foreach ($b in @($j.BandsConsidered)) { if ($b) { $actualBands += [string]$b } }

    if ($expectedBands.Count -eq 0 -and $actualBands.Count -gt 0) {
        Fail "BandsConsidered present but Filters.Bands is empty"
    }
    elseif ($expectedBands.Count -gt 0) {
        $expSet = [System.Collections.Generic.HashSet[string]]::new($expectedBands, [System.StringComparer]::Ordinal)
        $actSet = [System.Collections.Generic.HashSet[string]]::new($actualBands, [System.StringComparer]::Ordinal)
        if (-not ($expSet.SetEquals($actSet))) {
            Fail ("BandsConsidered mismatch. expected={0}; actual={1}" -f ($expectedBands -join ','), ($actualBands -join ','))
        }
    }
    Ok "BandsConsidered semantics validated"
}

# TopFailureReasons structure (when present)
if ($j.PSObject.Properties.Name -contains 'TopFailureReasons') {
    $tfr = $j.TopFailureReasons
    if ($tfr) {
        foreach ($entry in @($tfr)) {
            if (-not ($entry.PSObject.Properties.Name -contains 'System')) { Fail "TopFailureReasons entry missing 'System'" }
            if (-not ($entry.PSObject.Properties.Name -contains 'Reasons')) { Fail "TopFailureReasons entry missing 'Reasons'" }
            $sys = [string]$entry.System
            if ([string]::IsNullOrWhiteSpace($sys)) { Fail "TopFailureReasons.System is empty" }
            foreach ($r in @($entry.Reasons)) {
                if (-not ($r.PSObject.Properties.Name -contains 'Error')) { Fail "TopFailureReasons.Reasons missing 'Error'" }
                if (-not ($r.PSObject.Properties.Name -contains 'Count')) { Fail "TopFailureReasons.Reasons missing 'Count'" }
                $cnt = [int]$r.Count
                if ($cnt -lt 0) { Fail "TopFailureReasons.Count negative: $cnt" }
            }
        }
        Ok "TopFailureReasons structure validated"
    }
}

if ($VerboseOutput) {
    Write-Host "Visible systems: $($j.VisibleSystems -join ', ')" -ForegroundColor DarkGray
    if ($j.PSObject.Properties.Name -contains 'BandsConsidered') {
        Write-Host "Bands considered: $($j.BandsConsidered -join ', ')" -ForegroundColor DarkGray
    }
}

Write-Host "All dashboard output validations passed." -ForegroundColor Cyan