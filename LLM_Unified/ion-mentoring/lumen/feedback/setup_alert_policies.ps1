param(
    [Parameter(Mandatory = $true)] [string]$ProjectId,
    [string]$ServiceName = "lumen-gateway",
    [int]$HitRateThresholdPercent = 50,
    [int]$MemoryThresholdPercent = 90,
    [int]$HealthThreshold = 60,
    [switch]$DryRun
)

# Header banner (disabled to avoid encoding/quoting issues)
# Write-Host "`n╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
# Write-Host   "║  Lumen v1.7: Setup Cloud Monitoring Alerts     ║" -ForegroundColor Cyan
# Write-Host   "╚══════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

function Invoke-GCloud($argsArray) {
    $tmpOut = [System.IO.Path]::GetTempFileName()
    $cmdLine = "gcloud $($argsArray -join ' ') --project=$ProjectId"
    cmd /c "$cmdLine > `"$tmpOut`" 2>&1"
    $out = Get-Content -Path $tmpOut -Raw -ErrorAction SilentlyContinue
    Remove-Item $tmpOut -ErrorAction SilentlyContinue
    return $out
}

function Get-AlertPolicyByDisplayName([string]$displayName) {
    $json = Invoke-GCloud @("monitoring", "policies", "list", "--format=json")
    if (-not $json) { return $null }
    try {
        $arr = $json | ConvertFrom-Json
        foreach ($p in $arr) {
            if ($p.displayName -eq $displayName) { return $p }
        }
    }
    catch {}
    return $null
}

function Ensure-MqlAlertPolicy {
    param(
        [Parameter(Mandatory = $true)] [string]$DisplayName,
        [Parameter(Mandatory = $true)] [string]$ConditionDisplayName,
        [Parameter(Mandatory = $true)] [string]$MqlQuery,
        [string]$AutoClose = "604800s"  # 7 days
    )

    Write-Host "`n[•] Ensuring alert policy: $DisplayName" -ForegroundColor Yellow
    $existing = Get-AlertPolicyByDisplayName -displayName $DisplayName

    $policyObj = [ordered]@{
        displayName   = $DisplayName
        combiner      = "OR"
        conditions    = @(@{
                displayName                      = $ConditionDisplayName
                conditionMonitoringQueryLanguage = @{ query = $MqlQuery }
            })
        alertStrategy = @{ autoClose = $AutoClose }
        enabled       = $true
    }

    if ($DryRun) {
        Write-Host "   - DryRun: Would apply policy below:" -ForegroundColor DarkGray
        $policyObj | ConvertTo-Json -Depth 10 | Write-Output
        return
    }

    $tmpPolicy = [System.IO.Path]::GetTempFileName()
    try {
        if ($existing -and $existing.name) {
            # Update path requires name present
            $policyObj.name = $existing.name
            $policyObj | ConvertTo-Json -Depth 10 | Out-File -FilePath $tmpPolicy -Encoding UTF8
            $out = Invoke-GCloud @("monitoring", "policies", "update", "--policy-from-file=$tmpPolicy")
            Write-Host "   - Updated: $($existing.name)" -ForegroundColor DarkGray
        }
        else {
            $policyObj | ConvertTo-Json -Depth 10 | Out-File -FilePath $tmpPolicy -Encoding UTF8
            $out = Invoke-GCloud @("monitoring", "policies", "create", "--policy-from-file=$tmpPolicy")
            Write-Host "   - Created: $DisplayName" -ForegroundColor DarkGray
        }
    }
    finally {
        Remove-Item $tmpPolicy -ErrorAction SilentlyContinue
    }
}

# Build MQL for distribution metrics from logs-based metrics
$thrHit = [math]::Max(0, [math]::Min(100, $HitRateThresholdPercent)) / 100.0
$thrMem = [math]::Max(0, [math]::Min(100, $MemoryThresholdPercent))
$thrHealth = [math]::Max(0, [math]::Min(100, $HealthThreshold))

$mql_hit = @'
fetch logging.googleapis.com/user/cache_hit_rate
| align delta(1m)
| every 1m
| group_by [], [p50: percentile(value, 50)]
| condition lt(p50, __THR__)
'@
$mql_hit = $mql_hit.Replace("__THR__", $thrHit.ToString("0.00", [Globalization.CultureInfo]::InvariantCulture))

$mql_mem = @'
fetch logging.googleapis.com/user/cache_memory_usage_percent
| align delta(1m)
| every 1m
| group_by [], [p90: percentile(value, 90)]
| condition gt(p90, __THR__)
'@
$mql_mem = $mql_mem.Replace("__THR__", $thrMem.ToString([Globalization.CultureInfo]::InvariantCulture))

$mql_health = @'
fetch logging.googleapis.com/user/unified_health_score
| align delta(1m)
| every 1m
| group_by [], [p50: percentile(value, 50)]
| condition lt(p50, __THR__)
'@
$mql_health = $mql_health.Replace("__THR__", $thrHealth.ToString([Globalization.CultureInfo]::InvariantCulture))

$thrHitLabel = $thrHit.ToString('0.00', [Globalization.CultureInfo]::InvariantCulture)
$condHit = 'cache_hit_rate p50 ' + '<' + ' ' + $thrHitLabel + ' (5m)'
$condMem = 'memory_usage_percent p90 ' + '>' + ' ' + $thrMem + ' (5m)'
$condHealth = 'unified_health_score p50 ' + '<' + ' ' + $thrHealth + ' (5m)'

Ensure-MqlAlertPolicy -DisplayName "Lumen: Cache Hit Rate Low" -ConditionDisplayName $condHit -MqlQuery $mql_hit
Ensure-MqlAlertPolicy -DisplayName "Lumen: Memory Usage High" -ConditionDisplayName $condMem -MqlQuery $mql_mem
Ensure-MqlAlertPolicy -DisplayName "Lumen: Unified Health Low" -ConditionDisplayName $condHealth -MqlQuery $mql_health

Write-Host ("`n" + '✓ Alert policies ensured for project: ' + $ProjectId) -ForegroundColor Green
