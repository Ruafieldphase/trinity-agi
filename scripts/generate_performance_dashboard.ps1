# Performance Metrics Dashboard Generator
# Tracks execution time, success rate, and resource usage
#
# Parameters:
#   -Days: Number of days to analyze (default: 7)
#   -OpenDashboard: Open generated MD file in VS Code
#   -ExportJson: Export metrics as JSON
#   -ExportCsv: Export metrics as CSV with metadata headers
#   -WriteLatest: Update *_latest.* aliases for all outputs
#   -AllowEmpty: Generate report even when no test data exists
#   -ExcellentAt: Success rate threshold for Excellent band (default: 90%)
#   -GoodAt: Success rate threshold for Good band (default: 70%)
#   -TopHistory: Maximum test runs to include in history table
#   -TopAttentionCount: Number of systems to show in Top Attention list
#   -TopErrorReasons: Number of error reasons to display per system
#   -Profile: Load predefined filter/sort configuration (e.g., 'ops-daily', 'ops-focus')
#   -OnlyBands: Filter display to specific bands (Excellent, Good, Needs, NoData)
#   -AttentionRespectsBands: When set, Top Attention list respects OnlyBands filter
#   -IncludeSystems: Whitelist of system names to include (overrides profile)
#   -ExcludeSystems: Blacklist of system names to exclude (overrides profile)
#   -SortBy: Sort systems by 'effective', 'overall', or 'name'
#   -Order: Sort order 'asc' or 'desc'

param(
    [int]$Days = 7,
    [switch]$OpenDashboard,
    [switch]$ExportJson,
    [switch]$ExportCsv,
    [switch]$WriteLatest,
    [switch]$AllowEmpty,
    [ValidateRange(1, 100)][int]$ExcellentAt = 90,
    [ValidateRange(1, 100)][int]$GoodAt = 70,
    [ValidateRange(1, 100)][int]$TopHistory = 10,
    [ValidateRange(1, 50)][int]$TopAttentionCount = 3,
    [ValidateRange(1, 20)][int]$TopErrorReasons = 3,
    [string]$Profile = '',
    [ValidateSet('Excellent', 'Good', 'Needs', 'NoData', 'No Data')][string[]]$OnlyBands = @(),
    [switch]$AttentionRespectsBands,
    [string[]]$IncludeSystems = @(),
    [string[]]$ExcludeSystems = @(),
    [ValidateSet('effective', 'overall', 'name')][string]$SortBy = 'effective',
    [ValidateSet('asc', 'desc')][string]$Order = 'asc'
)

$ErrorActionPreference = "Continue"

# Helpers: band normalization and canonicalization
function Normalize-BandInput {
    param([Parameter(Mandatory=$true)][string]$Band)
    switch ($Band) {
        'NoData' { 'No Data'; break }
        'Needs'  { 'Needs Attention'; break }
        default  { $Band }
    }
}
function Get-CanonicalBandFromRates {
    param(
        [bool]$HasData,
        [double]$EffectiveRate,
        [int]$ExcellentAt,
        [int]$GoodAt
    )
    if ($HasData -and $EffectiveRate -ge $ExcellentAt) { return 'Excellent' }
    elseif ($HasData -and $EffectiveRate -ge $GoodAt) { return 'Good' }
    elseif ($HasData) { return 'Needs Attention' }
    else { return 'No Data' }
}

# Ensure UTF-8 console/output (PS 5.1 compatible)
try { chcp 65001 > $null 2> $null } catch {}
try {
    [Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false, $false)
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false, $false)
    $global:OutputEncoding = New-Object System.Text.UTF8Encoding($false, $false)
}
catch {}
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$outputDir = Join-Path (Split-Path -Parent $scriptDir) "outputs"

# Ensure output directory exists
if (-not (Test-Path $outputDir)) { New-Item -ItemType Directory -Path $outputDir -Force | Out-Null }

