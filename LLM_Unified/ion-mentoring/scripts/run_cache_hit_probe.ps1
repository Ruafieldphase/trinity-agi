# Requires: PowerShell 5+
# Purpose: Send the same chat request twice to trigger cache HIT on the second call

[CmdletBinding()]
param(
    [string]$BaseUrl = "https://lumen-gateway-64076350717.us-central1.run.app",
    [string]$Path = "/chat",
    [string]$Message = "Explain AI concepts in a concise style",
    [int]$TimeoutSec = 20
)

function Invoke-Chat {
    param(
        [string]$url,
        [string]$msg
    )
    $body = @{ message = $msg } | ConvertTo-Json -Depth 5
    $headers = @{ "Content-Type" = "application/json" }
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $resp = Invoke-WebRequest -Uri $url -Method POST -Headers $headers -Body $body -TimeoutSec $TimeoutSec -UseBasicParsing
    $sw.Stop()
    [PSCustomObject]@{
        StatusCode   = $resp.StatusCode
        Milliseconds = $sw.ElapsedMilliseconds
        Content      = $resp.Content
    }
}

try {
    $endpoint = $BaseUrl.TrimEnd('/') + $Path
    Write-Host "\n=== Cache Hit Probe: $endpoint ===" -ForegroundColor Cyan
    Write-Host "Message: '$Message'" -ForegroundColor Gray

    Write-Host "\n[1/2] First request (expected MISS) ..." -ForegroundColor Yellow
    $r1 = Invoke-Chat -url $endpoint -msg $Message
    Write-Host (" -> {0} {1}ms" -f $r1.StatusCode, $r1.Milliseconds) -ForegroundColor White

    Start-Sleep -Milliseconds 250

    Write-Host "\n[2/2] Second request (expected HIT) ..." -ForegroundColor Yellow
    $r2 = Invoke-Chat -url $endpoint -msg $Message
    Write-Host (" -> {0} {1}ms" -f $r2.StatusCode, $r2.Milliseconds) -ForegroundColor White

    $faster = ($r2.Milliseconds -lt ($r1.Milliseconds * 0.5))
    Write-Host "\nSummary:" -ForegroundColor Green
    Write-Host ("  First:  {0}ms" -f $r1.Milliseconds)
    Write-Host ("  Second: {0}ms" -f $r2.Milliseconds)
    if ($faster) {
        Write-Host "  Likely HIT on second call (>=50% faster)." -ForegroundColor Green
    }
    else {
        Write-Host "  No strong evidence of HIT from latency alone." -ForegroundColor DarkYellow
    }

}
catch {
    Write-Host "Error during probe: $_" -ForegroundColor Red
    exit 1
}

Write-Host "\nTip: Run /cache/stats to confirm key count increase." -ForegroundColor Cyan
