param(
    [string]$Url = $env:CORE_GATEWAY_URL,
    [int]$TimeoutSec = 10
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if (-not $Url -or $Url.Trim() -eq '') {
    # fallback to known default if env not set
    $Url = 'https://Core-gateway-x4qvsargwa-uc.a.run.app/chat'
}

$payload = @{ message = 'ping' } | ConvertTo-Json -Compress
$payloadBytes = [System.Text.Encoding]::UTF8.GetBytes($payload)

try {
    $webRequest = [System.Net.HttpWebRequest]::Create($Url)
    $webRequest.Method = 'POST'
    $webRequest.ContentType = 'application/json; charset=utf-8'
    $webRequest.Timeout = $TimeoutSec * 1000
    $webRequest.ContentLength = $payloadBytes.Length
    
    $stream = $webRequest.GetRequestStream()
    $stream.Write($payloadBytes, 0, $payloadBytes.Length)
    $stream.Close()
    
    $webResponse = $webRequest.GetResponse()
    $responseStream = $webResponse.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($responseStream, [System.Text.Encoding]::UTF8)
    $responseText = $reader.ReadToEnd()
    $reader.Close()
    $responseStream.Close()
    $webResponse.Close()
    
    $response = $responseText | ConvertFrom-Json
    
    Write-Host "Core PROBE: PASS" -ForegroundColor Green
    if ($response) {
        $preview = ($response | ConvertTo-Json -Depth 5 -Compress:$false)
        if ($preview.Length -gt 500) { $preview = $preview.Substring(0, 500) + '...' }
        Write-Output $preview
    }
    exit 0
}
catch {
    Write-Host "Core PROBE: FAIL" -ForegroundColor Red
    Write-Error $_
    exit 1
}