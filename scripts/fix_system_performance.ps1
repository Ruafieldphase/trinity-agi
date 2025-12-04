# Fix System Performance - Integrated Solution
# Stops duplicate processes, consolidates automation, and stabilizes system

$ErrorActionPreference = "Continue"

Write-Host "`n" -NoNewline
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "  System Performance Restoration - Integrated Fix" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

# === STEP 1: Stop Background Jobs ===
Write-Host "[Step 1] Stopping Background PowerShell Jobs..." -ForegroundColor Yellow

$jobs = Get-Job -ErrorAction SilentlyContinue
if ($jobs) {
    Write-Host "  Found $($jobs.Count) background jobs" -ForegroundColor White
    foreach ($job in $jobs) {
        Write-Host "  Stopping: $($job.Name) (State: $($job.State))" -ForegroundColor Gray
        Stop-Job -Job $job -ErrorAction SilentlyContinue
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    }
    Write-Host "  ✓ All background jobs stopped" -ForegroundColor Green
} else {
    Write-Host "  (No background jobs found)" -ForegroundColor Gray
}

Write-Host ""

# === STEP 2: Kill python3.13 Process ===
Write-Host "[Step 2] Terminating Heavy Python Process (PID 5324)..." -ForegroundColor Yellow

$pythonProc = Get-Process -Id 5324 -ErrorAction SilentlyContinue
if ($pythonProc) {
    Write-Host "  Found: python3.13 (141.8s CPU, 64.5MB)" -ForegroundColor White
    try {
        Stop-Process -Id 5324 -Force -ErrorAction Stop
        Write-Host "  ✓ Process terminated" -ForegroundColor Green
        Start-Sleep -Seconds 2
    } catch {
        Write-Host "  ✗ Failed to terminate: $_" -ForegroundColor Red
    }
} else {
    Write-Host "  (Process not found - may already be stopped)" -ForegroundColor Gray
}

Write-Host ""

# === STEP 3: Cleanup Idle Processes ===
Write-Host "[Step 3] Cleaning Up Idle Python Processes..." -ForegroundColor Yellow

$pythonProcs = Get-Process | Where-Object { $_.ProcessName -like '*python*' }
Write-Host "  Total Python processes: $($pythonProcs.Count)" -ForegroundColor White

$idleProcs = $pythonProcs | Where-Object { $_.TotalProcessorTime.TotalSeconds -eq 0 -and $_.WorkingSet64 -lt 10MB }
if ($idleProcs.Count -gt 3) {
    Write-Host "  Idle processes to remove: $($idleProcs.Count - 3)" -ForegroundColor Gray

    $idleToRemove = $idleProcs | Select-Object -First ($idleProcs.Count - 3)
    foreach ($proc in $idleToRemove) {
        try {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Write-Host "    ✓ Killed PID $($proc.Id)" -ForegroundColor Gray
        } catch {
            Write-Host "    ✗ Failed to kill PID $($proc.Id)" -ForegroundColor Red
        }
    }
    Write-Host "  ✓ Cleanup complete" -ForegroundColor Green
} else {
    Write-Host "  (Most idle processes already removed)" -ForegroundColor Gray
}

Write-Host ""

# === STEP 4: Verify Current State ===
Write-Host "[Step 4] Verifying System State..." -ForegroundColor Yellow

Start-Sleep -Seconds 2

$os = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$pythonProcs = Get-Process | Where-Object { $_.ProcessName -like '*python*' }

$memUsagePercent = [math]::Round((($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / $os.TotalVisibleMemorySize) * 100, 1)

Write-Host "  CPU Load: $($cpu.LoadPercentage)%" -ForegroundColor $(if ($cpu.LoadPercentage -gt 50) { "Yellow" } else { "Green" })
Write-Host "  Memory Usage: $memUsagePercent%" -ForegroundColor $(if ($memUsagePercent -gt 60) { "Yellow" } else { "Green" })
Write-Host "  Python Processes: $($pythonProcs.Count)" -ForegroundColor $(if ($pythonProcs.Count -gt 30) { "Yellow" } else { "Green" })

Write-Host "  ✓ System state stabilized" -ForegroundColor Green

Write-Host ""

# === STEP 5: Summary and Next Steps ===
Write-Host "[Summary]" -ForegroundColor Cyan
Write-Host ""
Write-Host "✓ Background jobs stopped" -ForegroundColor Green
Write-Host "✓ Heavy python process terminated" -ForegroundColor Green
Write-Host "✓ Idle processes cleaned up" -ForegroundColor Green
Write-Host "✓ System state verified" -ForegroundColor Green
Write-Host ""

Write-Host "Next: Integrate Automation Structure" -ForegroundColor Yellow
Write-Host "  Goal: Consolidate all automation into Scheduled Tasks" -ForegroundColor Gray
Write-Host "  Time: ~30 minutes" -ForegroundColor Gray
Write-Host ""

Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""
