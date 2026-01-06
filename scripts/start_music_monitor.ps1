#Requires -Version 5.1
<#
.SYNOPSIS
    Start realtime music monitoring daemon

.DESCRIPTION
    Continuously monitors playing music and validates rhythm phase matching.
    Alerts when music is not suitable for current phase.

.PARAMETER IntervalSeconds
    Analysis interval in seconds (default: 30)

.PARAMETER KillExisting
    Kill existing monitor before starting

.EXAMPLE
    .\start_music_monitor.ps1
    .\start_music_monitor.ps1 -IntervalSeconds 60 -KillExisting
#>

param(
    [int]$IntervalSeconds = 30,
    [switch]$KillExisting
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

# Kill existing monitor
if ($KillExisting) {
    Write-Host "🛑 Stopping existing music monitors..." -ForegroundColor Yellow
    Get-Process -Name "pwsh", "powershell", "python" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*realtime_music_analyzer.py*" } |
    Stop-Process -Force
    Start-Sleep -Seconds 1
}

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

# Check librosa availability
Write-Host "🔍 Checking audio libraries..." -ForegroundColor Cyan
$LibCheck = & $PythonExe -c "try: import librosa, sounddevice; print('OK')
except: print('MISSING')" 2>&1

if ($LibCheck -notmatch "OK") {
    Write-Host "⚠️ Required libraries not installed" -ForegroundColor Yellow
    Write-Host "   Installing librosa and sounddevice..." -ForegroundColor Cyan
    
    & $PythonExe -m pip install librosa sounddevice --quiet
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install libraries" -ForegroundColor Red
        Write-Host "   Please run: pip install librosa sounddevice" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "✓ Libraries installed successfully" -ForegroundColor Green
}

# Start monitor
Write-Host "`n🎵 Starting realtime music monitor..." -ForegroundColor Green
Write-Host "   Interval: $IntervalSeconds seconds" -ForegroundColor Cyan
Write-Host "   Press Ctrl+C to stop`n" -ForegroundColor Yellow

$MonitorScript = Join-Path $WorkspaceRoot "scripts\realtime_music_analyzer.py"

& $PythonExe $MonitorScript --monitor --interval $IntervalSeconds --workspace $WorkspaceRoot

Write-Host "`n✓ Music monitor stopped" -ForegroundColor Green