# Optional: load profile overrides
if (-not [string]::IsNullOrWhiteSpace($Profile)) {
    try {
        $root = Split-Path -Parent $scriptDir
        $candidatePaths = @(
            (Join-Path $root 'configs/perf_dashboard_profiles.local.json'),
            (Join-Path $root 'configs/perf_dashboard_profiles.json')
        )
        $profilePath = ($candidatePaths | Where-Object { Test-Path $_ } | Select-Object -First 1)
        if ($profilePath) {
            $profJson = Get-Content $profilePath -Raw | ConvertFrom-Json
            $prof = $null
            if ($profJson -and $profJson.profiles) { $prof = $profJson.profiles.($Profile) }
            if ($null -ne $prof) {
                if (-not $PSBoundParameters.ContainsKey('IncludeSystems') -and $prof.IncludeSystems) { $IncludeSystems = @($prof.IncludeSystems) }
                if (-not $PSBoundParameters.ContainsKey('ExcludeSystems') -and $prof.ExcludeSystems) { $ExcludeSystems = @($prof.ExcludeSystems) }
                if (-not $PSBoundParameters.ContainsKey('SortBy') -and $prof.SortBy) { $SortBy = [string]$prof.SortBy }
                if (-not $PSBoundParameters.ContainsKey('Order') -and $prof.Order) { $Order = [string]$prof.Order }
                if (-not $PSBoundParameters.ContainsKey('ExcellentAt') -and $prof.ExcellentAt) { $ExcellentAt = [int]$prof.ExcellentAt }
                if (-not $PSBoundParameters.ContainsKey('GoodAt') -and $prof.GoodAt) { $GoodAt = [int]$prof.GoodAt }
                if (-not $PSBoundParameters.ContainsKey('TopHistory') -and $prof.TopHistory) { $TopHistory = [int]$prof.TopHistory }
                if (-not $PSBoundParameters.ContainsKey('Days') -and $prof.Days) { $Days = [int]$prof.Days }
                if (-not $PSBoundParameters.ContainsKey('OnlyBands') -and $prof.OnlyBands) { $OnlyBands = @($prof.OnlyBands) }
                if (-not $PSBoundParameters.ContainsKey('AttentionRespectsBands') -and $prof.AttentionRespectsBands) { $AttentionRespectsBands = [bool]$prof.AttentionRespectsBands }
            }
            else {
                Write-Warning "Profile '$Profile' not found in $profilePath"
            }
        }
        else {
            Write-Warning "No profile config found. Checked: $($candidatePaths -join ', ')"
        }
    }
    catch {
        Write-Warning "Failed to load profile '$Profile': $($_.Exception.Message)"
    }
}

# Sanity-check thresholds: ensure GoodAt < ExcellentAt for meaningful bands
if ($GoodAt -ge $ExcellentAt) {
    Write-Warning "GoodAt ($GoodAt) should be less than ExcellentAt ($ExcellentAt). Adjusting GoodAt..."
    $GoodAt = [int]([Math]::Max(0, $ExcellentAt - 1))
}

Write-Host "`n" -NoNewline
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "`n  Performance Metrics Dashboard`n" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "`n"

# Collect E2E test results
Write-Host "Collecting performance data (last $Days days)..." -ForegroundColor Cyan

$cutoffDate = (Get-Date).AddDays(-$Days)
$testResults = Get-ChildItem -Path $outputDir -Filter "e2e_test_results_*.json" |
Where-Object { $_.LastWriteTime -ge $cutoffDate } |
Sort-Object LastWriteTime -Descending

Write-Host "  Found $($testResults.Count) test runs`n" -ForegroundColor Gray

if ($testResults.Count -eq 0) {
    Write-Host "No test data found in the last $Days days." -ForegroundColor Yellow
    if (-not $AllowEmpty) {
        Write-Host "Run: .\run_e2e_integration_test.ps1 to generate data`n" -ForegroundColor Gray
        exit 1
    }
}

# Parse results
$allResults = @()
foreach ($file in $testResults) {
    try {
        $data = Get-Content $file.FullName -Raw | ConvertFrom-Json
        $timestamp = $file.BaseName -replace 'e2e_test_results_', ''
        
        foreach ($result in $data) {
            $allResults += [PSCustomObject]@{
                Timestamp = $timestamp
                System    = $result.System
                Status    = $result.Status
                Error     = $result.Error
                File      = $file.Name
            }
        }
    }
    catch {
        Write-Warning "Failed to parse $($file.Name): $_"
    }
}

Write-Host "Analyzing metrics..." -ForegroundColor Cyan

# Calculate metrics per system
$systems = @()
if ($allResults -and $allResults.Count -gt 0) {
    $systems = $allResults | Select-Object -ExpandProperty System -Unique
}
$metrics = @{}

foreach ($system in $systems) {
    # Normalize statuses and sort by run timestamp (desc)
    $systemResults = $allResults | Where-Object { $_.System -eq $system } |
    ForEach-Object {
        $ts = $_.Timestamp
        $dt = $null
        try {
            $dt = [datetime]::ParseExact($ts, 'yyyy-MM-dd_HHmmss', $null)
        }
        catch {
            try { $dt = [datetime]$ts } catch { $dt = [datetime]::MinValue }
        }
        [PSCustomObject]@{
            Timestamp = $_.Timestamp
            System    = $_.System
            Status    = ("$($_.Status)".Trim().ToUpper())
            Error     = $_.Error
            RunAt     = $dt
        }
    } |
    Sort-Object -Property RunAt -Descending

    $totalRuns = @($systemResults).Count
    $passCount = @($systemResults | Where-Object { $_.Status -eq 'PASS' }).Count
    $failCount = @($systemResults | Where-Object { $_.Status -eq 'FAIL' }).Count
    $skipCount = @($systemResults | Where-Object { $_.Status -eq 'SKIP' }).Count

    $successRate = if ($totalRuns -gt 0) { ($passCount / $totalRuns) * 100 } else { 0 }
    $effectiveRuns = $passCount + $failCount
    $effectiveSuccessRate = if ($effectiveRuns -gt 0) { ($passCount / $effectiveRuns) * 100 } else { 0 }

    # Prefer last non-SKIP status for labeling; fallback to newest entry
    $latestNonSkip = $systemResults | Where-Object { $_.Status -ne 'SKIP' } | Select-Object -First 1
    $lastEntry = if ($latestNonSkip) { $latestNonSkip } else { $systemResults | Select-Object -First 1 }

    $metrics[$system] = @{
        TotalRuns            = $totalRuns
        Passed               = $passCount
        Failed               = $failCount
        Skipped              = $skipCount
        SuccessRate          = $successRate
        EffectiveRuns        = $effectiveRuns
        EffectiveSuccessRate = $effectiveSuccessRate
        LastStatus           = $lastEntry.Status
        LastError            = $lastEntry.Error
        Band                 = $null  # Will be set during band classification
    }
}

