# Analyze Performance Trends
# Generates statistical analysis from historical benchmark data

param(
    [string]$BenchmarkLog = "$PSScriptRoot\..\outputs\performance_benchmark_log.jsonl",
    [string]$OutJson = "$PSScriptRoot\..\outputs\performance_trend_analysis.json",
    [string]$OutMd = "$PSScriptRoot\..\outputs\performance_trend_analysis.md",
    [int]$WindowHours = 24,
    [switch]$OpenMd
)

$ErrorActionPreference = "Stop"

Write-Host "📈 Analyzing Performance Trends..." -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $BenchmarkLog)) {
    Write-Host "❌ No benchmark data found at $BenchmarkLog" -ForegroundColor Red
    exit 1
}

# Load all benchmarks
$allBenchmarks = Get-Content $BenchmarkLog | ForEach-Object {
    try { $_ | ConvertFrom-Json } catch { $null }
} | Where-Object { $_ -ne $null }

Write-Host "📊 Loaded $($allBenchmarks.Count) benchmark records" -ForegroundColor Cyan

# Filter by time window
$cutoff = (Get-Date).AddHours(-$WindowHours)
$recentBenchmarks = $allBenchmarks | Where-Object {
    try {
        [DateTime]::Parse($_.timestamp) -gt $cutoff
    }
    catch {
        $false
    }
}

Write-Host "   Recent (${WindowHours}h): $($recentBenchmarks.Count) records" -ForegroundColor DarkGray
Write-Host ""

if ($recentBenchmarks.Count -lt 2) {
    Write-Host "⚠️  Not enough recent data for trend analysis (need at least 2 records)" -ForegroundColor Yellow
    exit 0
}

# Statistical analysis function
function Get-Stats {
    param([double[]]$values)
    
    if ($values.Count -eq 0) {
        return @{
            count  = 0
            mean   = 0
            median = 0
            min    = 0
            max    = 0
            stddev = 0
            trend  = "insufficient data"
        }
    }
    
    $sorted = $values | Sort-Object
    $mean = ($values | Measure-Object -Average).Average
    $median = if ($sorted.Count % 2 -eq 0) {
        ($sorted[$sorted.Count / 2 - 1] + $sorted[$sorted.Count / 2]) / 2
    }
    else {
        $sorted[[math]::Floor($sorted.Count / 2)]
    }
    
    $variance = ($values | ForEach-Object { [math]::Pow($_ - $mean, 2) } | Measure-Object -Average).Average
    $stddev = [math]::Sqrt($variance)
    
    # Simple trend: compare first half vs second half
    $halfPoint = [math]::Floor($values.Count / 2)
    $firstHalf = $values[0..($halfPoint - 1)] | Measure-Object -Average | Select-Object -ExpandProperty Average
    $secondHalf = $values[$halfPoint..($values.Count - 1)] | Measure-Object -Average | Select-Object -ExpandProperty Average
    
    $trend = if ($secondHalf -lt $firstHalf * 0.95) {
        "improving"
    }
    elseif ($secondHalf -gt $firstHalf * 1.05) {
        "degrading"
    }
    else {
        "stable"
    }
    
    return @{
        count  = $values.Count
        mean   = [math]::Round($mean, 2)
        median = [math]::Round($median, 2)
        min    = [math]::Round($sorted[0], 2)
        max    = [math]::Round($sorted[-1], 2)
        stddev = [math]::Round($stddev, 2)
        trend  = $trend
    }
}

# Analyze Lumen
$lumenLatencies = $recentBenchmarks | Where-Object { $_.lumen.available } | ForEach-Object { $_.lumen.avg_ms }
$lumenStats = Get-Stats -values $lumenLatencies

# Analyze LM Studio
$lmLatencies = $recentBenchmarks | Where-Object { $_.lm_studio.available } | ForEach-Object { $_.lm_studio.avg_ms }
$lmStats = Get-Stats -values $lmLatencies

# Availability stats
$lumenAvailability = ($recentBenchmarks | Where-Object { $_.lumen.available }).Count / $recentBenchmarks.Count * 100
$lmAvailability = ($recentBenchmarks | Where-Object { $_.lm_studio.available }).Count / $recentBenchmarks.Count * 100

