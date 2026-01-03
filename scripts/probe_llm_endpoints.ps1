param(
    [int]$Requests = 5,
    [string[]]$Endpoints = @("http://localhost:8080/v1/models", "http://localhost:18090/v1/models"),
    [string]$OutJson = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\local_latency_probe_latest.json",
    [int]$TimeoutSec = 10
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'

function Get-Stats {
    param([double[]]$values)
    if (-not $values -or $values.Count -eq 0) { return @{ count = 0; mean_ms = $null; p95_ms = $null; min_ms = $null; max_ms = $null } }
    $count = $values.Count
    $mean = [Math]::Round(($values | Measure-Object -Average).Average, 2)
    $sorted = $values | Sort-Object
    $p95Index = [Math]::Ceiling(0.95 * $count) - 1
    if ($p95Index -lt 0) { $p95Index = 0 }
    if ($p95Index -ge $sorted.Count) { $p95Index = $sorted.Count - 1 }
    $p95 = [Math]::Round($sorted[$p95Index], 2)
    $min = [Math]::Round($sorted[0], 2)
    $max = [Math]::Round($sorted[-1], 2)
    return @{ count = $count; mean_ms = $mean; p95_ms = $p95; min_ms = $min; max_ms = $max }
}

$result = @{
    timestamp   = (Get-Date).ToString("s")
    requests    = $Requests
    timeout_sec = $TimeoutSec
    endpoints   = @()
    notes       = @{
        description = "Short-window latency probe using GET /v1/models"
        rationale   = "Reconcile dashboard long-window baseline with immediate probe"
    }
    version     = "1.0.0"
}

foreach ($ep in $Endpoints) {
    $samples = New-Object System.Collections.Generic.List[double]
    $errors = New-Object System.Collections.Generic.List[string]
    for ($i = 0; $i -lt $Requests; $i++) {
        try {
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            $null = Invoke-WebRequest -Method GET -Uri $ep -TimeoutSec $TimeoutSec -UseBasicParsing
            $sw.Stop()
            $samples.Add([Math]::Round($sw.Elapsed.TotalMilliseconds, 2))
        }
        catch {
            $sw.Stop()
            $errors.Add($_.Exception.Message)
        }
    }
    $stats = Get-Stats -values $samples
    $result.endpoints += @{
        url           = $ep
        success_count = $stats.count
        fail_count    = $Requests - $stats.count
        samples_ms    = $samples
        mean_ms       = $stats.mean_ms
        p95_ms        = $stats.p95_ms
        min_ms        = $stats.min_ms
        max_ms        = $stats.max_ms
        errors        = $errors
    }
}

# Ensure output directory exists
$outDir = Split-Path -Parent $OutJson
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

$result | ConvertTo-Json -Depth 6 | Out-File -FilePath $OutJson -Encoding UTF8

# Exit code: success if any endpoint had at least 1 success
$anySuccess = $result.endpoints | Where-Object { $_.success_count -gt 0 }
if ($anySuccess) { exit 0 } else { exit 1 }