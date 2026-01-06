param(
    [Parameter(Mandatory = $false)][string]$Url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    [Parameter(Mandatory = $false)][string]$Server = "http://127.0.0.1:8092",
    [Parameter(Mandatory = $false)][int]$ClipSeconds = 10,
    [Parameter(Mandatory = $false)][int]$MaxFrames = 3,
    [Parameter(Mandatory = $false)][double]$FrameInterval = 30.0,
    [Parameter(Mandatory = $false)][int]$TimeoutSeconds = 90,
    [switch]$EnableOcr
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $here

function Test-Server {
    param([string]$HealthUrl)
    try {
        $null = Invoke-WebRequest -Uri $HealthUrl -TimeoutSec 2 -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

function Start-QueueServer8092 {
    $health = "$Server/api/health"
    if (Test-Server -HealthUrl $health) {
        Write-Host "Queue server already running at $Server" -ForegroundColor Green
        return
    }
    Write-Host "Starting queue server on 8092..." -ForegroundColor Yellow
    $ion = Join-Path $root 'LLM_Unified/ion-mentoring'
    $py = Join-Path $ion '.venv/Scripts/python.exe'
    $cmd = if (Test-Path $py) { "& '$py' task_queue_server.py --port 8092" } else { "python task_queue_server.py --port 8092" }
    Start-Process -WindowStyle Hidden -WorkingDirectory $ion -FilePath powershell -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $cmd | Out-Null
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while ($sw.Elapsed.TotalSeconds -lt 10) {
        Start-Sleep -Milliseconds 500
        if (Test-Server -HealthUrl $health) { Write-Host "Queue server online." -ForegroundColor Green; return }
    }
    throw "Queue server failed to start on 8092"
}

function Start-YouTubeWorker8092 {
    Write-Host "Starting YouTube worker (8092)..." -ForegroundColor Yellow
    $py = Join-Path $root 'fdo_agi_repo/.venv/Scripts/python.exe'
    $worker = Join-Path $root 'fdo_agi_repo/integrations/youtube_worker.py'
    if (-not (Test-Path $worker)) { throw "Worker not found: $worker" }
    $cmd = if (Test-Path $py) { "& '$py' '$worker' --server '$Server' --interval 0.5 --worker-name youtube-worker --log-level INFO" } else { "python '$worker' --server '$Server' --interval 0.5 --worker-name youtube-worker --log-level INFO" }
    Start-Process -WindowStyle Hidden -FilePath powershell -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $cmd | Out-Null
}

function Invoke-YouTubeEnqueue {
    Write-Host "Enqueue task: $Url" -ForegroundColor Cyan
    $enqueue = Join-Path $root 'scripts/enqueue_youtube_learn.ps1'
    if (-not (Test-Path $enqueue)) { throw "Enqueue script not found: $enqueue" }
    $params = @{ Url = $Url; Server = $Server; ClipSeconds = $ClipSeconds; MaxFrames = $MaxFrames; FrameInterval = $FrameInterval }
    if ($EnableOcr) { $params.EnableOcr = $true }
    $out = & $enqueue @params 2>&1 | Out-String
    Write-Host $out -ForegroundColor DarkGray
    $taskId = $null
    if ($out -match 'Task created:\s*([0-9a-fA-F\-]{36})') { $taskId = $Matches[1] }
    return $taskId
}

function Wait-ForResult {
    param([string]$TaskId)
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while ($sw.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
        try {
            $resp = Invoke-RestMethod -Uri "$Server/api/results" -TimeoutSec 5
            if ($null -ne $resp.results) {
                if ($TaskId) {
                    $hit = $resp.results | Where-Object { $_.task_id -eq $TaskId }
                    if ($hit) { return $hit }
                }
                else {
                    $recent = $resp.results | Select-Object -First 1
                    if ($recent) { return $recent }
                }
            }
        }
        catch {}
        Start-Sleep -Milliseconds 800
    }
    throw "No result within $TimeoutSeconds seconds"
}

try {
    Start-QueueServer8092
    Start-YouTubeWorker8092
    $taskId = Invoke-YouTubeEnqueue
    $res = Wait-ForResult -TaskId $taskId
    if ($res.success -ne $true) {
        Write-Host "Task failed:" -ForegroundColor Red
        $res | ConvertTo-Json -Depth 8 | Write-Output
        exit 1
    }
    Write-Host "Task succeeded:" -ForegroundColor Green
    $res | ConvertTo-Json -Depth 8 | Write-Output
    $outPath = $res.data.output_file
    if ($outPath) {
        $full = if ([System.IO.Path]::IsPathRooted($outPath)) { $outPath } else { Join-Path $root $outPath }
        if (Test-Path $full) { Start-Process code $full }
    }
    exit 0
}
catch {
    Write-Host $_ -ForegroundColor Red
    exit 1
}