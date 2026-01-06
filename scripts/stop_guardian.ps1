# Rhythm Guardian Stopper
# Guardian을 안전하게 종료합니다


. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot
$ErrorActionPreference = "SilentlyContinue"
$ProjectRoot = "$WorkspaceRoot"
$PidFile = "$ProjectRoot\outputs\rhythm_guardian.pid"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Rhythm Guardian Stopper" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (Test-Path $PidFile) {
    $pid = Get-Content $PidFile
    $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue

    if ($proc) {
        Write-Host "[STOP] Stopping Guardian (PID: $pid)..." -ForegroundColor Yellow
        Stop-Process -Id $pid -Force
        Start-Sleep -Seconds 1
        Write-Host "[OK] Guardian stopped" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Guardian not running (stale PID)" -ForegroundColor Yellow
    }

    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
} else {
    Write-Host "[INFO] Guardian is not running" -ForegroundColor Gray
}

Write-Host "========================================" -ForegroundColor Cyan