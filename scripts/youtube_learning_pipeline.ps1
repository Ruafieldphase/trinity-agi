# YouTube Learning Pipeline - PowerShell Wrapper
param(
    [Parameter(Mandatory=$true)]
    [string]$Url,
    [int]$ClipSeconds = 30,
    [int]$MaxFrames = 5,
    [int]$FrameInterval = 30,
    [switch]$EnableOcr,
    [switch]$OpenReport
)

$ErrorActionPreference = "Stop"

Write-Host "`nYouTube Learning Pipeline" -ForegroundColor Green
Write-Host "URL: $Url" -ForegroundColor White

# Step 1: Enqueue task
Write-Host "`nStep 1: Enqueueing YouTube learn task..." -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$enqueueScript = Join-Path $scriptDir "enqueue_youtube_learn.ps1"

$enqueueArgs = @(
    "-Url", $Url,
    "-ClipSeconds", $ClipSeconds,
    "-MaxFrames", $MaxFrames,
    "-FrameInterval", $FrameInterval
)

if ($EnableOcr) {
    $enqueueArgs += "-EnableOcr"
}

& $enqueueScript @enqueueArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to enqueue task" -ForegroundColor Red
    exit 1
}

Write-Host "Task enqueued" -ForegroundColor Green

# Step 2: Wait
Write-Host "`nStep 2: Waiting for RPA Worker..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# Step 3: Check results
Write-Host "`nStep 3: Checking results..." -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8091/api/results" -TimeoutSec 5
    
    if ($response.results -and $response.results.Count -gt 0) {
        $latest = $response.results[0]
        Write-Host "Latest result:" -ForegroundColor Green
        Write-Host "  Task ID: $($latest.task_id)" -ForegroundColor White
        Write-Host "  Status: $($latest.status)" -ForegroundColor White
        
        if ($latest.status -eq "success") {
            $result = $latest.result
            if ($result.json_path) {
                Write-Host "  JSON: $($result.json_path)" -ForegroundColor Cyan
                if ($OpenReport) {
                    code $result.json_path
                }
            }
            if ($result.md_path) {
                Write-Host "  Markdown: $($result.md_path)" -ForegroundColor Cyan
                if ($OpenReport) {
                    code $result.md_path
                }
            }
            Write-Host "`nSuccess!" -ForegroundColor Green
        }
    }
    else {
        Write-Host "No results yet" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "Could not fetch results: $_" -ForegroundColor Red
}
