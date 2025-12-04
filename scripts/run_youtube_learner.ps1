param(
    [string]$Url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    [int]$MaxFrames = 1,
    [double]$FrameInterval = 30.0,
    [switch]$EnableOcr,
    [string]$LogPath,
    [switch]$SkipIfToday
)

$ErrorActionPreference = 'Stop'
Write-Host "[YouTubeLearner] Running..." -ForegroundColor Cyan

# Ensure PYTHONPATH includes repo roots
$env:PYTHONPATH = "C:\workspace\agi;C:\workspace\agi\fdo_agi_repo"

$rootDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$outDir = Join-Path (Join-Path $rootDir 'outputs') 'youtube_learner'

# Optional: skip if already ran today for the same video id
if ($SkipIfToday) {
    try {
        $vid = $null
        if ($Url -match 'v=([^&#]+)') { $vid = $Matches[1] }
        elseif ($Url -match 'youtu\.be/([^?&#/]+)') { $vid = $Matches[1] }
        if ($vid) {
            $outFile = Join-Path $outDir ("{0}_analysis.json" -f $vid)
            if (Test-Path $outFile) {
                $last = (Get-Item $outFile).LastWriteTime.Date
                if ($last -eq (Get-Date).Date) {
                    Write-Host "[YouTubeLearner] Skip: already ran today for video $vid" -ForegroundColor Yellow
                    exit 0
                }
            }
        }
    } catch {
        Write-Verbose "SkipIfToday check failed: $($_.Exception.Message)"
    }
}

$argsList = @(
    '-X','utf8','-m','rpa.youtube_learner',
    '--url', $Url,
    '--max-frames', $MaxFrames,
    '--frame-interval', $FrameInterval
)
if ($EnableOcr) { $argsList += '--enable-ocr' }

& py -3 @argsList

if ($LASTEXITCODE -ne 0) {
    throw "YouTubeLearner run failed with exit code $LASTEXITCODE"
}

Write-Host "[YouTubeLearner] Done." -ForegroundColor Green

# Optional: append a compact summary to a JSONL log
if ($LogPath) {
    try {
        $rootDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
        $outDir = Join-Path (Join-Path $rootDir 'outputs') 'youtube_learner'
        $latest = Get-ChildItem -Path $outDir -Filter '*_analysis.json' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($latest) {
            $json = Get-Content -Path $latest.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
            $entry = [PSCustomObject]@{
                ts = (Get-Date).ToString('s')
                url = $Url
                video_id = $json.video_id
                title = $json.title
                subtitles = $json.subtitles_count
                frames = $json.frames_count
                summary = $json.summary
                output_file = $latest.FullName
            }
            $line = $entry | ConvertTo-Json -Compress
            $logDir = Split-Path -Path $LogPath -Parent
            if ($logDir -and -not (Test-Path $logDir)) { New-Item -Path $logDir -ItemType Directory -Force | Out-Null }
            Add-Content -Path $LogPath -Value $line -Encoding UTF8
            Write-Host "[YouTubeLearner] Logged summary to $LogPath"
            # Generate Markdown from JSON
            try {
                & (Join-Path $PSScriptRoot 'generate_youtube_md_from_json.ps1') -File $latest.FullName | Out-Null
            } catch { Write-Verbose "Failed to generate MD: $($_.Exception.Message)" }
        } else {
            Write-Warning "[YouTubeLearner] No analysis JSON found to log."
        }
    } catch {
        Write-Warning "[YouTubeLearner] Failed to append log: $($_.Exception.Message)"
    }
}

# Refresh INDEX.md after run
try {
    & (Join-Path $PSScriptRoot 'generate_youtube_index.ps1') | Out-Null
    Write-Host "[YouTubeLearner] INDEX.md refreshed"
} catch { Write-Verbose "Failed to refresh index: $($_.Exception.Message)" }
