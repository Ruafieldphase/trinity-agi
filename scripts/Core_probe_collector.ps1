# Core Probe Collector: run a lightweight health probe and append JSONL log
[CmdletBinding()]
param(
    [string]$OutPath = '',
    [int]$TimeoutSec = 8,
    [int]$Attempts = 3,
    [int]$BackoffMs = 300,
    [switch]$WriteLatest,
    [string]$Tag = '',
    [string]$Url = '',
    [ValidateSet('GET', 'POST')][string]$Method = 'POST',
    [string]$Message = 'ping',
    [hashtable]$Headers = @{}
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
    $OutPath = (Join-Path $workspace 'outputs/core_probe_log.jsonl')
}

# Ensure UTF-8 console/output
try { chcp 65001 > $null 2> $null } catch {}
try {
    [Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false, $false)
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false, $false)
    $global:OutputEncoding = New-Object System.Text.UTF8Encoding($false, $false)
}
catch {}

# Ensure output directory
$dir = Split-Path -Parent $OutPath
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }

# Resolve gateway URL (priority: -Url > env > default)
$resolved = if (-not [string]::IsNullOrWhiteSpace($Url)) { $Url } elseif (-not [string]::IsNullOrWhiteSpace($env:CORE_GATEWAY_URL)) { $env:CORE_GATEWAY_URL } else { 'https://Core-gateway-x4qvsargwa-uc.a.run.app/chat' }
if ($resolved -notmatch '^https?://') { $resolved = 'https://{0}' -f $resolved }
$uri = $resolved

$ok = $false
$status = $null
$respText = $null
$errMsg = $null
$ms = 0
$apiSuccess = $null

# Retry loop with simple backoff
for ($attempt = 1; $attempt -le [Math]::Max(1, $Attempts); $attempt++) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        # Prepare request
        $defaultHeaders = @{ 'Accept' = 'application/json'; 'User-Agent' = 'CoreProbeCollector/1.0' }
        foreach ($k in $Headers.Keys) { $defaultHeaders[$k] = $Headers[$k] }

        if ($Method -eq 'GET') {
            $reqUri = $uri
            if (-not [string]::IsNullOrWhiteSpace($Message)) {
                if ($uri -match '\?') { $join = '&' } else { $join = '?' }
                $encoded = [System.Uri]::EscapeDataString([string]$Message)
                $reqUri = "{0}{1}message={2}" -f $uri, $join, $encoded
            }
            $resp = Invoke-WebRequest -Uri $reqUri -Method Get -Headers $defaultHeaders -TimeoutSec $TimeoutSec -ErrorAction Stop
        }
        else {
            $payload = @{ message = $Message } | ConvertTo-Json -Depth 3
            $resp = Invoke-WebRequest -Uri $uri -Method Post -Headers $defaultHeaders -Body $payload -ContentType 'application/json' -TimeoutSec $TimeoutSec -ErrorAction Stop
        }
        $sw.Stop()
        $ms = [int]$sw.Elapsed.TotalMilliseconds
        $status = $resp.StatusCode

        # Force UTF-8 decoding regardless of missing/incorrect charset headers
        try {
            if ($resp.RawContentStream) {
                $mem = New-Object System.IO.MemoryStream
                $resp.RawContentStream.Seek(0, [System.IO.SeekOrigin]::Begin) | Out-Null
                $resp.RawContentStream.CopyTo($mem)
                $bytes = $mem.ToArray()
                $utf8 = New-Object System.Text.UTF8Encoding($false, $false)
                $respText = $utf8.GetString($bytes)
            }
            elseif ($resp.Content) {
                # Fallback: use Content string
                $respText = [string]$resp.Content
            }
        }
        catch {
            try { $respText = [string]$resp.Content } catch {}
        }

        $ok = ($status -ge 200 -and $status -lt 300)

        # Try to parse API JSON and surface a top-level success flag if present
        try {
            if ($respText -and ($resp.Headers['Content-Type'] -like '*json*' -or $respText.Trim().StartsWith('{'))) {
                $jsonObj = $respText | ConvertFrom-Json -ErrorAction Stop
                if ($null -ne $jsonObj) {
                    $hasProp = ($jsonObj.PSObject.Properties.Name -contains 'success')
                    if ($hasProp) {
                        $val = $jsonObj.success
                        if ($val -is [bool]) { $apiSuccess = [bool]$val }
                        elseif ($val -is [int] -or $val -is [long]) { $apiSuccess = ([int]$val -ne 0) }
                        else {
                            $s = ("{0}" -f $val).Trim().ToLowerInvariant()
                            if ($s -in @('true','1','ok','yes','success')) { $apiSuccess = $true }
                            elseif ($s -in @('false','0','no','fail','failed','error')) { $apiSuccess = $false }
                        }
                    }
                }
            }
        }
        catch { }
        if ($ok) { break }
    }
    catch {
        $sw.Stop()
        $ms = [int]$sw.Elapsed.TotalMilliseconds
        $err = $_
        $ok = $false
        try {
            if ($_.Exception.Response) {
                $status = [int]$_.Exception.Response.StatusCode
                $stream = $_.Exception.Response.GetResponseStream()
                if ($stream) {
                    # Explicitly decode as UTF-8 (no BOM) for consistency
                    $sr = New-Object System.IO.StreamReader($stream, (New-Object System.Text.UTF8Encoding($false, $false)), $true)
                    $respText = $sr.ReadToEnd()
                    $sr.Close()
                }
            }
        }
        catch {}
        $errMsg = ($err.Exception.Message)
    }

    if (-not $ok -and $attempt -lt $Attempts) {
        Start-Sleep -Milliseconds ([int]([Math]::Max(0, $BackoffMs) * [Math]::Pow(1.5, ($attempt - 1))))
    }
}
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
    method  = $Method
    api_success = $apiSuccess
    preview = $preview
    error   = $errMsg
    tag     = $Tag
}

