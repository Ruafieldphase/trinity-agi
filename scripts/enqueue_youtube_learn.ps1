param(
    [Parameter(Mandatory = $true)][string]$Url,
    [string]$Server = 'http://127.0.0.1:8091',
    [switch]$EnableOcr,
    [int]$MaxFrames = 3,
    [double]$FrameInterval = 30.0,
    [int]$ClipSeconds = 10
)

$ErrorActionPreference = 'Stop'

$body = @{
    type = 'youtube_learn'
    data = @{
        url            = $Url
        enable_ocr     = [bool]$EnableOcr
        max_frames     = $MaxFrames
        frame_interval = $FrameInterval
        clip_seconds   = $ClipSeconds
    }
}

$uri = "$Server/api/tasks/create"
$payload = $body | ConvertTo-Json -Depth 10

try {
    $resp = Invoke-RestMethod -Method Post -Uri $uri -ContentType 'application/json' -Body $payload -TimeoutSec 15
    Write-Host "Task created: $($resp.task_id) at position $($resp.queue_position)" -ForegroundColor Green
}
catch {
    Write-Host "Failed to enqueue task: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails) { Write-Host $_.ErrorDetails -ForegroundColor Yellow }
    exit 1
}