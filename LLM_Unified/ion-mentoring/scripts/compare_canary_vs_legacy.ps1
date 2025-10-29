param(
    [Parameter(Mandatory = $false)]
    [string]$CanaryUrl = 'https://ion-api-canary-x4qvsargwa-uc.a.run.app',
    [Parameter(Mandatory = $false)]
    [string]$LegacyUrl = 'https://ion-api-x4qvsargwa-uc.a.run.app',

    # Request/Comparison controls
    [Parameter(Mandatory = $false)] [ValidateSet('GET', 'POST')]
    [string]$Method = 'GET',
    [Parameter(Mandatory = $false)] [string]$EndpointPath = '',
    [Parameter(Mandatory = $false)] [string]$CanaryEndpointPath = '',
    [Parameter(Mandatory = $false)] [string]$LegacyEndpointPath = '',
    [Parameter(Mandatory = $false)] [string]$CanaryBodyJson = '',
    [Parameter(Mandatory = $false)] [string]$LegacyBodyJson = '',
    [Parameter(Mandatory = $false)] [string]$HeadersJson = '',
    [Parameter(Mandatory = $false)] [int]$RequestsPerSide = 10,
    [Parameter(Mandatory = $false)] [int]$Retries = 0,
    [Parameter(Mandatory = $false)] [int]$DelayMsBetweenRequests = 50,
    [Parameter(Mandatory = $false)] [int]$TimeoutSec = 20,
    [Parameter(Mandatory = $false)] [int]$MinSuccessRatePercent = 80,
    [Parameter(Mandatory = $false)] [string]$OutJson = ''
)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function Get-Percentile {
    param([double[]]$Values, [double]$Percentile)
    if (-not $Values -or $Values.Count -eq 0) { return $null }
    $sorted = $Values | Sort-Object
    $n = $sorted.Count
    $rank = ($Percentile / 100.0) * ($n - 1)
    $lower = [math]::Floor($rank)
    $upper = [math]::Ceiling($rank)
    if ($lower -eq $upper) { return [math]::Round($sorted[$lower], 3) }
    $weight = $rank - $lower
    $value = $sorted[$lower] + $weight * ($sorted[$upper] - $sorted[$lower])
    return [math]::Round($value, 3)
}

function Invoke-MeasureRequest {
    param(
        [string]$BaseUrl,
        [string]$Endpoint,
        [string]$Method,
        [string]$BodyJson,
        [hashtable]$Headers
    )
    $base = $BaseUrl.TrimEnd('/')
    $path = ''
    if ($Endpoint) {
        if ($Endpoint.StartsWith('/')) { $path = $Endpoint }
        else { $path = "/$Endpoint" }
    }
    $uri = "$base$path"
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        if ($Method -eq 'POST') {
            $params = @{ Uri = $uri; Method = 'POST'; ContentType = 'application/json'; Body = $BodyJson; TimeoutSec = $TimeoutSec; ErrorAction = 'Stop' }
            if ($Headers) { $params.Headers = $Headers }
            Invoke-RestMethod @params | Out-Null
        }
        else {
            $params = @{ Uri = $uri; Method = 'GET'; TimeoutSec = $TimeoutSec; ErrorAction = 'Stop' }
            if ($Headers) { $params.Headers = $Headers }
            Invoke-RestMethod @params | Out-Null
        }
        $sw.Stop()
        return @{ ok = $true; code = 200; ms = [math]::Round($sw.Elapsed.TotalMilliseconds, 3) }
    }
    catch {
        $sw.Stop()
        $code = -1
        if ($_.Exception.Response) { try { $code = [int]$_.Exception.Response.StatusCode } catch { $code = -1 } }
        return @{ ok = $false; code = $code; ms = [math]::Round($sw.Elapsed.TotalMilliseconds, 3); err = $_.Exception.Message }
    }
}

function Get-RequestHeaders {
    param([string]$HeadersJson)
    if ([string]::IsNullOrWhiteSpace($HeadersJson)) { return @{} }
    try {
        $obj = ConvertFrom-Json -InputObject $HeadersJson -Depth 5
        if ($null -eq $obj) { return @{} }
        if ($obj -is [hashtable]) { return $obj }
        $hash = @{}
        $props = ($obj | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name)
        foreach ($name in $props) { $hash[$name] = $obj.$name }
        return $hash
    }
    catch {
        return @{}
    }
}

Write-Host ("[compare] Starting comparison: Canary={0} Legacy={1} Method={2} RequestsPerSide={3}" -f $CanaryUrl, $LegacyUrl, $Method, $RequestsPerSide) -ForegroundColor Cyan

$commonHeaders = Get-RequestHeaders -HeadersJson $HeadersJson

# Resolve endpoints per side
$canaryPath = if ($CanaryEndpointPath) { $CanaryEndpointPath } elseif ($EndpointPath) { $EndpointPath } else { '' }
$legacyPath = if ($LegacyEndpointPath) { $LegacyEndpointPath } elseif ($EndpointPath) { $EndpointPath } else { '' }

