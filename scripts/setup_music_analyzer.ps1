<#
.SYNOPSIS
    Setup Music Pattern Analyzer with librosa

.DESCRIPTION
    Installs required Python packages for music analysis
#>

param(
    [switch]$SkipInstall,
    [switch]$RunAnalysis
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Continue"

Write-Host "`n🎛️ Music Pattern Analyzer Setup" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor DarkCyan

# Find Python venv
$pythonExe = $null
$venvPaths = @(
    "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe",
    "$WorkspaceRoot\LLM_Unified\.venv\Scripts\python.exe"
)

foreach ($path in $venvPaths) {
    if (Test-Path $path) {
        $pythonExe = $path
        Write-Host "✅ Python venv found: $path" -ForegroundColor Green
        break
    }
}

if (-not $pythonExe) {
    Write-Host "❌ No Python venv found" -ForegroundColor Red
    Write-Host "   Looking for system Python..." -ForegroundColor Yellow
    $pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
    
    if ($pythonExe) {
        Write-Host "✅ System Python: $pythonExe" -ForegroundColor Green
    }
    else {
        Write-Host "❌ No Python found. Please install Python first." -ForegroundColor Red
        exit 1
    }
}

# Check current packages
Write-Host "`n📦 Checking installed packages..." -ForegroundColor Cyan
& $pythonExe -m pip list | Select-String -Pattern "librosa|numpy|soundfile"

if (-not $SkipInstall) {
    # Install dependencies
    Write-Host "`n📥 Installing music analysis packages..." -ForegroundColor Cyan
    Write-Host "   This may take a few minutes..." -ForegroundColor DarkGray
    
    $packages = @(
        "librosa",
        "numpy",
        "soundfile",
        "scipy",
        "numba"
    )
    
    foreach ($pkg in $packages) {
        Write-Host "`n   Installing $pkg..." -ForegroundColor Yellow
        & $pythonExe -m pip install $pkg --quiet --upgrade
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ $pkg installed" -ForegroundColor Green
        }
        else {
            Write-Host "   ⚠️ $pkg installation had warnings (may still work)" -ForegroundColor Yellow
        }
    }
}

# Verify installation
Write-Host "`n✅ Verifying installation..." -ForegroundColor Cyan
$testScript = @"
import sys
try:
    import librosa
    import numpy as np
    print('✅ librosa:', librosa.__version__)
    print('✅ numpy:', np.__version__)
    sys.exit(0)
except ImportError as e:
    print('❌ Import error:', e)
    sys.exit(1)
"@

$testFile = "$WorkspaceRoot\outputs\test_music_imports.py"
Set-Content -Path $testFile -Value $testScript -Encoding UTF8

& $pythonExe $testFile

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✨ Setup complete! Ready for music analysis!" -ForegroundColor Green
}
else {
    Write-Host "`n⚠️ Setup completed with warnings" -ForegroundColor Yellow
    Write-Host "   The analyzer may still work, try running it" -ForegroundColor DarkGray
}

# Clean up test file
Remove-Item $testFile -ErrorAction SilentlyContinue

if ($RunAnalysis) {
    Write-Host "`n🎵 Running music analysis..." -ForegroundColor Cyan
    & $pythonExe "$PSScriptRoot\reaper_music_pattern_analyzer.py"
}

Write-Host "`n" -NoNewline