# Build analysis
$analysis = @{
    generated_at   = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    window_hours   = $WindowHours
    total_records  = $allBenchmarks.Count
    recent_records = $recentBenchmarks.Count
    lumen          = @{
        stats                = $lumenStats
        availability_percent = [math]::Round($lumenAvailability, 1)
    }
    lm_studio      = @{
        stats                = $lmStats
        availability_percent = [math]::Round($lmAvailability, 1)
    }
    recommendation = ""
}

# Generate recommendation
if ($lumenStats.count -gt 0 -and $lmStats.count -gt 0) {
    $speedup = [math]::Round($lmStats.mean / $lumenStats.mean, 1)
    if ($lumenStats.mean -lt $lmStats.mean) {
        $analysis.recommendation = "Lumen is ${speedup}x faster. Use for latency-sensitive tasks."
    }
    else {
        $analysis.recommendation = "LM Studio is faster. Consider using for local inference."
    }
    
    # Add trend warnings
    if ($lumenStats.trend -eq "degrading") {
        $analysis.recommendation += " ⚠️ Lumen latency is degrading."
    }
    if ($lmStats.trend -eq "degrading") {
        $analysis.recommendation += " ⚠️ LM Studio performance is degrading."
    }
}
elseif ($lumenStats.count -gt 0) {
    $analysis.recommendation = "Only Lumen data available. Trend: $($lumenStats.trend)"
}
elseif ($lmStats.count -gt 0) {
    $analysis.recommendation = "Only LM Studio data available. Trend: $($lmStats.trend)"
}

# Save JSON
$outDir = Split-Path -Parent $OutJson
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

$analysis | ConvertTo-Json -Depth 10 | Set-Content -Path $OutJson -Encoding UTF8
Write-Host "✓ JSON saved: $OutJson" -ForegroundColor Green

# Generate Markdown Report
$md = @"
# Performance Trend Analysis

**Generated:** $($analysis.generated_at)  
**Window:** Last $WindowHours hours  
**Records:** $($analysis.recent_records) recent / $($analysis.total_records) total

---

## 🎯 Recommendation

$($analysis.recommendation)

---

## ⚡ Lumen Gateway

**Availability:** $($analysis.lumen.availability_percent)%

| Metric | Value |
|--------|-------|
| Records | $($lumenStats.count) |
| Mean Latency | $($lumenStats.mean) ms |
| Median | $($lumenStats.median) ms |
| Min / Max | $($lumenStats.min) ms / $($lumenStats.max) ms |
| Std Dev | $($lumenStats.stddev) ms |
| **Trend** | **$($lumenStats.trend.ToUpper())** |

---

## 🖥️ LM Studio Local

**Availability:** $($analysis.lm_studio.availability_percent)%

| Metric | Value |
|--------|-------|
| Records | $($lmStats.count) |
| Mean Latency | $($lmStats.mean) ms |
| Median | $($lmStats.median) ms |
| Min / Max | $($lmStats.min) ms / $($lmStats.max) ms |
| Std Dev | $($lmStats.stddev) ms |
| **Trend** | **$($lmStats.trend.ToUpper())** |

---

## 📊 Performance Comparison

| Backend | Latency (mean) | Variability (σ) | Trend |
|---------|---------------|-----------------|-------|
| Lumen | $($lumenStats.mean) ms | $($lumenStats.stddev) ms | $($lumenStats.trend) |
| LM Studio | $($lmStats.mean) ms | $($lmStats.stddev) ms | $($lmStats.trend) |

---

*Auto-generated by AGI Performance Monitor*
"@

$md | Set-Content -Path $OutMd -Encoding UTF8
Write-Host "✓ Markdown saved: $OutMd" -ForegroundColor Green

# Display summary
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Trend Summary" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "Lumen:     $($lumenStats.mean)ms (trend: $($lumenStats.trend))" -ForegroundColor $(
    if ($lumenStats.trend -eq 'improving') { 'Green' }
    elseif ($lumenStats.trend -eq 'stable') { 'Cyan' }
    else { 'Yellow' }
)
Write-Host "LM Studio: $($lmStats.mean)ms (trend: $($lmStats.trend))" -ForegroundColor $(
    if ($lmStats.trend -eq 'improving') { 'Green' }
    elseif ($lmStats.trend -eq 'stable') { 'Cyan' }
    else { 'Yellow' }
)
Write-Host ""
Write-Host "💡 $($analysis.recommendation)" -ForegroundColor White
Write-Host ""

if ($OpenMd) {
    Start-Process code $OutMd
    Write-Host "✓ Opened in editor" -ForegroundColor Green
}