# Append JSONL (single line for proper JSONL format)
$line = ($rec | ConvertTo-Json -Depth 5 -Compress)
# Ensure UTF-8 (without BOM if possible) write for JSONL stability on PS 5.1
try {
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false, $false)
    [System.IO.File]::AppendAllText($OutPath, $line + [Environment]::NewLine, $utf8NoBom)
}
catch {
    # Fallback to Add-Content UTF8
    Add-Content -Path $OutPath -Value $line -Encoding UTF8
}

# Also write a one-liner for console
if ($ok) {
    Write-Host ("PASS  {0}ms  {1}" -f $ms, $uri) -ForegroundColor Green
}
else {
    Write-Host ("FAIL  {0}ms  status={1}  {2}" -f $ms, $status, $uri) -ForegroundColor Yellow
    if ($errMsg) { Write-Host ("Reason: {0}" -f $errMsg) -ForegroundColor DarkYellow }
}

# Optionally write latest ASCII digest and JSON
if ($WriteLatest) {
    try {
        $latestJson = Join-Path $workspace 'outputs/core_probe_latest.json'
        $latestMd = Join-Path $workspace 'outputs/core_probe_latest.md'

        $utf8NoBom = New-Object System.Text.UTF8Encoding($false, $false)
        $jsonBody = ($rec | ConvertTo-Json -Depth 6)
        [System.IO.File]::WriteAllText($latestJson, $jsonBody, $utf8NoBom)

        $safePreview = if ($preview) { ($preview -replace "\r|\n", " ") } else { '' }
        $md = @()
        $md += '[Core PROBE DIGEST - ASCII SAFE]'
        $md += ''
        $md += ('- When (UTC): {0}' -f $rec.ts)
        $md += ('- URL: {0}' -f $uri)
        $md += ('- OK: {0}  status: {1}  {2}ms' -f $ok, $status, $ms)
        $md += ('- Method: {0}' -f $Method)
        if ($null -ne $apiSuccess) { $md += ('- API success: {0}' -f $apiSuccess) }
        if ($Tag) { $md += ('- Tag: {0}' -f $Tag) }
        if ($safePreview) { $md += ('- Preview: {0}' -f ($safePreview.Substring(0, [Math]::Min(140, $safePreview.Length)))) }
        $md += ''
        $md += '---'
        $md += ''
        $md += 'Append-only log: outputs/core_probe_log.jsonl'

        [System.IO.File]::WriteAllText($latestMd, ($md -join "`r`n"), $utf8NoBom)
    }
    catch {
        Write-Warning "Could not write latest artifacts: $($_.Exception.Message)"
    }
}

exit ($(if ($ok) { 0 } else { 1 }))