# Generate dashboard report
$dashboardPath = Join-Path $outputDir "performance_dashboard_$(Get-Date -Format 'yyyy-MM-dd').md"

# Build visible system set (include/exclude, case-insensitive)
$visibleKeys = @($metrics.Keys)
if ($IncludeSystems -and $IncludeSystems.Count -gt 0) {
    $inc = @{}
    foreach ($i in $IncludeSystems) { if ($i) { $inc[$i.ToLower()] = $true } }
    $visibleKeys = $visibleKeys | Where-Object { $inc.ContainsKey($_.ToLower()) }
}
if ($ExcludeSystems -and $ExcludeSystems.Count -gt 0) {
    $exc = @{}
    foreach ($e in $ExcludeSystems) { if ($e) { $exc[$e.ToLower()] = $true } }
    $visibleKeys = $visibleKeys | Where-Object { -not $exc.ContainsKey($_.ToLower()) }
}
$visibleSet = @{}
foreach ($k in $visibleKeys) { $visibleSet[$k.ToLower()] = $true }

$filteredMetrics = $metrics.GetEnumerator() | Where-Object { $visibleSet.ContainsKey($_.Key.ToLower()) }

# Overall success & flagged systems for digest (filtered)
$successRates = $filteredMetrics | ForEach-Object { [double]$_.Value.SuccessRate }
$overallSuccess = ($successRates | Measure-Object -Average).Average
if ($null -eq $overallSuccess) { $overallSuccess = 0 }

# Effective overall success (exclude SKIPs-only systems; filtered)
$effectiveRates = ($filteredMetrics |
    Where-Object { $_.Value.EffectiveRuns -gt 0 } |
    ForEach-Object { [double]$_.Value.EffectiveSuccessRate })
$overallEffectiveSuccess = ($effectiveRates | Measure-Object -Average).Average
if ($null -eq $overallEffectiveSuccess) { $overallEffectiveSuccess = 0 }

# Flag systems using effective success rate; ignore systems with no effective runs (all SKIP); filtered
$flaggedSystems = (
    $filteredMetrics |
    Where-Object { $_.Value.EffectiveRuns -gt 0 -and $_.Value.EffectiveSuccessRate -lt $ExcellentAt } |
    Select-Object -ExpandProperty Key
)
if ($null -eq $flaggedSystems) { $flaggedSystems = @() }

# Band counts for digest (exclude no-data; track NoData separately); filtered
$bandExcellent = ($filteredMetrics | Where-Object { $_.Value.EffectiveRuns -gt 0 -and $_.Value.EffectiveSuccessRate -ge $ExcellentAt }).Count
$bandGood = ($filteredMetrics | Where-Object { $_.Value.EffectiveRuns -gt 0 -and $_.Value.EffectiveSuccessRate -ge $GoodAt -and $_.Value.EffectiveSuccessRate -lt $ExcellentAt }).Count
$bandNeeds = ($filteredMetrics | Where-Object { $_.Value.EffectiveRuns -gt 0 -and $_.Value.EffectiveSuccessRate -lt $GoodAt }).Count
$bandNoData = ($filteredMetrics | Where-Object { $_.Value.EffectiveRuns -le 0 }).Count

# Assign Band to all metrics for export
foreach ($sys in $metrics.Keys) {
    $mv = $metrics[$sys]
    $hasData = ($mv.EffectiveRuns -gt 0)
    $band = Get-CanonicalBandFromRates -HasData:$hasData -EffectiveRate:([double]$mv.EffectiveSuccessRate) -ExcellentAt:$ExcellentAt -GoodAt:$GoodAt
    $metrics[$sys].Band = $band
}

# Top attention systems (lowest effective success under Excellent; exclude no-data); filtered
$topAttention = ($filteredMetrics |
    Where-Object { $_.Value.EffectiveRuns -gt 0 -and $_.Value.EffectiveSuccessRate -lt $ExcellentAt } |
    Sort-Object { $_.Value.EffectiveSuccessRate } |
    Select-Object -First $TopAttentionCount)

# If OnlyBands is specified, restrict Top Attention list to those bands
if ($AttentionRespectsBands -and $OnlyBands -and $OnlyBands.Count -gt 0 -and $topAttention) {
    $allowed = @{}
    foreach ($b in $OnlyBands) {
        if ($b) {
            $bb = Normalize-BandInput -Band $b
            $allowed[$bb] = $true
        }
    }
    $topAttention = ($topAttention | Where-Object {
            $er = [double]$_.Value.EffectiveSuccessRate
            $hasData = ([int]$_.Value.EffectiveRuns -gt 0)
            $band = Get-CanonicalBandFromRates -HasData:$hasData -EffectiveRate:$er -ExcellentAt:$ExcellentAt -GoodAt:$GoodAt
            $allowed.ContainsKey($band)
        })
}

