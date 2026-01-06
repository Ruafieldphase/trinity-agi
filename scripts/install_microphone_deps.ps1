#requires -Version 5.1
<#
.SYNOPSIS
    🎤 Install microphone analysis dependencies

.DESCRIPTION
    Installs sounddevice, numpy, scipy for microphone frequency analysis.

.EXAMPLE
    powershell -File scripts/install_microphone_deps.ps1
#>

param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$wsRoot = Split-Path -Parent $PSScriptRoot

# Detect Python
$py = $null
$candidates = @(
    (Join-Path $wsRoot 'fdo_agi_repo\.venv\Scripts\python.exe'),
    (Join-Path $wsRoot 'LLM_Unified\.venv\Scripts\python.exe'),
    'python'
)

foreach ($candidate in $candidates) {
    if (Test-Path -LiteralPath $candidate -ErrorAction SilentlyContinue) {
        $py = $candidate
        break
    }
    if ($candidate -eq 'python') {
        try {
            $null = & python --version 2>&1
            $py = 'python'
            break
        }
        catch {}
    }
}

if (-not $py) {
    Write-Host "❌ Python not found!" -ForegroundColor Red
    exit 1
}

Write-Host "🐍 Using Python: $py" -ForegroundColor Cyan

# Install packages
Write-Host "`n📦 Installing microphone analysis dependencies..." -ForegroundColor Yellow
Write-Host "   - sounddevice (audio capture)" -ForegroundColor Gray
Write-Host "   - numpy (array processing)" -ForegroundColor Gray
Write-Host "   - scipy (FFT analysis)" -ForegroundColor Gray

try {
    & $py -m pip install --upgrade sounddevice numpy scipy
    
    if ($LASTEXITCODE -ne 0) {
        throw "pip install failed with exit code $LASTEXITCODE"
    }
    
    Write-Host "`n✅ Installation complete!" -ForegroundColor Green
    Write-Host "`n🎤 Test your microphone:" -ForegroundColor Cyan
    Write-Host "   Run VS Code task: '🎤 Microphone: List Devices'" -ForegroundColor White
    Write-Host "   Or run: python scripts/microphone_frequency_analyzer.py --list-devices" -ForegroundColor Gray
    
}
catch {
    Write-Host "`n❌ Installation failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}