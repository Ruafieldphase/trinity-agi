param(
    [Parameter(Mandatory = $true)] [string]$ProjectId,
    [string]$ServiceName = "lumen-gateway"
)

# ----------------------------------------------------------------------------
# Lumen v1.7 - Logs-based Metrics Setup
# Creates/updates 4 user metrics used by the Phase 4 dashboard:
#   - logging.googleapis.com/user/cache_hit_rate
#   - logging.googleapis.com/user/cache_memory_usage_percent
#   - logging.googleapis.com/user/cache_avg_ttl_seconds
#   - logging.googleapis.com/user/unified_health_score
# ----------------------------------------------------------------------------

Write-Host "\n╔═══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Lumen v1.7: Setup Logs-based Metrics (GCP Logging)  ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════╝\n" -ForegroundColor Cyan

$commonFilter = "resource.type=\`"cloud_run_revision\`" AND resource.labels.service_name=\`"$ServiceName\`" AND jsonPayload.component=\`"feedback_loop\`" AND jsonPayload.metric=\`"feedback_metrics\`""

function Invoke-GCloud($argsArray) {
    $tmpOut = [System.IO.Path]::GetTempFileName()
    $cmdLine = "gcloud $($argsArray -join ' ') --project=$ProjectId"
    cmd /c "$cmdLine > `"$tmpOut`" 2>&1"
    $out = Get-Content -Path $tmpOut -Raw -ErrorAction SilentlyContinue
    Remove-Item $tmpOut -ErrorAction SilentlyContinue
    return $out
}

function Set-LogsBasedMetric {
    param(
        [Parameter(Mandatory = $true)] [string]$Name,
        [Parameter(Mandatory = $true)] [string]$Description,
        [Parameter(Mandatory = $true)] [string]$LogFilter,
        [Parameter(Mandatory = $true)] [string]$ValueExtractor,
        [Parameter(Mandatory = $true)] [string]$BucketOptionsJson
    )

    Write-Host "\n[•] Ensuring metric: $Name" -ForegroundColor Yellow
    $desc = Invoke-GCloud @("logging", "metrics", "describe", $Name)
    if ($desc -match "name: $Name") {
        Write-Host "   - Found. Updating..." -ForegroundColor Yellow
        # Build advanced metric config (distribution) JSON
        $bucketObj = $BucketOptionsJson | ConvertFrom-Json
        $unit = "1"
        if ($Name -eq "cache_avg_ttl_seconds") { $unit = "s" }
        $metricDescriptor = [ordered]@{
            metricKind  = "DELTA"
            valueType   = "DISTRIBUTION"
            unit        = $unit
            displayName = $Description
        }
        $configObj = [ordered]@{
            name             = $Name
            description      = $Description
            filter           = $LogFilter
            valueExtractor   = $ValueExtractor
            bucketOptions    = $bucketObj
            metricDescriptor = $metricDescriptor
        }
        $tmpConfig = [System.IO.Path]::GetTempFileName()
        $configObj | ConvertTo-Json -Depth 10 | Out-File -FilePath $tmpConfig -Encoding UTF8
        $args = @(
            "logging", "metrics", "update", $Name,
            "--config-from-file=$tmpConfig"
        )
        $out = Invoke-GCloud $args
        Remove-Item $tmpConfig -ErrorAction SilentlyContinue
        Write-Host "   - Update output: $out" -ForegroundColor DarkGray
    }
    else {
        Write-Host "   - Not found. Creating..." -ForegroundColor Yellow
        # Build advanced metric config (distribution) JSON
        $bucketObj = $BucketOptionsJson | ConvertFrom-Json
        $unit = "1"
        if ($Name -eq "cache_avg_ttl_seconds") { $unit = "s" }
        $metricDescriptor = [ordered]@{
            metricKind  = "DELTA"
            valueType   = "DISTRIBUTION"
            unit        = $unit
            displayName = $Description
        }
        $configObj = [ordered]@{
            name             = $Name
            description      = $Description
            filter           = $LogFilter
            valueExtractor   = $ValueExtractor
            bucketOptions    = $bucketObj
            metricDescriptor = $metricDescriptor
        }
        $tmpConfig = [System.IO.Path]::GetTempFileName()
        $configObj | ConvertTo-Json -Depth 10 | Out-File -FilePath $tmpConfig -Encoding UTF8
        $args = @(
            "logging", "metrics", "create", $Name,
            "--config-from-file=$tmpConfig"
        )
        $out = Invoke-GCloud $args
        Remove-Item $tmpConfig -ErrorAction SilentlyContinue
        Write-Host "   - Create output: $out" -ForegroundColor DarkGray
    }
}

# Bucket options (explicit) for distribution metrics
$Buckets_HitRate = @'
{
  "explicitBuckets": {"bounds": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]}
}
'@
$Buckets_MemoryPercent = @'
{
  "explicitBuckets": {"bounds": [0, 50, 70, 85, 95, 100]}
}
'@
$Buckets_TTLSeconds = @'
{
  "explicitBuckets": {"bounds": [0, 60, 300, 600, 1800, 3600, 7200, 14400]}
}
'@
$Buckets_HealthScore = @'
{
  "explicitBuckets": {"bounds": [0, 50, 70, 80, 90, 100]}
}
'@

# Ensure metrics
Set-LogsBasedMetric -Name "cache_hit_rate" -Description "Feedback Loop: Cache hit rate (0..1)" -LogFilter $commonFilter -ValueExtractor 'EXTRACT(jsonPayload.cache_hit_rate)' -BucketOptionsJson $Buckets_HitRate
Set-LogsBasedMetric -Name "cache_memory_usage_percent" -Description "Feedback Loop: Cache memory usage percent (0..100)" -LogFilter $commonFilter -ValueExtractor 'EXTRACT(jsonPayload.cache_memory_usage_percent)' -BucketOptionsJson $Buckets_MemoryPercent
Set-LogsBasedMetric -Name "cache_avg_ttl_seconds" -Description "Feedback Loop: Average TTL in seconds" -LogFilter $commonFilter -ValueExtractor 'EXTRACT(jsonPayload.cache_avg_ttl_seconds)' -BucketOptionsJson $Buckets_TTLSeconds
Set-LogsBasedMetric -Name "unified_health_score" -Description "Feedback Loop: Unified health score (0..100)" -LogFilter $commonFilter -ValueExtractor 'EXTRACT(jsonPayload.unified_health_score)' -BucketOptionsJson $Buckets_HealthScore

Write-Host "\n✓ Logs-based metrics ensured for project: $ProjectId" -ForegroundColor Green