# Compute how many systems will be displayed in the overview section (respects -OnlyBands)
$displayedCount = $visibleKeys.Count
if ($OnlyBands -and $OnlyBands.Count -gt 0) {
    $displayedCount = 0
    foreach ($sys in $visibleKeys) {
        if (-not $metrics.ContainsKey($sys)) { continue }
        $mv = $metrics[$sys]
        $hasData = ($mv.EffectiveRuns -gt 0)
        $band = Get-CanonicalBandFromRates -HasData:$hasData -EffectiveRate:([double]$mv.EffectiveSuccessRate) -ExcellentAt:$ExcellentAt -GoodAt:$GoodAt
        # Store band in metrics for export
        $metrics[$sys].Band = $band
        $allowed = $false
        foreach ($b in $OnlyBands) {
            $bb = Normalize-BandInput -Band $b
            if ($bb -eq $band) { $allowed = $true; break }
        }
        if ($allowed) { $displayedCount++ }
    }
}

$report = @"
[PERFORMANCE DIGEST - ASCII SAFE]

- Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
- Period: Last $Days days
 - Total test runs: $($testResults.Count)
 - Systems considered: $($visibleKeys.Count)
- Overall success: $($overallSuccess.ToString('F1'))%
- Effective overall success: $($overallEffectiveSuccess.ToString('F1'))%
- Thresholds: ExcellentAt=$ExcellentAt%  GoodAt=$GoodAt%
- Systems flagged (<$ExcellentAt%): $(if ($flaggedSystems.Count -gt 0) { ($flaggedSystems -join ', ') } else { 'None' })
 - Flagged count: $($flaggedSystems.Count)
  - Band counts: Excellent=$bandExcellent, Good=$bandGood, Needs=$bandNeeds, NoData=$bandNoData
$( if ($OnlyBands -and $OnlyBands.Count -gt 0) {
    $bandsDisplay = ($OnlyBands | ForEach-Object { Normalize-BandInput -Band $_ }) -join ', '
    "- Bands considered: $bandsDisplay`n- Systems displayed: $displayedCount"
} else { '' } )
   - Top attention$(if ($AttentionRespectsBands -and $OnlyBands -and $OnlyBands.Count -gt 0) { ' (respecting bands)' } else { '' }): $(if ($topAttention.Count -gt 0) { ($topAttention | ForEach-Object { "{0} ({1}%)" -f $_.Key, ([double]$_.Value.EffectiveSuccessRate).ToString('F1') }) -join ', ' } else { 'None' })

---

# Performance Metrics Dashboard

**Generated**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")  
**Period**: Last $Days days  
**Total Test Runs**: $($testResults.Count)  
**Systems Considered**: $($visibleKeys.Count)
$( if ($OnlyBands -and $OnlyBands.Count -gt 0) { "**Systems Displayed**: $displayedCount" } else { '' } )

---

## System Performance Overview

"@

