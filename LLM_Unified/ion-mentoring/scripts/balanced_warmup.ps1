param(
    [Parameter(Mandatory = $false)]
    [string]$CanaryUrl = 'https://ion-api-canary-x4qvsargwa-uc.a.run.app',
    [Parameter(Mandatory = $false)]
    [string]$LegacyUrl = 'https://ion-api-x4qvsargwa-uc.a.run.app',
    [Parameter(Mandatory = $false)]
    [int]$CountPerSide = 25,
    [Parameter(Mandatory = $false)]
    [int]$Concurrency = 1
)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function Invoke-PostChat {
    param(
        [string]$BaseUrl,
        [string]$Message
    )
    try {
        $body = @{ message = $Message } | ConvertTo-Json -Depth 5
        Invoke-RestMethod -Uri ("{0}/chat" -f $BaseUrl.TrimEnd('/')) -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 30 -ErrorAction Stop | Out-Null
        return @{ ok = $true; code = 200 }
    }
    catch {
        $code = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { -1 }
        return @{ ok = $false; code = $code; err = $_.Exception.Message }
    }
}

Write-Host ("[balanced_warmup] Starting warm-up: Canary={0} Legacy={1} CountPerSide={2}" -f $CanaryUrl, $LegacyUrl, $CountPerSide) -ForegroundColor Cyan

$messages = @(
    'Warmup message 1', 'Warmup message 2', 'Performance check', 'Quick ping', 'Short payload'
)

$canaryOk = 0; $canaryErr = 0
$legacyOk = 0; $legacyErr = 0

for ($i = 1; $i -le $CountPerSide; $i++) {
    $msg = $messages[($i % $messages.Count)]
    $r1 = Invoke-PostChat -BaseUrl $CanaryUrl -Message $msg
    if ($r1.ok) { $canaryOk++ } else { $canaryErr++ }

    $r2 = Invoke-PostChat -BaseUrl $LegacyUrl -Message $msg
    if ($r2.ok) { $legacyOk++ } else { $legacyErr++ }

    if (($i % 5) -eq 0) { Start-Sleep -Milliseconds 200 }
}

Write-Host ("[balanced_warmup] Canary: OK={0} ERR={1} | Legacy: OK={2} ERR={3}" -f $canaryOk, $canaryErr, $legacyOk, $legacyErr) -ForegroundColor Green

if ($canaryOk -eq 0 -and $legacyOk -eq 0) { exit 2 }
exit 0
