#Requires -Version 5.1
<#
.SYNOPSIS
    Stop Auto-Stabilizer daemon
.DESCRIPTION
    Stops the background Auto-Stabilizer process
.EXAMPLE
    .\stop_auto_stabilizer_daemon.ps1
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path $WorkspaceRoot "outputs\auto_stabilizer_daemon.pid"

Write-Host "🔍 Checking for Auto-Stabilizer daemon..." -ForegroundColor Yellow

# Check PID file
if (Test-Path -LiteralPath $PidFile) {
    $SavedPid = Get-Content -Path $PidFile -Raw
    $SavedPid = $SavedPid.Trim()
    
    if ($SavedPid -match '^\d+$') {
        $Process = Get-Process -Id $SavedPid -ErrorAction SilentlyContinue
        
        if ($Process -and $Process.ProcessName -like "python*") {
            Write-Host "⚠️  Found daemon process (PID: $SavedPid)" -ForegroundColor Yellow
            Stop-Process -Id $SavedPid -Force
            Remove-Item -Path $PidFile -Force
            Write-Host "✅ Daemon stopped" -ForegroundColor Green
            exit 0
        }
        else {
            Write-Host "⚠️  PID file exists but process not found. Cleaning up..." -ForegroundColor Yellow
            Remove-Item -Path $PidFile -Force
        }
    }
}

# Fallback: search by command line (WMI for PS 5.1 compatibility)
$Procs = Get-WmiObject Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" |
Where-Object { $_.CommandLine -like "*auto_stabilizer.py*" }

if ($Procs) {
    Write-Host "⚠️  Found $($Procs.Count) Auto-Stabilizer process(es)" -ForegroundColor Yellow
    $Procs | ForEach-Object {
        Write-Host "   Stopping PID $($_.ProcessId)..." -ForegroundColor Gray
        Stop-Process -Id $_.ProcessId -Force
    }
    Write-Host "✅ All processes stopped" -ForegroundColor Green
}
else {
    Write-Host "✅ No Auto-Stabilizer daemon found" -ForegroundColor Green
}