$orderingBase = ($metrics.GetEnumerator() | Where-Object { $visibleSet.ContainsKey($_.Key.ToLower()) })
if ($OnlyBands -and $OnlyBands.Count -gt 0 -and $displayedCount -eq 0) {
    $report += "_No systems match selected bands._`n`n"
}
switch ($SortBy) {
    'effective' {
        $withData = ($orderingBase | Where-Object { $_.Value.EffectiveRuns -gt 0 })
        $noData = ($orderingBase | Where-Object { $_.Value.EffectiveRuns -le 0 })
        $withData = if ($Order -eq 'desc') { $withData | Sort-Object { $_.Value.EffectiveSuccessRate } -Descending } else { $withData | Sort-Object { $_.Value.EffectiveSuccessRate } }
        $noData = $noData | Sort-Object Key
        $orderedWithData = ($withData | Select-Object -ExpandProperty Key)
        $orderedNoData = ($noData   | Select-Object -ExpandProperty Key)
    }
    'overall' {
        $withData = ($orderingBase | Where-Object { $_.Value.TotalRuns -gt 0 })
        $noData = ($orderingBase | Where-Object { $_.Value.TotalRuns -le 0 })
        $withData = if ($Order -eq 'desc') { $withData | Sort-Object { $_.Value.SuccessRate } -Descending } else { $withData | Sort-Object { $_.Value.SuccessRate } }
        $noData = $noData | Sort-Object Key
        $orderedWithData = ($withData | Select-Object -ExpandProperty Key)
        $orderedNoData = ($noData   | Select-Object -ExpandProperty Key)
    }
    'name' {
        $orderedWithData = ($orderingBase | Where-Object { $_.Value.EffectiveRuns -gt 0 } | Sort-Object Key -Descending:($Order -eq 'desc') | Select-Object -ExpandProperty Key)
        $orderedNoData = ($orderingBase | Where-Object { $_.Value.EffectiveRuns -le 0 } | Sort-Object Key -Descending:($Order -eq 'desc') | Select-Object -ExpandProperty Key)
    }
}
$orderedSystems = @($orderedWithData + $orderedNoData)
if ($orderedSystems.Count -eq 0) {
    $report += "_No systems in selected period._`n"
}
if (-not ($OnlyBands -and $OnlyBands.Count -gt 0 -and $displayedCount -eq 0)) {
    foreach ($system in $orderedSystems) {
        $m = $metrics[$system]
        $statusEmoji = switch ($m.LastStatus) {
            "PASS" { "[PASS]" }
            "FAIL" { "[FAIL]" }
            "SKIP" { "[SKIP]" }
            default { "[UNKNOWN]" }
        }
    
        $hasData = ($m.EffectiveRuns -gt 0)
        $healthColor = if ($hasData -and $m.EffectiveSuccessRate -ge $ExcellentAt) { "GREEN" } 
        elseif ($hasData -and $m.EffectiveSuccessRate -ge $GoodAt) { "YELLOW" } 
        elseif ($hasData) { "RED" } else { "GRAY" }
        $healthBand = if ($hasData -and $m.EffectiveSuccessRate -ge $ExcellentAt) { "Excellent" } 
        elseif ($hasData -and $m.EffectiveSuccessRate -ge $GoodAt) { "Good" } 
        elseif ($hasData) { "Needs Attention" } else { "No Data" }

        # Optional band filter for overview rendering
        if ($OnlyBands -and $OnlyBands.Count -gt 0) {
            $canonical = $healthBand
            $match = $false
            foreach ($b in $OnlyBands) {
                $bb = Normalize-BandInput -Band $b
                if ($bb -eq $canonical) { $match = $true; break }
            }
            if (-not $match) { continue }
        }
    
        $report += @"

### $statusEmoji $system

$healthColor **Health Score**: $(if ($hasData) { $m.EffectiveSuccessRate.ToString('F1') + '%' } else { 'N/A' })
Band: $healthBand

| Metric | Value |
|--------|-------|
| Total Runs | $($m.TotalRuns) |
| Passed | $($m.Passed) |
| Failed | $($m.Failed) |
| Skipped | $($m.Skipped) |
| Success Rate | $(if ($hasData) { $m.SuccessRate.ToString('F1') + '%' } else { 'N/A' }) |
| Effective Success Rate | $(if ($hasData) { $m.EffectiveSuccessRate.ToString('F1') + '%' } else { 'N/A' }) |

"@

        if ($m.LastStatus -eq "FAIL" -and $m.LastError) {
            $report += "**Last Error**: ``$($m.LastError)```n`n"
        }
    }
}

# Overall system health (based on effective overall success)
$healthStatus = if ($overallEffectiveSuccess -ge $ExcellentAt) { "Excellent" } 
elseif ($overallEffectiveSuccess -ge $GoodAt) { "Good" } 
else { "Needs Attention" }

$report += @"

---

## Overall System Health

**Status**: $healthStatus  
**Average Success Rate**: $($overallSuccess.ToString('F1'))%  
**Effective Average Success** (excluding SKIPs): $($overallEffectiveSuccess.ToString('F1'))%

### Recommendations

"@

foreach ($system in $systems) {
    $m = $metrics[$system]
    if ($m.EffectiveRuns -le 0) { continue }
    if ($m.EffectiveSuccessRate -lt $GoodAt) {
        $report += "- [Must fix] **$system**: $($m.EffectiveSuccessRate.ToString('F1'))% - stabilize failing paths.`n"
    }
    elseif ($m.EffectiveSuccessRate -lt $ExcellentAt) {
        $report += "- [Improve] **$system**: $($m.EffectiveSuccessRate.ToString('F1'))% - optimize to reach $ExcellentAt%.`n"
    }
}

if ($overallSuccess -ge $ExcellentAt) {
    $report += "- All systems performing well! No action required.`n"
}

$report += @"

---

## Failure Reasons (Top $TopErrorReasons)

"@

# Build top failure reasons for filtered systems (respect OnlyBands if provided)
$errorBySystem = @{}
if ($allResults -and $allResults.Count -gt 0) {
    foreach ($sys in $visibleKeys) {
        if ($OnlyBands -and $OnlyBands.Count -gt 0 -and $metrics.ContainsKey($sys)) {
            $mv = $metrics[$sys]
            $hasData = ($mv.EffectiveRuns -gt 0)
            $band = Get-CanonicalBandFromRates -HasData:$hasData -EffectiveRate:([double]$mv.EffectiveSuccessRate) -ExcellentAt:$ExcellentAt -GoodAt:$GoodAt
            $allowed = $false
            foreach ($b in $OnlyBands) {
                $bb = Normalize-BandInput -Band $b
                if ($bb -eq $band) { $allowed = $true; break }
            }
            if (-not $allowed) { continue }
        }
        $fails = $allResults | Where-Object { $_.System -eq $sys -and ("$($_.Status)".Trim().ToUpper()) -eq 'FAIL' -and ($_.Error -ne $null) -and ("$($_.Error)".Trim().Length -gt 0) }
        if ($fails -and $fails.Count -gt 0) {
            $groups = $fails | ForEach-Object {
                $msg = ("$($_.Error)".Trim())
                if ($msg.Length -gt 140) { $msg = $msg.Substring(0, 140) + '…' }
                $msg
            } | Group-Object | Sort-Object Count -Descending
            $top = $groups | Select-Object -First $TopErrorReasons
            $errorBySystem[$sys] = $top
        }
    }
}

