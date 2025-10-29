# Requires: gcloud CLI, permissions to read Cloud Logging
param(
    [Parameter(Mandatory = $true)] [string]$ProjectId,
    [string]$LegacyService = 'ion-api',
    [string]$CanaryService = 'ion-api-canary',
    [string]$Freshness = '15m',
    [int]$Limit = 20000
)

$ErrorActionPreference = 'Stop'

function Get-ServiceMetrics {
    param(
        [string]$Project,
        [string]$Service,
        [string]$Freshness,
        [int]$Limit
    )
    $filter = @"
resource.type="cloud_run_revision" AND
resource.labels.service_name="$Service" AND
logName="projects/$Project/logs/run.googleapis.com%2Frequests"
"@
    $json = & gcloud logging read $filter --project=$Project --freshness=$Freshness --limit=$Limit --format=json 2>$null
    if (-not $json -or $json.Trim().Length -eq 0) {
        return [pscustomobject]@{ service = $Service; total = 0; errors5xx = 0; errors4xx = 0; errorRate5xx = 0.0; p95ms = $null }
    }
    $entries = $null
    try { $entries = $json | ConvertFrom-Json } catch { $entries = @() }
    if (-not $entries) { return [pscustomobject]@{ service = $Service; total = 0; errors5xx = 0; errors4xx = 0; errorRate5xx = 0.0; p95ms = $null } }

    $latencies = New-Object System.Collections.Generic.List[int]
    $total = 0
    $errors5xx = 0
    $errors4xx = 0

    foreach ($e in $entries) {
        $status = $null
        if ($e.httpRequest -and $e.httpRequest.status) { $status = [int]$e.httpRequest.status }
        elseif ($e.jsonPayload -and $e.jsonPayload.status) { $status = [int]$e.jsonPayload.status }
        if (-not $status) { continue }
        $total++
        if ($status -ge 500) { $errors5xx++ }
        elseif ($status -ge 400) { $errors4xx++ }

        $latRaw = $null
        if ($e.httpRequest -and $e.httpRequest.latency) { $latRaw = $e.httpRequest.latency }
        elseif ($e.jsonPayload -and $e.jsonPayload.latency) { $latRaw = $e.jsonPayload.latency }
        elseif ($e.jsonPayload -and $e.jsonPayload.response_latency) { $latRaw = $e.jsonPayload.response_latency }

        $latSec = $null
        if ($latRaw) {
            if ($latRaw -is [string]) {
                if ($latRaw -match '([0-9]+\.?[0-9]*)s') { $latSec = [double]$matches[1] }
                elseif ($latRaw -match '([0-9]+\.?[0-9]*)') { $latSec = [double]$latRaw }
            }
            elseif ($latRaw -is [double] -or $latRaw -is [int]) {
                $latSec = [double]$latRaw
            }
        }
        if ($latSec -ne $null) {
            $latMs = [int]([math]::Round($latSec * 1000))
            $latencies.Add($latMs)
        }
    }

    if ($total -eq 0) {
        return [pscustomobject]@{ service = $Service; total = 0; errors5xx = 0; errors4xx = 0; errorRate5xx = 0.0; p95ms = $null }
    }

    $errorRate5xx = if ($total -gt 0) { [math]::Round(($errors5xx / $total) * 100, 3) } else { 0.0 }
    $p95ms = $null
    if ($latencies.Count -gt 0) {
        $arr = $latencies.ToArray()
        [array]::Sort($arr)
        $idx = [int][math]::Ceiling(0.95 * $arr.Length) - 1
        if ($idx -lt 0) { $idx = 0 }
        if ($idx -ge $arr.Length) { $idx = $arr.Length - 1 }
        $p95ms = $arr[$idx]
    }

    return [pscustomobject]@{
        service      = $Service
        total        = $total
        errors5xx    = $errors5xx
        errors4xx    = $errors4xx
        errorRate5xx = $errorRate5xx
        p95ms        = $p95ms
    }
}

$legacy = Get-ServiceMetrics -Project $ProjectId -Service $LegacyService -Freshness $Freshness -Limit $Limit
$canary = Get-ServiceMetrics -Project $ProjectId -Service $CanaryService -Freshness $Freshness -Limit $Limit

$results = @($legacy, $canary)
$results | Format-Table -AutoSize

Write-Host ""
Write-Host "SLO Deltas (Canary vs Legacy, $Freshness):"
$deltaErr = [math]::Round(($canary.errorRate5xx - $legacy.errorRate5xx), 3)
if ($legacy.p95ms -and $canary.p95ms) {
    $deltaP95pct = [math]::Round((($canary.p95ms - $legacy.p95ms) / [double]$legacy.p95ms) * 100, 2)
    Write-Host ("  Error-rate (5xx) delta: {0}%p (canary {1}%, legacy {2}%); gate <= +0.5%p" -f $deltaErr, $canary.errorRate5xx, $legacy.errorRate5xx)
    Write-Host ("  P95 latency delta: {0}% (canary {1} ms, legacy {2} ms); gate <= +10%" -f $deltaP95pct, $canary.p95ms, $legacy.p95ms)
}
else {
    Write-Host ("  Error-rate (5xx) delta: {0}%p (canary {1}%, legacy {2}%); gate <= +0.5%p" -f $deltaErr, $canary.errorRate5xx, $legacy.errorRate5xx)
    Write-Host "  P95 latency delta: insufficient latency data in logs"
}

# Save JSON snapshot
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$outDir = Join-Path (Join-Path $PSScriptRoot '..') 'outputs'
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }
$outPath = Join-Path $outDir "slo_snapshot_${timestamp}.json"
$payload = [pscustomobject]@{
    project   = $ProjectId
    freshness = $Freshness
    legacy    = $legacy
    canary    = $canary
    deltas    = [pscustomobject]@{ errorRate5xx_delta_percent_points = $deltaErr; note = 'P95 delta shown above if available' }
}
$payload | ConvertTo-Json -Depth 5 | Out-File -FilePath $outPath -Encoding UTF8
Write-Host "\nSnapshot saved to: $outPath"
