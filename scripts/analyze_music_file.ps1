#Requires -Version 5.1
<#
.SYNOPSIS
    Analyze music file for rhythm phase suitability

.DESCRIPTION
    Analyzes an audio file and determines its suitability for the current rhythm phase.

.PARAMETER AudioFile
    Path to audio file (WAV, MP3, etc.)

.PARAMETER Phase
    Target phase to check against (default: current phase)

.PARAMETER Open
    Open analysis report after generation

.EXAMPLE
    .\analyze_music_file.ps1 -AudioFile "outputs\generated_music\wake_up_20251110.wav"
    .\analyze_music_file.ps1 -AudioFile "music\coding.mp3" -Phase FOCUS
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$AudioFile,
    
    [ValidateSet("WAKING", "FOCUS", "CODING", "REST", "DEEP_REST")]
    [string]$Phase,
    
    [switch]$Open
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

# Validate file
if (-not (Test-Path $AudioFile)) {
    Write-Host "❌ Audio file not found: $AudioFile" -ForegroundColor Red
    exit 1
}

$AudioFile = (Resolve-Path $AudioFile).Path

# Find Python
$PythonExe = $null
$VenvPaths = @(
    "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe",
    "$WorkspaceRoot\LLM_Unified\.venv\Scripts\python.exe"
)

foreach ($path in $VenvPaths) {
    if (Test-Path $path) {
        $PythonExe = $path
        break
    }
}

if (-not $PythonExe) {
    $PythonExe = "python"
}

# Run analysis
Write-Host "🎵 Analyzing audio file..." -ForegroundColor Cyan
Write-Host "   File: $(Split-Path -Leaf $AudioFile)" -ForegroundColor Gray

$AnalyzerScript = Join-Path $WorkspaceRoot "scripts\realtime_music_analyzer.py"

$ResultJson = & $PythonExe $AnalyzerScript --file $AudioFile --workspace $WorkspaceRoot 2>&1 | Out-String

# Parse result
try {
    $Result = $ResultJson | ConvertFrom-Json
    
    Write-Host "`n📊 Analysis Results:" -ForegroundColor Green
    Write-Host "   Current Phase: $($Result.current_phase)" -ForegroundColor Cyan
    
    if ($Result.features) {
        $Features = $Result.features
        Write-Host "`n🎵 Music Features:" -ForegroundColor White
        Write-Host "   Tempo: $([math]::Round($Features.tempo, 1)) BPM" -ForegroundColor Gray
        Write-Host "   Energy: $([math]::Round($Features.energy, 3))" -ForegroundColor Gray
        Write-Host "   Brightness: $([math]::Round($Features.brightness, 1)) Hz" -ForegroundColor Gray
        Write-Host "   Complexity: $([math]::Round($Features.complexity, 3))" -ForegroundColor Gray
    }
    
    Write-Host "`n📈 Phase Match:" -ForegroundColor White
    Write-Host "   Score: $([math]::Round($Result.match_score * 100, 1))%" -ForegroundColor Cyan
    Write-Host "   $($Result.verdict)" -ForegroundColor $(
        if ($Result.verdict -match "EXCELLENT") { "Green" }
        elseif ($Result.verdict -match "GOOD") { "Cyan" }
        elseif ($Result.verdict -match "SUBOPTIMAL") { "Yellow" }
        else { "Red" }
    )
    
    # Save report
    $OutputDir = Join-Path $WorkspaceRoot "outputs"
    $ReportFile = Join-Path $OutputDir "music_analysis_latest.json"
    $ResultJson | Out-File -FilePath $ReportFile -Encoding utf8 -Force
    
    Write-Host "`n✓ Report saved: outputs\music_analysis_latest.json" -ForegroundColor Green
    
    if ($Open) {
        code $ReportFile
    }
    
}
catch {
    Write-Host "❌ Failed to parse analysis results" -ForegroundColor Red
    Write-Host $ResultJson
    exit 1
}
