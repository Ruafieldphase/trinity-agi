param(
    [Parameter(Mandatory = $false)][string]$File,
    [Parameter(Mandatory = $false)][string]$OutFile,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'

function Get-LatestJsonPath {
    $scriptDir = $PSScriptRoot
    if (-not $scriptDir -or [string]::IsNullOrWhiteSpace($scriptDir)) {
        $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    }
    if (-not $scriptDir -or [string]::IsNullOrWhiteSpace($scriptDir)) {
        $scriptDir = (Get-Location).Path
    }
    $rootDir = Split-Path -Parent $scriptDir
    $folder = Join-Path $rootDir 'outputs/youtube_learner'
    if (-not (Test-Path $folder)) { throw "Folder not found: $folder" }
    $files = Get-ChildItem -Path $folder -Filter '*.json' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    if (-not $files -or $files.Count -eq 0) { throw "No JSON files found in: $folder" }
    return $files[0].FullName
}

if (-not $File -or [string]::IsNullOrWhiteSpace($File)) {
    $File = Get-LatestJsonPath
}
if (-not $File -or [string]::IsNullOrWhiteSpace($File)) { throw "Could not resolve latest JSON file path." }
if (-not (Test-Path $File)) { throw "JSON file not found: $File" }

# Read and parse JSON
$content = Get-Content -Raw -Path $File | ConvertFrom-Json

# Extract fields with fallbacks
function Get-FirstNonNull([object[]]$values) {
    foreach ($v in $values) { if ($null -ne $v -and $v -ne '') { return $v } }
    return $null
}

$videoId = Get-FirstNonNull @($content.video_id, $content.data.video_id)
$title = Get-FirstNonNull @($content.title, $content.data.title, 'YouTube Analysis')
$duration = Get-FirstNonNull @($content.duration, $content.data.duration)
$frames = Get-FirstNonNull @($content.frames_count, $content.frames, $content.data.frames)
$subtitles = Get-FirstNonNull @($content.subtitles_count, $content.subtitles, $content.data.subtitles)
$keywords = Get-FirstNonNull @($content.keywords, $content.data.keywords)
$summary = Get-FirstNonNull @($content.summary, $content.data.summary)
$analyzed = Get-FirstNonNull @($content.analyzed_at, $content.data.analyzed_at)

# Build Markdown
$md = @()
$md += "# YouTube Analysis"
if ($title) { $md += "\n**Title:** $title" }
if ($videoId) {
    $thumb = "https://img.youtube.com/vi/$videoId/hqdefault.jpg"
    $yt = "https://www.youtube.com/watch?v=$videoId"
    $md += "\n\n[![$title]($thumb)]($yt)"
}
if ($videoId) { $md += "\n**Video ID:** $videoId" }
if ($videoId) { $md += "\n**Link:** https://www.youtube.com/watch?v=$videoId" }
if ($duration) { $md += "\n**Duration:** ${duration} sec" }
if ($null -ne $frames) { $md += "\n**Frames:** $frames" }
if ($null -ne $subtitles) { $md += "\n**Subtitles:** $subtitles" }
if ($keywords) {
    if ($keywords -is [System.Array]) {
        $kw = $keywords -join ', '
        $md += "\n**Keywords:** $kw"
    }
    else {
        $md += "\n**Keywords:** $keywords"
    }
}
if ($analyzed) { $md += "\n**Analyzed At:** $analyzed" }
if ($File) { $md += "\n**Source JSON:** $File" }
${now} = Get-Date -Format o
$md += "\n**Generated At:** ${now}"
if ($summary) { $md += "\n\n## Summary\n$summary" }

# Output path
if (-not $OutFile -or [string]::IsNullOrWhiteSpace($OutFile)) {
    $OutFile = [System.IO.Path]::ChangeExtension($File, '.md')
}

$mdText = $md -join "\n"
Set-Content -Path $OutFile -Value $mdText -Encoding UTF8
Write-Host "Markdown written: $OutFile" -ForegroundColor Green

# Optionally open in VS Code
if (-not $NoOpen) {
    try {
        Start-Process code $OutFile | Out-Null
    }
    catch {
        Write-Host "Note: Unable to auto-open VS Code: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}