if ($errorBySystem.Keys.Count -gt 0) {
    foreach ($kv in $errorBySystem.GetEnumerator() | Sort-Object Key) {
        $report += "### $($kv.Key)`n`n"
        foreach ($g in $kv.Value) {
            $report += ("- ($($g.Count)x) $($g.Name)`n")
        }
        $report += "`n"
    }
}
else {
    $report += "_No failures with error messages in selected period/scope._`n`n"
}

$report += @"

---

## Test Run History

| Timestamp | Total | Passed | Failed | Skipped |
|-----------|-------|--------|--------|---------|
"@

# Ensure a newline before first data row to avoid header/data sticking
$report += "`n"

if ($testResults.Count -gt 0) {
    foreach ($file in ($testResults | Select-Object -First $TopHistory)) {
        $timestamp = $file.BaseName -replace 'e2e_test_results_', ''
        $dataRaw = Get-Content $file.FullName -Raw
        try { $data = $dataRaw | ConvertFrom-Json } catch { $data = @() }
        if ($null -eq $data) { $data = @() }
        $total = @($data).Count
        $passed = @($data | Where-Object { ("" + $_.Status).Trim() -ieq "PASS" }).Count
        $failed = @($data | Where-Object { ("" + $_.Status).Trim() -ieq "FAIL" }).Count
        $skipped = @($data | Where-Object { ("" + $_.Status).Trim() -ieq "SKIP" }).Count

        $report += "| $timestamp | $total | $passed | $failed | $skipped |`n"
    }
}
else {
    $report += "| (no data) | 0 | 0 | 0 | 0 |`n"
}

$report += @"

---

## Usage

- **Run E2E Test**: ``.\run_e2e_integration_test.ps1``
- **Auto Recovery**: ``.\start_auto_recovery.ps1``
- **Daily Briefing**: ``.\generate_daily_briefing.ps1 -OpenReport``

---

*Generated by Performance Metrics Dashboard*
"@

# Save report (UTF-8 without BOM)
$utf8NoBom = New-Object System.Text.UTF8Encoding($false, $false)
[System.IO.File]::WriteAllText($dashboardPath, [string]$report, $utf8NoBom)
Write-Host "  Dashboard saved: $dashboardPath" -ForegroundColor Green

# Export JSON
if ($ExportJson) {
    $jsonPath = Join-Path $outputDir "performance_metrics_$(Get-Date -Format 'yyyy-MM-dd').json"

    # Build filtered systems map for JSON (respect visible set)
    $systemsFiltered = @{}
    foreach ($kv in $filteredMetrics) { $systemsFiltered[$kv.Key] = $kv.Value }

    # Optional bands considered text
    $bandsConsidered = @()
    if ($OnlyBands -and $OnlyBands.Count -gt 0) {
        $bandsConsidered = @($OnlyBands | ForEach-Object { Normalize-BandInput -Band $_ })
    }

    $metricsExport = @{
        Generated                   = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Period                      = $Days
        OverallSuccessRate          = $overallSuccess
        OverallEffectiveSuccessRate = $overallEffectiveSuccess
        Systems                     = $metrics
        SystemsFiltered             = $systemsFiltered
        TestRuns                    = $testResults.Count
        Thresholds                  = @{ ExcellentAt = $ExcellentAt; GoodAt = $GoodAt }
        BandCounts                  = @{ Excellent = $bandExcellent; Good = $bandGood; Needs = $bandNeeds; NoData = $bandNoData }
        SystemsConsidered           = $visibleKeys.Count
        VisibleSystems              = $visibleKeys
        Filters                     = @{ IncludeSystems = $IncludeSystems; ExcludeSystems = $ExcludeSystems; Bands = $OnlyBands }
        SystemsDisplayed            = $displayedCount
        Sort                        = @{ SortBy = $SortBy; Order = $Order }
        TopAttentionCount           = $TopAttentionCount
    }
    if ($bandsConsidered -and $bandsConsidered.Count -gt 0) { $metricsExport.BandsConsidered = $bandsConsidered }
    $metricsExport.FlaggedSystems = $flaggedSystems
    $topAttentionExport = @()
    foreach ($item in $topAttention) {
        $topAttentionExport += [PSCustomObject]@{
            System               = $item.Key
            EffectiveSuccessRate = [double]$item.Value.EffectiveSuccessRate
        }
    }
    $metricsExport.TopAttention = $topAttentionExport
    $metricsExport.TopAttentionRespectsBands = [bool]$AttentionRespectsBands
    # Export top failure reasons (filtered, respects OnlyBands)
    $topFailureReasonsExport = @()
    if ($errorBySystem -and $errorBySystem.Keys.Count -gt 0) {
        foreach ($kv in $errorBySystem.GetEnumerator()) {
            $reasons = @()
            foreach ($g in $kv.Value) {
                $reasons += [PSCustomObject]@{ Error = "$($g.Name)"; Count = [int]$g.Count }
            }
            $topFailureReasonsExport += [PSCustomObject]@{ System = $kv.Key; Reasons = $reasons }
        }
    }
    if ($topFailureReasonsExport.Count -gt 0) { $metricsExport.TopFailureReasons = $topFailureReasonsExport }
    $jsonBody = ($metricsExport | ConvertTo-Json -Depth 10)
    [System.IO.File]::WriteAllText($jsonPath, $jsonBody, $utf8NoBom)
    Write-Host "  JSON exported: $jsonPath" -ForegroundColor Green
}