function Measure-Side {
    param(
        [string]$BaseUrl,
        [string]$Endpoint,
        [string]$Method,
        [string]$BodyJson
    )
    $ok = 0; $err = 0; $times = New-Object System.Collections.Generic.List[double]
    $codes = @{}
    for ($i = 0; $i -lt $RequestsPerSide; $i++) {
        $r = Invoke-MeasureRequest -BaseUrl $BaseUrl -Endpoint $Endpoint -Method $Method -BodyJson $BodyJson -Headers $commonHeaders
        if ($r.ok) { $ok++ } else { $err++ }
        if ($null -ne $r.ms) { [void]$times.Add([double]$r.ms) }
        $codeKey = [string]$r.code
        if (-not $codes.ContainsKey($codeKey)) { $codes[$codeKey] = 0 }
        $codes[$codeKey] = $codes[$codeKey] + 1
        if ($DelayMsBetweenRequests -gt 0) { Start-Sleep -Milliseconds $DelayMsBetweenRequests }
    }
    $total = $ok + $err
    $errorRate = if ($total -gt 0) { [math]::Round(($err * 100.0) / $total, 3) } else { 0 }
    $mean = if ($times.Count -gt 0) { [math]::Round(($times | Measure-Object -Average).Average, 3) } else { $null }
    $p50 = Get-Percentile -Values $times.ToArray() -Percentile 50
    $p95 = Get-Percentile -Values $times.ToArray() -Percentile 95
    $p99 = Get-Percentile -Values $times.ToArray() -Percentile 99
    return [pscustomobject]@{
        request_count      = $total
        success_count      = $ok
        error_count        = $err
        error_rate_percent = $errorRate
        mean_ms            = $mean
        p50_ms             = $p50
        p95_ms             = $p95
        p99_ms             = $p99
        status_code_hist   = [pscustomobject]$codes
    }
}

# Use provided body JSONs as-is; do not auto-shape to avoid schema mismatches.
$canaryStats = Measure-Side -BaseUrl $CanaryUrl -Endpoint $canaryPath -Method $Method -BodyJson $CanaryBodyJson
$legacyStats = Measure-Side -BaseUrl $LegacyUrl -Endpoint $legacyPath -Method $Method -BodyJson $LegacyBodyJson

# Comparison thresholds
$maxErrorDeltaPctPoints = 0.5   # +0.5%p allowed
$maxP95DeltaPercent = 10        # +10% allowed

$comparison = [pscustomobject]@{}
if ($legacyStats.request_count -gt 0 -and $canaryStats.request_count -gt 0) {
    $errorDelta = [math]::Round(($canaryStats.error_rate_percent - $legacyStats.error_rate_percent), 3)
    $p95DeltaPct = $null
    if ($legacyStats.p95_ms -and $legacyStats.p95_ms -gt 0) {
        $p95DeltaPct = [math]::Round((($canaryStats.p95_ms - $legacyStats.p95_ms) * 100.0 / $legacyStats.p95_ms), 3)
    }
    $canarySuccessRate = if ($canaryStats.request_count -gt 0) { [math]::Round(($canaryStats.success_count * 100.0) / $canaryStats.request_count, 3) } else { 0 }
    $legacySuccessRate = if ($legacyStats.request_count -gt 0) { [math]::Round(($legacyStats.success_count * 100.0) / $legacyStats.request_count, 3) } else { 0 }
    $minSuccessPass = ($canarySuccessRate -ge $MinSuccessRatePercent) -and ($legacySuccessRate -ge $MinSuccessRatePercent)
    $errorPass = ($errorDelta -le $maxErrorDeltaPctPoints)
    $p95Pass = $true
    if ($null -ne $p95DeltaPct) { $p95Pass = ($p95DeltaPct -le $maxP95DeltaPercent) }
    $status = if ($minSuccessPass -and $errorPass -and $p95Pass) { 'pass' } else { 'fail' }
    $comparison = [pscustomobject]@{
        status        = $status
        thresholds    = [pscustomobject]@{
            max_error_rate_delta_pct_points = $maxErrorDeltaPctPoints
            max_p95_latency_delta_percent   = $maxP95DeltaPercent
            min_success_rate_percent        = $MinSuccessRatePercent
        }
        deltas        = [pscustomobject]@{
            error_rate_delta_pct_points = $errorDelta
            p95_latency_delta_percent   = $p95DeltaPct
        }
        success_rates = [pscustomobject]@{
            canary = $canarySuccessRate
            legacy = $legacySuccessRate
        }
    }
}
else {
    $comparison = [pscustomobject]@{ status = 'insufficient_data'; reason = 'One or both sides have zero requests measured.' }
}

$result = [pscustomobject]@{
    canary      = $canaryStats
    legacy      = $legacyStats
    comparison  = $comparison
    measured_at = (Get-Date).ToString('s')
}

$json = $result | ConvertTo-Json -Depth 8
Write-Host "\n[compare] Result:\n$json" -ForegroundColor Green

if ($OutJson) {
    try { $json | Out-File -FilePath $OutJson -Encoding utf8; Write-Host ("[compare] Saved to {0}" -f $OutJson) -ForegroundColor Yellow } catch { }
}

if ($comparison.status -eq 'fail') { exit 2 }
exit 0
