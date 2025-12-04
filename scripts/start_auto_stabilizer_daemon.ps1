#Requires -Version 5.1
<#
.SYNOPSIS
    Start Auto-Stabilizer as a background daemon
.DESCRIPTION
    Starts the Auto-Stabilizer Python script as a background process
    to continuously monitor Lumen emotional signals and trigger
    automatic recovery actions.
.PARAMETER IntervalSeconds
    Check interval in seconds (default: 600 = 10 minutes)
.PARAMETER AutoExecute
    Enable auto-execution of recovery actions (default: false)
.PARAMETER KillExisting
    Kill any existing Auto-Stabilizer processes before starting
.EXAMPLE
    .\start_auto_stabilizer_daemon.ps1 -KillExisting
.EXAMPLE
    .\start_auto_stabilizer_daemon.ps1 -IntervalSeconds 300 -AutoExecute
#>
[CmdletBinding()]
param(
    [int]$IntervalSeconds = 600,
    [switch]$AutoExecute,
    [switch]$KillExisting
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$PythonScript = Join-Path $WorkspaceRoot "scripts\auto_stabilizer.py"
$LogFile = Join-Path $WorkspaceRoot "outputs\auto_stabilizer_daemon.log"

# Ensure outputs directory
$OutputsDir = Split-Path -Parent $LogFile
if (!(Test-Path -LiteralPath $OutputsDir)) {
    New-Item -ItemType Directory -Path $OutputsDir -Force | Out-Null
}

# Kill existing processes if requested
if ($KillExisting) {
    Write-Host "🔍 Checking for existing Auto-Stabilizer processes..." -ForegroundColor Yellow
    
    # Use WMI for command line detection (PS 5.1 compatible)
    $ExistingProcs = Get-WmiObject Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" |
    Where-Object { $_.CommandLine -like "*auto_stabilizer.py*" }
    
    if ($ExistingProcs) {
        Write-Host "⚠️  Found $($ExistingProcs.Count) existing process(es). Terminating..." -ForegroundColor Yellow
        $ExistingProcs | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
        Start-Sleep -Seconds 2
        Write-Host "✅ Existing processes terminated" -ForegroundColor Green
    }
    else {
        Write-Host "✅ No existing processes found" -ForegroundColor Green
    }
}

# Find Python executable
$PythonExe = $null
$VenvPaths = @(
    "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe",
    "$WorkspaceRoot\LLM_Unified\.venv\Scripts\python.exe"
)

foreach ($Path in $VenvPaths) {
    if (Test-Path -LiteralPath $Path) {
        $PythonExe = $Path
        break
    }
}

if (!$PythonExe) {
    $PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (!$PythonExe) {
        Write-Host "❌ Python executable not found" -ForegroundColor Red
        exit 1
    }
}

Write-Host "🐍 Using Python: $PythonExe" -ForegroundColor Cyan

# Build command
$PythonArgs = @(
    $PythonScript,
    "--interval", $IntervalSeconds
)

if ($AutoExecute) {
    $PythonArgs += "--auto-execute"
    Write-Host "⚙️  Auto-execute mode: ENABLED" -ForegroundColor Yellow
}
else {
    Write-Host "⚙️  Auto-execute mode: DISABLED (dry-run)" -ForegroundColor Yellow
}

# Start background process
Write-Host "🚀 Starting Auto-Stabilizer daemon..." -ForegroundColor Cyan
Write-Host "   Check interval: $IntervalSeconds seconds" -ForegroundColor Gray
Write-Host "   Log file: $LogFile" -ForegroundColor Gray

$ProcessInfo = Start-Process -FilePath $PythonExe `
    -ArgumentList $PythonArgs `
    -RedirectStandardOutput $LogFile `
    -RedirectStandardError "$LogFile.err" `
    -WindowStyle Hidden `
    -PassThru

if ($ProcessInfo) {
    Write-Host "✅ Auto-Stabilizer daemon started (PID: $($ProcessInfo.Id))" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Monitor status:" -ForegroundColor Yellow
    Write-Host "   - Log: Get-Content '$LogFile' -Tail 20 -Wait" -ForegroundColor Gray
    Write-Host "   - Stop: Stop-Process -Id $($ProcessInfo.Id)" -ForegroundColor Gray
    Write-Host ""
    
    # Save PID for management
    $PidFile = Join-Path $WorkspaceRoot "outputs\auto_stabilizer_daemon.pid"
    $ProcessInfo.Id | Out-File -FilePath $PidFile -Encoding ASCII
    
    Write-Host "💾 PID saved to: $PidFile" -ForegroundColor Cyan
}
else {
    Write-Host "❌ Failed to start daemon" -ForegroundColor Red
    exit 1
}