# Export CSV for filtered systems
if ($ExportCsv) {
    try {
        $csvPath = Join-Path $outputDir "performance_metrics_$(Get-Date -Format 'yyyy-MM-dd').csv"
        # Build metadata comments
        $metaLines = @()
        $metaLines += "# Performance Metrics CSV - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        $metaLines += "# Period: Last $Days days"
        $metaLines += "# Systems Considered: $($visibleKeys.Count)"
        if ($OnlyBands -and $OnlyBands.Count -gt 0) {
            $bandsDisplay = ($OnlyBands | ForEach-Object { Normalize-BandInput -Band $_ }) -join ', '
            $metaLines += "# Bands Considered: $bandsDisplay"
            $metaLines += "# Systems Displayed: $displayedCount"
        }
        if ($AttentionRespectsBands) {
            $metaLines += "# Top Attention Respects Bands: Yes"
        }
        $metaLines += ""
        $rows = @()
        foreach ($kv in $filteredMetrics) {
            $name = $kv.Key
            $val = $kv.Value
            $hasData = ([int]$val.EffectiveRuns -gt 0)
            $band = Get-CanonicalBandFromRates -HasData:$hasData -EffectiveRate:([double]$val.EffectiveSuccessRate) -ExcellentAt:$ExcellentAt -GoodAt:$GoodAt
            $rows += [PSCustomObject]@{
                System               = $name
                Band                 = $band
                TotalRuns            = [int]$val.TotalRuns
                Passed               = [int]$val.Passed
                Failed               = [int]$val.Failed
                Skipped              = [int]$val.Skipped
                SuccessRate          = [double]$val.SuccessRate
                EffectiveRuns        = [int]$val.EffectiveRuns
                EffectiveSuccessRate = [double]$val.EffectiveSuccessRate
                LastStatus           = "$($val.LastStatus)"
            }
        }
        # Write metadata as comments then CSV
        $csvContent = ($metaLines -join "`n") + "`n"
        $csvContent += ($rows | ConvertTo-Csv -NoTypeInformation | Out-String)
        [System.IO.File]::WriteAllText($csvPath, $csvContent, $utf8NoBom)
        Write-Host "  CSV exported: $csvPath" -ForegroundColor Green

        if ($WriteLatest) {
            try {
                $latestCsv = Join-Path $outputDir 'performance_metrics_latest.csv'
                if (Test-Path $csvPath) { Copy-Item -Force -Path $csvPath -Destination $latestCsv }
                Write-Host "  Latest CSV updated: $latestCsv" -ForegroundColor DarkCyan
            }
            catch {
                Write-Warning "Could not update latest CSV alias: $($_.Exception.Message)"
            }
        }
    }
    catch {
        Write-Warning "Failed to export CSV: $($_.Exception.Message)"
    }
}

# Optionally update latest aliases
if ($WriteLatest) {
    try {
        $latestMd = Join-Path $outputDir 'performance_dashboard_latest.md'
        Copy-Item -Force -Path $dashboardPath -Destination $latestMd
        Write-Host "  Latest MD updated: $latestMd" -ForegroundColor DarkCyan
    }
    catch {
        Write-Warning "Could not update latest MD alias: $($_.Exception.Message)"
    }
    if ($ExportJson) {
        try {
            $jsonPath = Join-Path $outputDir "performance_metrics_$(Get-Date -Format 'yyyy-MM-dd').json"
            $latestJson = Join-Path $outputDir 'performance_metrics_latest.json'
            if (Test-Path $jsonPath) {
                Copy-Item -Force -Path $jsonPath -Destination $latestJson
                Write-Host "  Latest JSON updated: $latestJson" -ForegroundColor DarkCyan
            }
        }
        catch {
            Write-Warning "Could not update latest JSON alias: $($_.Exception.Message)"
        }
    }
}

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "`n  Performance Dashboard Generated!`n" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "`n"

Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Test Runs: $($testResults.Count)" -ForegroundColor White
Write-Host "  Systems Considered: $($visibleKeys.Count)" -ForegroundColor White
if ($OnlyBands -and $OnlyBands.Count -gt 0) {
    Write-Host "  Systems Displayed: $displayedCount" -ForegroundColor White
}
Write-Host "  Overall Success: $($overallSuccess.ToString('F1'))%" -ForegroundColor $(if ($overallSuccess -ge $ExcellentAt) { "Green" } elseif ($overallSuccess -ge $GoodAt) { "Yellow" } else { "Red" })
Write-Host "  Effective Overall Success: $($overallEffectiveSuccess.ToString('F1'))%" -ForegroundColor $(if ($overallEffectiveSuccess -ge $ExcellentAt) { "Green" } elseif ($overallEffectiveSuccess -ge $GoodAt) { "Yellow" } else { "Red" })
Write-Host "  Status: $healthStatus" -ForegroundColor White
if ($bandExcellent -or $bandGood -or $bandNeeds -or $bandNoData) {
    Write-Host ("  Bands: Excellent={0}  Good={1}  Needs={2}  NoData={3}" -f $bandExcellent, $bandGood, $bandNeeds, $bandNoData) -ForegroundColor Gray
}
try {
    if ($topAttention -and $topAttention.Count -gt 0) {
        $ta = ($topAttention | ForEach-Object { "{0} ({1}%)" -f $_.Key, ([double]$_.Value.EffectiveSuccessRate).ToString('F1') }) -join ', '
        Write-Host "  Top attention: $ta" -ForegroundColor Yellow
    }
}
catch {}
Write-Host ""

