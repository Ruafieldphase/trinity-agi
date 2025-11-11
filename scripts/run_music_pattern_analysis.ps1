<#
.SYNOPSIS
    Run Reaper Music Pattern Analysis

.DESCRIPTION
    Analyzes music library and extracts patterns for AGI rhythm system

.PARAMETER MusicDir
    Directory containing WAV files (default: C:\workspace\agi\music)

.PARAMETER OutputJson
    Output JSON file path (default: outputs/music_pattern_analysis.json)

.PARAMETER OpenResults
    Open results file after analysis
#>

param(
    [string]$MusicDir = "C:\workspace\agi\music",
    [string]$OutputJson = "$PSScriptRoot\..\outputs\music_pattern_analysis.json",
    [switch]$OpenResults
)

$ErrorActionPreference = "Continue"

# Find Python
$pythonExe = $null
$venvPaths = @(
    "$PSScriptRoot\..\fdo_agi_repo\.venv\Scripts\python.exe",
    "$PSScriptRoot\..\LLM_Unified\.venv\Scripts\python.exe"
)

foreach ($path in $venvPaths) {
    if (Test-Path $path) {
        $pythonExe = $path
        break
    }
}

if (-not $pythonExe) {
    $pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
}

if (-not $pythonExe) {
    Write-Host "❌ Python not found. Run setup_music_analyzer.ps1 first" -ForegroundColor Red
    exit 1
}

# Check if music directory exists
if (-not (Test-Path $MusicDir)) {
    Write-Host "❌ Music directory not found: $MusicDir" -ForegroundColor Red
    exit 1
}

# Count WAV files
$wavCount = (Get-ChildItem $MusicDir -Filter "*.wav" -ErrorAction SilentlyContinue).Count

if ($wavCount -eq 0) {
    Write-Host "❌ No WAV files found in: $MusicDir" -ForegroundColor Red
    Write-Host "   Please ensure music files are in WAV format" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n🎵 Found $wavCount WAV files" -ForegroundColor Green

# Run analysis
$analyzerScript = "$PSScriptRoot\reaper_music_pattern_analyzer.py"

if (-not (Test-Path $analyzerScript)) {
    Write-Host "❌ Analyzer script not found: $analyzerScript" -ForegroundColor Red
    exit 1
}

Write-Host "`n🎛️ Starting music pattern analysis..." -ForegroundColor Cyan
Write-Host "   This may take several minutes..." -ForegroundColor DarkGray
Write-Host ""

& $pythonExe $analyzerScript $MusicDir $OutputJson

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✨ Analysis complete!" -ForegroundColor Green
    
    if (Test-Path $OutputJson) {
        $jsonSize = (Get-Item $OutputJson).Length
        Write-Host "   Results: $OutputJson ($([math]::Round($jsonSize/1KB, 2)) KB)" -ForegroundColor Cyan
        
        # Quick summary
        try {
            $results = Get-Content $OutputJson -Raw | ConvertFrom-Json
            $total = $results.total_files
            $successful = ($results.analyses | Where-Object { -not $_.error }).Count
            
            Write-Host "`n📊 Quick Summary:" -ForegroundColor Cyan
            Write-Host "   Total files: $total" -ForegroundColor White
            Write-Host "   Successful: $successful" -ForegroundColor Green
            Write-Host "   Failed: $($total - $successful)" -ForegroundColor Yellow
            
            # AGI state distribution
            $stateGroups = $results.analyses | 
            Where-Object { $_.agi_mapping } | 
            Group-Object -Property { $_.agi_mapping.primary_state }
            
            Write-Host "`n🌊 AGI Rhythm State Distribution:" -ForegroundColor Cyan
            foreach ($group in $stateGroups) {
                Write-Host "   $($group.Name): $($group.Count) files" -ForegroundColor White
            }
        }
        catch {
            Write-Host "   (Summary parsing error, but file exists)" -ForegroundColor DarkGray
        }
        
        if ($OpenResults) {
            Write-Host "`n📂 Opening results..." -ForegroundColor Cyan
            code $OutputJson
        }
    }
}
else {
    Write-Host "`n❌ Analysis failed" -ForegroundColor Red
    Write-Host "   Check if librosa is installed (run setup_music_analyzer.ps1)" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
