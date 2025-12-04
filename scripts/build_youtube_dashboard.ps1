param(
    [Parameter(Mandatory = $false)][string]$Folder,
    [Parameter(Mandatory = $false)][string]$OutFile,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'

# Resolve default folder
if (-not $Folder -or [string]::IsNullOrWhiteSpace($Folder)) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
    if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
    $rootDir = Split-Path -Parent $scriptDir
    $Folder = Join-Path $rootDir 'outputs/youtube_learner'
}

if (-not (Test-Path $Folder)) {
    throw "Folder not found: $Folder"
}

# Read all JSON files
$jsonFiles = Get-ChildItem -Path $Folder -Filter '*_analysis.json' -File -ErrorAction SilentlyContinue |
Sort-Object LastWriteTime -Descending

if ($jsonFiles.Count -eq 0) {
    Write-Host "No analysis files found in: $Folder" -ForegroundColor Yellow
    exit 0
}

Write-Host "Found $($jsonFiles.Count) analysis file(s)" -ForegroundColor Cyan

# Collect data
$videos = @()
$allKeywords = @()

foreach ($jsonFile in $jsonFiles) {
    try {
        $data = Get-Content -Raw -Path $jsonFile.FullName | ConvertFrom-Json
        
        # Extract video ID from filename
        $videoId = $jsonFile.BaseName -replace '_analysis$', ''
        
        # Get title
        $title = $data.title
        if (-not $title) { $title = $data.data.title }
        if (-not $title) { $title = "Untitled Video" }
        
        # Get duration
        $duration = $data.duration
        if (-not $duration) { $duration = $data.data.duration }
        if (-not $duration) { $duration = 0 }
        
        # Ensure duration is a number
        try {
            $duration = [int]$duration
        }
        catch {
            $duration = 0
        }
        
        # Get summary
        $summary = $data.summary
        if (-not $summary) { $summary = $data.data.summary }
        if (-not $summary) { $summary = "" }
        if ($summary.Length -gt 200) {
            $summary = $summary.Substring(0, 200) + "..."
        }
        
        # Get keywords
        $keywords = $data.keywords
        if (-not $keywords) { $keywords = $data.data.keywords }
        if (-not $keywords) { $keywords = @() }
        if ($keywords -is [System.Array]) {
            $keywords = $keywords | Select-Object -First 5
        }
        else {
            $keywords = @($keywords)
        }
        
        # Collect for stats
        $allKeywords += $keywords
        
        # Determine emoji
        $emoji = '🟡'  # default medium
        if ($duration -lt 300) {
            $emoji = '🔵'  # short
        }
        elseif ($duration -gt 1800) {
            $emoji = '🔴'  # long
        }
        
        # Check if markdown exists
        $mdPath = $jsonFile.FullName -replace '\.json$', '.md'
        $hasMarkdown = Test-Path $mdPath
        
        # Get analyzed timestamp
        $analyzedAt = $jsonFile.LastWriteTime.ToString('yyyy-MM-ddTHH:mm:ss')
        
        $videos += [PSCustomObject]@{
            id          = $videoId
            title       = $title
            duration    = [int]$duration
            emoji       = $emoji
            summary     = $summary
            keywords    = $keywords
            hasMarkdown = $hasMarkdown
            analyzedAt  = $analyzedAt
            jsonPath    = $jsonFile.FullName
            mdPath      = $mdPath
        }
    }
    catch {
        Write-Host "Error processing $($jsonFile.Name): $($_.Exception.Message)" -ForegroundColor Red
    }
}

if ($videos.Count -eq 0) {
    Write-Host "No valid video data found" -ForegroundColor Yellow
    exit 0
}

# Calculate stats
$totalCount = $videos.Count
$withMarkdown = ($videos | Where-Object { $_.hasMarkdown }).Count
$avgDuration = [int](($videos | Measure-Object -Property duration -Average).Average)
$shortVideos = ($videos | Where-Object { $_.duration -lt 300 }).Count
$mediumVideos = ($videos | Where-Object { $_.duration -ge 300 -and $_.duration -lt 1800 }).Count
$longVideos = ($videos | Where-Object { $_.duration -ge 1800 }).Count

# Top keywords
$topKeywords = $allKeywords | Group-Object | Sort-Object Count -Descending | Select-Object -First 5

# Output JavaScript data file
$jsData = @{
    stats       = @{
        total        = $totalCount
        withMarkdown = $withMarkdown
        avgDuration  = $avgDuration
        distribution = @{
            short  = $shortVideos
            medium = $mediumVideos
            long   = $longVideos
        }
        topKeywords  = $topKeywords | ForEach-Object { @{ keyword = $_.Name; count = $_.Count } }
    }
    videos      = $videos
    generatedAt = (Get-Date -Format o)
}

$jsContent = "const youtubeData = " + ($jsData | ConvertTo-Json -Depth 10 -Compress) + ";"

# Determine output file
if (-not $OutFile) {
    $OutFile = Join-Path (Split-Path -Parent $Folder) 'youtube_data.js'
}

Set-Content -Path $OutFile -Value $jsContent -Encoding UTF8

Write-Host "Data file written: $OutFile" -ForegroundColor Green
Write-Host "  Videos: $totalCount" -ForegroundColor Cyan
Write-Host "  With MD: $withMarkdown / $totalCount" -ForegroundColor Cyan
Write-Host "  Avg Duration: ${avgDuration}s (~$([int]($avgDuration/60))m)" -ForegroundColor Cyan

# Copy HTML template if not exists
$htmlPath = Join-Path (Split-Path -Parent $Folder) 'youtube_dashboard.html'
if (-not (Test-Path $htmlPath)) {
    Write-Host "HTML template not found at: $htmlPath" -ForegroundColor Yellow
}

if (-not $NoOpen -and (Test-Path $htmlPath)) {
    Write-Host "Opening dashboard..." -ForegroundColor Green
    Start-Process $htmlPath
}
