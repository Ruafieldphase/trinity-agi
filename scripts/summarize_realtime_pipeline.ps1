param(
    [string]$StatusJson = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\realtime_pipeline_status.json",
    [string]$OutMd = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\realtime_pipeline_summary_latest.md",
    [string]$OutJson = "",
    [switch]$Open,
    [int]$Lookback = 12,
    [int]$SparkLen = 40,
    [ValidateSet("delta", "ma-slope", "reg-slope")]
    [string]$TrendMode = "delta",
    [int]$SmoothWindow = 3,
    [ValidateSet("basic", "dense")]
    [string]$AsciiSet = "basic",
    [switch]$AutoScale
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

function Find-LastGoodJson {
    param([string]$Dir)
    if (-not (Test-Path -LiteralPath $Dir)) { return $null }
    $candidates = Get-ChildItem -LiteralPath $Dir -Filter "realtime_pipeline_status_*.json" -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^\d{8}_\d{6}\.json$' } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
    if ($candidates) { return $candidates.FullName }
    return $null
}

if (-not (Test-Path -LiteralPath $StatusJson)) {
    $fallback = Find-LastGoodJson -Dir (Split-Path -Parent $StatusJson)
    if ($fallback) {
        Write-Host "Primary JSON not found. Using fallback: $fallback" -ForegroundColor Yellow
        $StatusJson = $fallback
    }
    else {
        Write-Host "Status JSON not found and no fallback available: $StatusJson" -ForegroundColor Yellow
        exit 0
    }
}

try {
    $raw = Get-Content -LiteralPath $StatusJson -Raw -Encoding UTF8
    $data = $raw | ConvertFrom-Json -ErrorAction Stop
}
catch {
    Write-Host "Failed to parse JSON: $($PSItem.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Basic fields
$genAt = $data.generated_at
$windowHours = $data.window_hours
$metricsPath = $data.metrics_path
$seeds = $data.seeds
$sim = $data.simulation
$next = $data.next_runs

# Helpers
function Get-Stat {
    param([double[]]$arr)
    if (-not $arr -or $arr.Count -eq 0) { return @{ min = $null; max = $null; avg = $null; last = $null } }
    $min = ($arr | Measure-Object -Minimum).Minimum
    $max = ($arr | Measure-Object -Maximum).Maximum
    $avg = [Math]::Round((($arr | Measure-Object -Average).Average), 4)
    $last = $arr[-1]
    return @{ min = $min; max = $max; avg = $avg; last = $last }
}

$resSeries = @()
if ($sim -and $sim.resonance_series) { $resSeries = [double[]]$sim.resonance_series }
$stats = Get-Stat -arr $resSeries

# Trend helpers (ASCII/Unicode sparkline and direction)
function New-Sparkline {
    param(
        [double[]]$arr,
        [int]$maxLen = 32,
        [string]$Set = "basic",
        [bool]$Scale = $false
    )
    if (-not $arr -or $arr.Count -eq 0) { return "" }
    
    # ASCII-safe levels
    $blocks = if ($Set -eq "dense") {
        @('_', '.', ',', '-', ':', '=', '+', '*', '#', '@')
    }
    else {
        @('.', ',', '-', ':', '=', '+', '*', '#')
    }
    
    # Downsample if too long
    $series = @()
    $step = [Math]::Ceiling($arr.Count / [double]$maxLen)
    if ($step -le 1) {
        $series = $arr
    }
    else {
        for ($i = 0; $i -lt $arr.Count; $i += $step) {
            $end = [Math]::Min($i + $step, $arr.Count)
            $slice = $arr[$i..($end - 1)]
            $avg = ($slice | Measure-Object -Average).Average
            $series += [double]$avg
        }
    }
    
    $min = ($series | Measure-Object -Minimum).Minimum
    $max = ($series | Measure-Object -Maximum).Maximum
    if ($null -eq $min -or $null -eq $max) { return "" }
    
    # Auto-scale: use percentile-based clipping to avoid outlier skew
    if ($Scale) {
        $sorted = $series | Sort-Object
        $p5 = $sorted[[Math]::Floor($sorted.Count * 0.05)]
        $p95 = $sorted[[Math]::Floor($sorted.Count * 0.95)]
        if ($p95 -gt $p5) {
            $min = $p5
            $max = $p95
        }
    }
    
    if ([Math]::Abs($max - $min) -lt 1e-9) { return ("=" * $series.Count) }
    
    $sb = New-Object System.Text.StringBuilder
    foreach ($v in $series) {
        $clamped = [Math]::Max($min, [Math]::Min($max, $v))
        $norm = ($clamped - $min) / ($max - $min)
        $idx = [int][Math]::Round($norm * ($blocks.Count - 1))
        if ($idx -lt 0) { $idx = 0 }
        if ($idx -ge $blocks.Count) { $idx = $blocks.Count - 1 }
        [void]$sb.Append($blocks[$idx])
    }
    return $sb.ToString()
}

function Get-ResonanceTrend {
    param(
        [double[]]$arr,
        [int]$Lookback = 12,
        [double]$Epsilon = 0.005,
        [string]$Mode = "delta",
        [int]$SmoothWindow = 3
    )
    if (-not $arr -or $arr.Count -lt 2) { 
        return @{ direction = 'N/A'; delta = $null; lookback = 0; mode = $Mode } 
    }
    
    $k = [Math]::Min($Lookback, $arr.Count)
    $window = $arr[($arr.Count - $k)..($arr.Count - 1)]
    
    # Apply moving average smoothing if requested
    if ($SmoothWindow -gt 1 -and $window.Count -ge $SmoothWindow) {
        $smoothed = @()
        for ($i = 0; $i -le $window.Count - $SmoothWindow; $i++) {
            $slice = $window[$i..($i + $SmoothWindow - 1)]
            $avg = ($slice | Measure-Object -Average).Average
            $smoothed += $avg
        }
        if ($smoothed.Count -ge 2) { $window = $smoothed }
    }
    
    $first = $window[0]
    $last = $window[-1]
    $delta = 0.0
    
    switch ($Mode) {
        "delta" {
            $delta = [Math]::Round(($last - $first), 6)
        }
        "ma-slope" {
            # Simple moving average slope: (sum of differences) / count
            $diffs = @()
            for ($i = 1; $i -lt $window.Count; $i++) {
                $diffs += ($window[$i] - $window[$i - 1])
            }
            if ($diffs.Count -gt 0) {
                $delta = [Math]::Round((($diffs | Measure-Object -Average).Average), 6)
            }
        }
        "reg-slope" {
            # Linear regression slope (least squares)
            $n = $window.Count
            $sumX = 0; $sumY = 0; $sumXY = 0; $sumX2 = 0
            for ($i = 0; $i -lt $n; $i++) {
                $x = $i
                $y = $window[$i]
                $sumX += $x
                $sumY += $y
                $sumXY += ($x * $y)
                $sumX2 += ($x * $x)
            }
            $denom = ($n * $sumX2 - $sumX * $sumX)
            if ([Math]::Abs($denom) -gt 1e-9) {
                $slope = ($n * $sumXY - $sumX * $sumY) / $denom
                $delta = [Math]::Round($slope, 6)
            }
        }
    }
    
    $dir = if ([Math]::Abs($delta) -lt $Epsilon) { 'flat' } elseif ($delta -gt 0) { 'up' } else { 'down' }
    return @{ direction = $dir; delta = $delta; lookback = $k; mode = $Mode }
}

# Safe string formatter
function SafeVal { param([object]$v) if ($null -eq $v -or ("$v" -eq "")) { return 'N/A' } else { return $v } }

# Build Markdown
$lines = @()
$lines += "# Realtime Pipeline Summary"
$lines += "Generated at: $genAt  "
$lines += "Window: last ${windowHours}h  "
$statusFlag = if ($metricsPath -and (Test-Path -LiteralPath $metricsPath)) { 'OK' } else { 'MISSING' }
$lines += "Metrics JSON: $metricsPath ($statusFlag)\n"

$lines += "## Seeds"
$lines += "- info_density: $(SafeVal $seeds.info_density)"
$lines += "- coherence: $(SafeVal $seeds.coherence)"
$lines += "- ethics: $(SafeVal $seeds.ethics)\n"

$final = $null; if ($sim) { $final = $sim.final_state }
$lines += "## Simulation Final State"
$lines += "- resonance: $(SafeVal $($final.resonance))"
$lines += "- entropy: $(SafeVal $($final.entropy))"
$lines += "- info_density: $(SafeVal $($final.info_density))"
$lines += "- coherence: $(SafeVal $($final.coherence))"
$lines += "- ethics: $(SafeVal $($final.ethics))"
$lines += "- phase: $(SafeVal $($final.phase))"
$lines += "- horizon_crossings: $(SafeVal $($final.horizon_crossings))\n"

$lines += "## Resonance Series"
$lines += "- count: $($resSeries.Count)"
$lines += "- min/max/avg/last: $($stats.min) / $($stats.max) / $($stats.avg) / $($stats.last)\n"

if ($resSeries.Count -ge 2) {
    $trend = Get-ResonanceTrend -arr $resSeries -Lookback $Lookback -Mode $TrendMode -SmoothWindow $SmoothWindow
    $spark = New-Sparkline -arr $resSeries -maxLen $SparkLen -Set $AsciiSet -Scale $AutoScale
    $lines += "## Resonance Trend"
    $lines += "- direction: $($trend.direction)"
    $lines += "- delta (last $($trend.lookback), mode=$($trend.mode)): $($trend.delta)"
    $lines += "- sparkline: $spark\n"
}

# Additional series if available (entropy, info_density)
$entropySeries = @()
if ($sim -and $sim.entropy_series) { $entropySeries = [double[]]$sim.entropy_series }
if ($entropySeries.Count -ge 2) {
    $entropyStats = Get-Stat -arr $entropySeries
    $entropySpark = New-Sparkline -arr $entropySeries -maxLen $SparkLen -Set $AsciiSet -Scale $AutoScale
    $lines += "## Entropy Series"
    $lines += "- count: $($entropySeries.Count)"
    $lines += "- min/max/avg/last: $($entropyStats.min) / $($entropyStats.max) / $($entropyStats.avg) / $($entropyStats.last)"
    $lines += "- sparkline: $entropySpark\n"
}

$infoDensitySeries = @()
if ($sim -and $sim.info_density_series) { $infoDensitySeries = [double[]]$sim.info_density_series }
if ($infoDensitySeries.Count -ge 2) {
    $infoStats = Get-Stat -arr $infoDensitySeries
    $infoSpark = New-Sparkline -arr $infoDensitySeries -maxLen $SparkLen -Set $AsciiSet -Scale $AutoScale
    $lines += "## Info Density Series"
    $lines += "- count: $($infoDensitySeries.Count)"
    $lines += "- min/max/avg/last: $($infoStats.min) / $($infoStats.max) / $($infoStats.avg) / $($infoStats.last)"
    $lines += "- sparkline: $infoSpark\n"
}

$lines += "## Metadata"
$lines += "- source: $(Split-Path -Leaf $StatusJson)"
$lines += "- generated_at: $genAt"
$lines += "- summarized_at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')\n"

$lines += "## Next Scheduled Runs"
if ($next) {
    foreach ($k in $next.PSObject.Properties.Name) {
        $rawVal = $next.$k
        [DateTime]$t = [DateTime]::MinValue
        if ([DateTime]::TryParse($rawVal, [ref] $t)) {
            $delta = $t - (Get-Date)
            $eta = if ($delta.TotalSeconds -lt 0) { 'in the past' } else { "in " + [string]([timespan]::FromSeconds([int]$delta.TotalSeconds)) }
            $lines += "- $($k): $rawVal ($eta)"
        }
        else {
            $lines += "- $($k): $rawVal"
        }
    }
}

$md = ($lines -join "`n") + "`n"
$dir = Split-Path -Parent $OutMd
if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
[void](Set-Content -LiteralPath $OutMd -Value $md -Encoding UTF8)
Write-Host "Wrote: $OutMd" -ForegroundColor Green

if ($OutJson) {
    $jsonSummary = @{
        source          = Split-Path -Leaf $StatusJson
        generated_at    = $genAt
        summarized_at   = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
        window_hours    = $windowHours
        final_state     = @{
            resonance    = $final.resonance
            entropy      = $final.entropy
            info_density = $final.info_density
            coherence    = $final.coherence
            phase        = $final.phase
        }
        resonance_stats = @{
            count = $resSeries.Count
            min   = $stats.min
            max   = $stats.max
            avg   = $stats.avg
            last  = $stats.last
        }
        trend           = @{
            direction = $trend.direction
            delta     = $trend.delta
            lookback  = $trend.lookback
        }
        sparkline       = $spark
    }
    $jsonDir = Split-Path -Parent $OutJson
    if (-not (Test-Path -LiteralPath $jsonDir)) { New-Item -ItemType Directory -Path $jsonDir -Force | Out-Null }
    [void](ConvertTo-Json -InputObject $jsonSummary -Depth 10 | Set-Content -LiteralPath $OutJson -Encoding UTF8)
    Write-Host "Wrote: $OutJson" -ForegroundColor Green
}

if ($Open) {
    if (Test-Path "${PWD}\scripts\open_file_safe.ps1") {
        [void](& "${PWD}\scripts\open_file_safe.ps1" -Path $OutMd)
    }
    else {
        [void](code $OutMd)
    }
}

exit 0