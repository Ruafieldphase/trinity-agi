# Lumen Probe Collector: run a lightweight health probe and append JSONL log
[CmdletBinding()]
param(
    [string]$OutPath = '',
    [int]$TimeoutSec = 8
)

$ErrorActionPreference = 'Stop'

# Determine workspace root robustly
if (-not $PSScriptRoot) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
else {
    $scriptDir = $PSScriptRoot
}
$workspace = Split-Path -Parent $scriptDir

# Set default output path if not provided
if ([string]::IsNullOrWhiteSpace($OutPath)) {
    $OutPath = (Join-Path $workspace 'outputs/lumen_probe_log.jsonl')
}

# Ensure UTF-8 console/output
try { chcp 65001 > $null 2> $null } catch {}
try {
    [Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $global:OutputEncoding = New-Object System.Text.UTF8Encoding($false)
}
catch {}

# Ensure output directory
$dir = Split-Path -Parent $OutPath
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }

# Resolve gateway URL
$base = $env:LUMEN_GATEWAY_URL
if ([string]::IsNullOrWhiteSpace($base)) {
    # Use actual Cloud Run endpoint
    $base = 'https://lumen-gateway-x4qvsargwa-uc.a.run.app/chat'
}

# If base looks like a base origin, append a default path
if ($base -notmatch '^https?://') {
    $base = 'https://lumen-gateway-x4qvsargwa-uc.a.run.app/chat'
}

$uri = $base

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$ok = $false
$status = $null
$respText = $null
$errMsg = $null
try {
    # Use same payload format as quick_status.ps1
    $payload = @{ message = 'ping' } | ConvertTo-Json -Depth 3
    $resp = Invoke-WebRequest -Uri $uri -Method Post -Body $payload -ContentType 'application/json' -TimeoutSec $TimeoutSec -ErrorAction Stop
    $sw.Stop()
    $status = $resp.StatusCode
    try { $respText = $resp.Content } catch {}
    $ok = ($status -ge 200 -and $status -lt 300)
}
catch {
    $sw.Stop()
    $err = $_
    $ok = $false
    try {
        if ($_.Exception.Response) {
            $status = [int]$_.Exception.Response.StatusCode
            $sr = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $respText = $sr.ReadToEnd()
            $sr.Close()
        }
    }
    catch {}
    $errMsg = ($err.Exception.Message)
}

$ms = [int]$sw.Elapsed.TotalMilliseconds
# Truncate response preview to keep JSONL lightweight
$preview = $null
if ($respText) {
    $preview = ($respText.Substring(0, [Math]::Min(500, $respText.Length)))
}

$rec = [ordered]@{
    ts      = [DateTime]::UtcNow.ToString('o')
    ok      = $ok
    ms      = $ms
    status  = $status
    url     = $uri
    preview = $preview
    error   = $errMsg
}

# Append JSONL (single line for proper JSONL format)
$line = ($rec | ConvertTo-Json -Depth 5 -Compress)
Add-Content -Path $OutPath -Value $line -Encoding UTF8

# Also write a one-liner for console
if ($ok) {
    Write-Host ("PASS  {0}ms  {1}" -f $ms, $uri) -ForegroundColor Green
}
else {
    Write-Host ("FAIL  {0}ms  status={1}  {2}" -f $ms, $status, $uri) -ForegroundColor Yellow
    if ($errMsg) { Write-Host ("Reason: {0}" -f $errMsg) -ForegroundColor DarkYellow }
}

exit 0
