#Requires -Version 5.1
<#
.SYNOPSIS
    Check Auto-Stabilizer daemon status
.DESCRIPTION
    Displays the current status of the Auto-Stabilizer daemon
.EXAMPLE
    .\check_auto_stabilizer_status.ps1
#>
[CmdletBinding()]
param()
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path $WorkspaceRoot "outputs\auto_stabilizer_daemon.pid"
$LogFile = Join-Path $WorkspaceRoot "outputs\auto_stabilizer_daemon.log"

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📊 Auto-Stabilizer Daemon Status" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan

# Check PID file
if (Test-Path -LiteralPath $PidFile) {
    $SavedPid = Get-Content -Path $PidFile -Raw
    $SavedPid = $SavedPid.Trim()
    
    if ($SavedPid -match '^\d+$') {
        $Process = Get-Process -Id $SavedPid -ErrorAction SilentlyContinue
        
        if ($Process) {
            Write-Host "✅ Daemon RUNNING" -ForegroundColor Green
            Write-Host "   PID: $SavedPid" -ForegroundColor Gray
            Write-Host "   CPU: $([math]::Round($Process.CPU, 2))s" -ForegroundColor Gray
            Write-Host "   Memory: $([math]::Round($Process.WorkingSet64 / 1MB, 2)) MB" -ForegroundColor Gray
            
            # Check log file
            if (Test-Path -LiteralPath $LogFile) {
                $LogInfo = Get-Item -LiteralPath $LogFile
                Write-Host "`n📝 Log File:" -ForegroundColor Yellow
                Write-Host "   Path: $LogFile" -ForegroundColor Gray
                Write-Host "   Size: $([math]::Round($LogInfo.Length / 1KB, 2)) KB" -ForegroundColor Gray
                Write-Host "   Modified: $($LogInfo.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
                
                Write-Host "`n📄 Last 10 lines:" -ForegroundColor Yellow
                Get-Content -Path $LogFile -Tail 10 | ForEach-Object {
                    Write-Host "   $_" -ForegroundColor Gray
                }
            }
            
            Write-Host ""
            exit 0
        }
        else {
            Write-Host "❌ Daemon STOPPED (stale PID file)" -ForegroundColor Red
            Write-Host "   Stale PID: $SavedPid" -ForegroundColor Gray
            Write-Host "   Run: .\stop_auto_stabilizer_daemon.ps1 (cleanup)" -ForegroundColor Yellow
            Write-Host ""
            exit 1
        }
    }
}

# No PID file
Write-Host "❌ Daemon NOT RUNNING" -ForegroundColor Red
Write-Host "   No PID file found" -ForegroundColor Gray
Write-Host "`n💡 To start:" -ForegroundColor Yellow
Write-Host "   .\start_auto_stabilizer_daemon.ps1 -KillExisting" -ForegroundColor Cyan
Write-Host ""
exit 1