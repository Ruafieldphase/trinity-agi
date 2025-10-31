param(
    [Parameter(Mandatory = $false)][string]$Folder,
    [switch]$GenerateMdIfMissing,
    [switch]$OpenFolder
)

$ErrorActionPreference = 'Stop'

# Resolve default folder robustly if not provided
if (-not $Folder -or [string]::IsNullOrWhiteSpace($Folder)) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    if (-not $scriptDir -or [string]::IsNullOrWhiteSpace($scriptDir)) {
        $scriptDir = $PSScriptRoot
    }
    if (-not $scriptDir -or [string]::IsNullOrWhiteSpace($scriptDir)) {
        $scriptDir = (Get-Location).Path
    }
    $rootDir = Split-Path -Parent $scriptDir
    $Folder = Join-Path $rootDir 'outputs/youtube_learner'
}

if (-not (Test-Path $Folder)) {
    Write-Host "No analysis folder found: $Folder" -ForegroundColor Yellow
    exit 1
}

$files = Get-ChildItem -Path $Folder -Filter '*.json' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
if (-not $files -or $files.Count -eq 0) {
    Write-Host "No analysis JSON files found in: $Folder" -ForegroundColor Yellow
    exit 1
}

$latest = $files[0].FullName
Write-Host "Opening latest analysis: $latest" -ForegroundColor Green
Start-Process code $latest

# Optionally open a sibling Markdown summary if present
try {
    $mdPath = [System.IO.Path]::ChangeExtension($latest, '.md')
    if ($mdPath -and (Test-Path $mdPath)) {
        Write-Host "Also opening summary: $mdPath" -ForegroundColor DarkGreen
        Start-Process code $mdPath
    }
    elseif ($GenerateMdIfMissing) {
        Write-Host "No MD found. Generating summary from JSON..." -ForegroundColor Yellow
        $gen = Join-Path (Split-Path -Parent $PSCommandPath) 'generate_youtube_md_from_json.ps1'
        if (-not (Test-Path $gen)) { throw "Generator not found: $gen" }
        & $gen -File $latest -OutFile $mdPath 2>&1 | Out-String | Write-Host
        if (Test-Path $mdPath) {
            Write-Host "Opening generated summary: $mdPath" -ForegroundColor DarkGreen
            Start-Process code $mdPath
        }
        else {
            Write-Host "Failed to generate MD summary." -ForegroundColor Red
        }
    }
}
catch {
    Write-Host "Note: Unable to open optional summary MD: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Optionally open the containing folder in Explorer
if ($OpenFolder) {
    try {
        Write-Host "Opening folder: $Folder" -ForegroundColor DarkCyan
        Start-Process explorer $Folder | Out-Null
    }
    catch {
        Write-Host "Note: Unable to open folder in Explorer: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}