Write-Host "Files:" -ForegroundColor Cyan
Write-Host "  - Dashboard: $dashboardPath" -ForegroundColor Gray
if ($ExportJson) {
    $jsonPath = Join-Path $outputDir "performance_metrics_$(Get-Date -Format 'yyyy-MM-dd').json"
    Write-Host "  - JSON: $jsonPath" -ForegroundColor Gray
}
Write-Host ""

if ($OpenDashboard) {
    Write-Host "Opening dashboard..." -ForegroundColor Cyan
    code $dashboardPath
}

Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "`nUsage:" -ForegroundColor Yellow
Write-Host "  Basic:        .\generate_performance_dashboard.ps1" -ForegroundColor Gray
Write-Host "  Open report:  .\generate_performance_dashboard.ps1 -OpenDashboard" -ForegroundColor Gray
Write-Host "  Export JSON:  .\generate_performance_dashboard.ps1 -ExportJson" -ForegroundColor Gray
Write-Host "  Export CSV:   .\\generate_performance_dashboard.ps1 -ExportCsv" -ForegroundColor Gray
Write-Host "  Write latest: .\generate_performance_dashboard.ps1 -WriteLatest" -ForegroundColor Gray
Write-Host "  Custom days:  .\generate_performance_dashboard.ps1 -Days 30" -ForegroundColor Gray
Write-Host "  Thresholds:   .\\generate_performance_dashboard.ps1 -ExcellentAt 92 -GoodAt 75" -ForegroundColor Gray
Write-Host "  Top history:  .\\generate_performance_dashboard.ps1 -TopHistory 20" -ForegroundColor Gray
Write-Host "  Allow empty:  .\\generate_performance_dashboard.ps1 -AllowEmpty" -ForegroundColor Gray
Write-Host "  Include:      .\\generate_performance_dashboard.ps1 -IncludeSystems 'Orchestration','Daily Briefing'" -ForegroundColor Gray
Write-Host "  Exclude:      .\\generate_performance_dashboard.ps1 -ExcludeSystems 'YouTube Learning'" -ForegroundColor Gray
Write-Host "  Sort:         .\\generate_performance_dashboard.ps1 -SortBy effective -Order desc" -ForegroundColor Gray
Write-Host "  Profile:      .\\generate_performance_dashboard.ps1 -Profile ops-daily" -ForegroundColor Gray
Write-Host "  Only bands:   .\\generate_performance_dashboard.ps1 -OnlyBands 'Needs','Good'" -ForegroundColor Gray
Write-Host "  Attention(bands): .\\generate_performance_dashboard.ps1 -AttentionRespectsBands" -ForegroundColor Gray
Write-Host "  Top errors:   .\\generate_performance_dashboard.ps1 -TopErrorReasons 5" -ForegroundColor Gray
Write-Host "  Profiles (EZ): .\\scripts\\dashboard_ops_daily.ps1 -Open" -ForegroundColor DarkGray
Write-Host "                  .\\scripts\\dashboard_ops_focus.ps1 -Open" -ForegroundColor DarkGray
Write-Host "                  .\\scripts\\dashboard_ops_attention.ps1 -Open" -ForegroundColor DarkGray
Write-Host "                  .\\scripts\\dashboard_ops_excellent.ps1 -Open" -ForegroundColor DarkGray
Write-Host "  Quick access:  .\\scripts\\dashboard_quick_needs.ps1 -Open" -ForegroundColor DarkGray
Write-Host "                  .\\scripts\\dashboard_quick_full.ps1 -Open" -ForegroundColor DarkGray
Write-Host "  Test suite:   .\\scripts\\test_performance_dashboard_integration.ps1" -ForegroundColor DarkGray
Write-Host "  Validate:     .\\scripts\\validate_performance_dashboard.ps1 -VerboseOutput" -ForegroundColor DarkGray
Write-Host "`n"

