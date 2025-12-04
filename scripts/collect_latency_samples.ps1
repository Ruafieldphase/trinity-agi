param(
    [string]$Uri = 'http://127.0.0.1:8091/api/health',
    [int]$Samples = 3,
    [string]$OutFile = 'outputs/latency_samples_micro_cycle.json'
)
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath (Split-Path -Parent $OutFile))) {
    New-Item -ItemType Directory -Path (Split-Path -Parent $OutFile) -Force | Out-Null
}

$results = @()
for ($i = 1; $i -le $Samples; $i++) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $status = 'ok'
    try {
        Invoke-RestMethod -Uri $Uri -TimeoutSec 5 | Out-Null
    }
    catch {
        $status = 'error'
    }
    $sw.Stop()
    $results += [pscustomobject]@{
        index     = $i
        ms        = [math]::Round($sw.Elapsed.TotalMilliseconds, 2)
        status    = $status
        timestamp = (Get-Date).ToString('o')
    }
    Start-Sleep -Milliseconds 300
}

$json = $results | ConvertTo-Json -Depth 5
Set-Content -LiteralPath $OutFile -Value $json -Encoding UTF8
Write-Host $json