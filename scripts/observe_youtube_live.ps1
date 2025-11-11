param(
    [Parameter(Mandatory = $true)][string]$Url,
    [string]$Server = 'http://127.0.0.1:8091',
    [int]$IntervalSeconds = 60,
    [int]$ClipSeconds = 10,
    [int]$MaxFrames = 3,
    [double]$FrameInterval = 30.0,
    [switch]$EnableOcr,
    [int]$DurationSeconds = 0, # 0 = run indefinitely
    [string]$OutDir = "${PSScriptRoot}\..\outputs\telemetry"
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$OutDir = [IO.Path]::GetFullPath($OutDir)
if (-not (Test-Path -LiteralPath $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
}

$pidFile = Join-Path $OutDir 'youtube_live_observer.pid'
$statusFile = Join-Path $OutDir 'youtube_live_observer_status.json'

# Write PID
try { Set-Content -LiteralPath $pidFile -Value $PID -Encoding ascii -Force } catch {}

$start = Get-Date
$deadline = if ($DurationSeconds -gt 0) { $start.AddSeconds($DurationSeconds) } else { [datetime]::MaxValue }

Write-Host "[yt-observer] Starting live observer. Interval=${IntervalSeconds}s Clip=${ClipSeconds}s Server=$Server" -ForegroundColor Cyan

function Write-Status([string]$phase, [string]$message) {
    $obj = [ordered]@{
        ts_utc   = (Get-Date).ToUniversalTime().ToString('o')
        phase    = $phase
        message  = $message
        url      = $Url
        interval = $IntervalSeconds
        server   = $Server
    }
    try { $obj | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $statusFile -Encoding utf8 -Force } catch {}
}

while ([datetime]::UtcNow -lt $deadline) {
    Write-Status 'enqueue' 'Submitting clip task'
    try {
        $argList = @('-Url', $Url, '-Server', $Server, '-ClipSeconds', $ClipSeconds, '-MaxFrames', $MaxFrames, '-FrameInterval', $FrameInterval)
        if ($EnableOcr) { $argList += '-EnableOcr' }
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'enqueue_youtube_learn.ps1') @argList | Out-Host
    }
    catch {
        Write-Host "[yt-observer] Enqueue failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }

    Start-Sleep -Seconds $IntervalSeconds
}

Write-Status 'stopped' ('DurationSeconds=' + [int]((Get-Date) - $start).TotalSeconds)
try { Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue } catch {}
Write-Host "[yt-observer] Stopped." -ForegroundColor Green
