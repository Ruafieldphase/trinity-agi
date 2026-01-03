# Adaptive Routing Optimizer
# Automatically adjusts routing policy based on performance trends

param(
    [string]$TrendAnalysis = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\performance_trend_analysis.json",
    [string]$PolicyFile = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\routing_policy.json",
    [switch]$DryRun,
    [switch]$Verbose
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"

Write-Host "🎯 Adaptive Routing Optimizer" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $TrendAnalysis)) {
    Write-Host "❌ Trend analysis not found. Run analyze_performance_trends.ps1 first." -ForegroundColor Red
    exit 1
}

# Load trend data
$trends = Get-Content $TrendAnalysis | ConvertFrom-Json

Write-Host "📊 Trend Data Loaded" -ForegroundColor Green
Write-Host "   Core: $($trends.Core.stats.mean)ms ($($trends.Core.stats.trend))" -ForegroundColor DarkGray
Write-Host "   LM Studio: $($trends.lm_studio.stats.mean)ms ($($trends.lm_studio.stats.trend))" -ForegroundColor DarkGray
Write-Host ""

# Load or create policy
$policy = if (Test-Path $PolicyFile) {
    $existing = Get-Content $PolicyFile | ConvertFrom-Json
    Write-Host "📋 Existing Policy Loaded" -ForegroundColor Green
    if ($Verbose) {
        Write-Host "   Primary: $($existing.primary_backend)" -ForegroundColor DarkGray
        Write-Host "   Threshold: $($existing.latency_threshold_ms)ms" -ForegroundColor DarkGray
    }
    $existing
}
else {
    Write-Host "📋 Creating New Policy" -ForegroundColor Yellow
    @{
        version              = "1.0"
        primary_backend      = "Core"
        fallback_backend     = "lm_studio"
        latency_threshold_ms = 2000
        auto_adjust          = $true
        last_updated         = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    }
}

Write-Host ""

# Optimization logic
$changes = @()
$newPolicy = $policy.PSObject.Copy()

# Rule 1: Select primary based on availability and performance
if ($trends.Core.availability_percent -gt 90 -and $trends.lm_studio.availability_percent -gt 90) {
    # Both available - choose faster
    $optimalPrimary = if ($trends.Core.stats.mean -lt $trends.lm_studio.stats.mean) {
        "Core"
    }
    else {
        "lm_studio"
    }
    
    if ($policy.primary_backend -ne $optimalPrimary) {
        $changes += "Primary backend: $($policy.primary_backend) → $optimalPrimary"
        $newPolicy.primary_backend = $optimalPrimary
    }
    
    # Set fallback to the other one
    $optimalFallback = if ($optimalPrimary -eq "Core") { "lm_studio" } else { "Core" }
    if ($policy.fallback_backend -ne $optimalFallback) {
        $changes += "Fallback backend: $($policy.fallback_backend) → $optimalFallback"
        $newPolicy.fallback_backend = $optimalFallback
    }
    
}
elseif ($trends.Core.availability_percent -gt 50) {
    # Prefer Core if available
    if ($policy.primary_backend -ne "Core") {
        $changes += "Primary backend: $($policy.primary_backend) → Core (high availability)"
        $newPolicy.primary_backend = "Core"
    }
}
elseif ($trends.lm_studio.availability_percent -gt 50) {
    # Fallback to LM Studio
    if ($policy.primary_backend -ne "lm_studio") {
        $changes += "Primary backend: $($policy.primary_backend) → lm_studio (Core unavailable)"
        $newPolicy.primary_backend = "lm_studio"
    }
}

# Rule 2: Adjust threshold based on performance variance
$primaryStats = if ($newPolicy.primary_backend -eq "Core") {
    $trends.Core.stats
}
else {
    $trends.lm_studio.stats
}

# Set threshold to mean + 2*stddev (covers 95% of cases under normal distribution)
$optimalThreshold = [math]::Round($primaryStats.mean + (2 * $primaryStats.stddev), 0)

# Clamp to reasonable range
$optimalThreshold = [math]::Max(500, [math]::Min($optimalThreshold, 10000))

if ([math]::Abs($policy.latency_threshold_ms - $optimalThreshold) -gt 100) {
    $changes += "Latency threshold: $($policy.latency_threshold_ms)ms → ${optimalThreshold}ms"
    $newPolicy.latency_threshold_ms = $optimalThreshold
}

# Rule 3: Add health warnings
$newPolicy.health_warnings = @()
if ($trends.Core.stats.trend -eq "degrading") {
    $newPolicy.health_warnings += "Core performance is degrading"
}
if ($trends.lm_studio.stats.trend -eq "degrading") {
    $newPolicy.health_warnings += "LM Studio performance is degrading"
}

# Update metadata
$newPolicy.last_updated = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$newPolicy.last_analysis = $trends.generated_at

# Display changes
if ($changes.Count -gt 0) {
    Write-Host "🔄 Proposed Changes:" -ForegroundColor Yellow
    foreach ($change in $changes) {
        Write-Host "   • $change" -ForegroundColor White
    }
    Write-Host ""
    
    if ($DryRun) {
        Write-Host "🔍 DRY RUN - No changes applied" -ForegroundColor Cyan
    }
    else {
        # Save policy
        $outDir = Split-Path -Parent $PolicyFile
        if (-not (Test-Path $outDir)) {
            New-Item -ItemType Directory -Path $outDir -Force | Out-Null
        }
        
        $newPolicy | ConvertTo-Json -Depth 10 | Set-Content -Path $PolicyFile -Encoding UTF8
        
        Write-Host "✓ Policy updated and saved to $PolicyFile" -ForegroundColor Green
    }
}
else {
    Write-Host "✓ Policy is already optimal - no changes needed" -ForegroundColor Green
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Current Policy" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Primary: $($newPolicy.primary_backend)" -ForegroundColor White
Write-Host "Fallback: $($newPolicy.fallback_backend)" -ForegroundColor White
Write-Host "Threshold: $($newPolicy.latency_threshold_ms)ms" -ForegroundColor White

if ($newPolicy.health_warnings.Count -gt 0) {
    Write-Host ""
    Write-Host "⚠️  Health Warnings:" -ForegroundColor Yellow
    foreach ($warning in $newPolicy.health_warnings) {
        Write-Host "   • $warning" -ForegroundColor Yellow
    }
}

Write-Host ""