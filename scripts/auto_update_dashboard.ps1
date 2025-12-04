# AGI Dashboard Auto-Updater
# ===========================
# 
# Automatically regenerate performance dashboard at specified intervals
# 
# Usage:
#   .\scripts\auto_update_dashboard.ps1                    # Update every 5 minutes (default)
#   .\scripts\auto_update_dashboard.ps1 -IntervalMinutes 3 # Update every 3 minutes
#   .\scripts\auto_update_dashboard.ps1 -Once              # Update once and exit

param(
    [int]$IntervalMinutes = 5,
    [switch]$Once
)

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptRoot
$PythonScript = Join-Path $RootDir "scripts\generate_performance_dashboard.py"
$PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source

if (-not $PythonExe) {
    $PythonExe = "py"
}

if (-not (Test-Path $PythonScript)) {
    Write-Host "[ERROR] Dashboard script not found: $PythonScript" -ForegroundColor Red
    exit 1
}

function Update-Dashboard {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [RELOAD] Updating dashboard..." -ForegroundColor Cyan
    
    Push-Location $RootDir
    try {
        # Capture output and error separately to preserve exit code
        $output = & $PythonExe $PythonScript 2>&1
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0 -or $output -match "Dashboard generated") {
            Write-Host "[$timestamp] [OK] Dashboard updated successfully" -ForegroundColor Green
        }
        else {
            Write-Host "[$timestamp] [WARN] Dashboard update failed (exit code: $exitCode)" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "[$timestamp] [ERROR] Error: $_" -ForegroundColor Red
    }
    finally {
        Pop-Location
    }
}

if ($Once) {
    Write-Host "[START] Running single dashboard update..." -ForegroundColor Cyan
    Update-Dashboard
    Write-Host "[OK] Done!" -ForegroundColor Green
    exit 0
}

Write-Host "[START] Starting AGI Dashboard Auto-Updater" -ForegroundColor Cyan
Write-Host "   Update interval: $IntervalMinutes minutes" -ForegroundColor White
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

$intervalSeconds = $IntervalMinutes * 60

# Initial update
Update-Dashboard

# Main loop
while ($true) {
    Start-Sleep -Seconds $intervalSeconds
    Update-Dashboard
}
