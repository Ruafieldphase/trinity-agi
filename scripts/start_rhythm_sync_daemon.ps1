# Rhythm Sync Daemon - Runs continuously in background
# Syncs Brain state from Linux to Windows every 5 seconds

$ErrorActionPreference = "SilentlyContinue"

Write-Host "🧠 Rhythm Sync Daemon Started" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

$syncScript = Join-Path $PSScriptRoot "sync_rhythm_from_linux.ps1"

while ($true) {
    try {
        # Run sync
        & $syncScript
        
        # Wait 5 seconds
        Start-Sleep -Seconds 5
    }
    catch {
        Write-Host "⚠️ Sync error: $_" -ForegroundColor Red
        Start-Sleep -Seconds 10
    }
}
