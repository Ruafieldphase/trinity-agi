# Clean Up Orphaned and Duplicate Processes
# Removes zombie processes and consolidates duplicate work

param(
    [switch]$DryRun,  # Show what would be removed without actually removing
    [switch]$Force    # Force kill even important processes
)

$ErrorActionPreference = "Continue"

Write-Host "`n" -NoNewline
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "  Process Cleanup Utility" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "🔍 DRY RUN MODE - No processes will be actually killed" -ForegroundColor Yellow
    Write-Host ""
}

# Get all python processes
$pythonProcs = Get-Process | Where-Object { $_.ProcessName -like '*python*' }

Write-Host "Found $($pythonProcs.Count) Python processes" -ForegroundColor Cyan
Write-Host ""

# Analyze processes
$largeMem = $pythonProcs | Where-Object { $_.WorkingSet64 -gt 100MB }
$idleLong = $pythonProcs | Where-Object { $_.TotalProcessorTime.TotalSeconds -eq 0 }
$cpuHeavy = $pythonProcs | Where-Object { $_.TotalProcessorTime.TotalSeconds -gt 20 }

Write-Host "Analysis:" -ForegroundColor Yellow
Write-Host "  Large Memory (>100MB): $($largeMem.Count)" -ForegroundColor $(if ($largeMem.Count -gt 0) { "Red" } else { "Green" })
Write-Host "  Idle (0 CPU time): $($idleLong.Count)" -ForegroundColor $(if ($idleLong.Count -gt 20) { "Yellow" } else { "Green" })
Write-Host "  High CPU (>20s): $($cpuHeavy.Count)" -ForegroundColor $(if ($cpuHeavy.Count -gt 0) { "Red" } else { "Green" })

Write-Host ""

# Categorize for cleanup
$toClean = @()

# 1. Idle processes with no CPU usage (likely zombie)
if ($idleLong.Count -gt 5) {
    Write-Host "🧹 Cleaning Idle Processes (0 CPU time):" -ForegroundColor Yellow

    # Keep some idle processes, remove excess
    $idleCutoff = [Math]::Max(3, $idleLong.Count - 10)
    $idleToRemove = $idleLong | Select-Object -First $idleCutoff

    foreach ($proc in $idleToRemove) {
        $memMB = [math]::Round($proc.WorkingSet64 / 1MB, 1)

        if (-not $DryRun) {
            try {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                Write-Host "  ✓ Killed PID $($proc.Id) ($memMB MB)" -ForegroundColor Green
            } catch {
                Write-Host "  ✗ Failed to kill PID $($proc.Id): $_" -ForegroundColor Red
            }
        } else {
            Write-Host "  → Would kill PID $($proc.Id) ($memMB MB)" -ForegroundColor Gray
        }
    }

    Write-Host ""
}

# 2. Large memory consumers
if ($largeMem.Count -gt 0) {
    Write-Host "🔴 Large Memory Consumers (>100MB):" -ForegroundColor Yellow

    foreach ($proc in $largeMem) {
        $memMB = [math]::Round($proc.WorkingSet64 / 1MB, 1)
        $cpuTime = [math]::Round($proc.TotalProcessorTime.TotalSeconds, 1)

        Write-Host "  PID $($proc.Id): $memMB MB, CPU: ${cpuTime}s"

        # Only force-kill if explicitly requested
        if ($Force -and -not $DryRun) {
            try {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                Write-Host "    → Killed" -ForegroundColor Red
            } catch {
                Write-Host "    → Failed: $_" -ForegroundColor Gray
            }
        } else {
            Write-Host "    → (Preserve) Use -Force to remove" -ForegroundColor Gray
        }
    }

    Write-Host ""
}

# 3. Heavy CPU processes
if ($cpuHeavy.Count -gt 0) {
    Write-Host "🔥 High CPU Processes (>20s):" -ForegroundColor Yellow

    foreach ($proc in $cpuHeavy) {
        $memMB = [math]::Round($proc.WorkingSet64 / 1MB, 1)
        $cpuTime = [math]::Round($proc.TotalProcessorTime.TotalSeconds, 1)

        Write-Host "  PID $($proc.Id): CPU: ${cpuTime}s, Memory: $memMB MB"
        Write-Host "    → (Monitor) Check if this is expected work" -ForegroundColor Yellow
    }

    Write-Host ""
}

# Summary
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Total Python Processes: $($pythonProcs.Count)" -ForegroundColor White
Write-Host "  Processes to Clean: $($idleToRemove.Count)" -ForegroundColor $(if ($idleToRemove.Count -gt 0) { "Yellow" } else { "Green" })

if ($DryRun) {
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Review the dry run output above" -ForegroundColor Gray
    Write-Host "  2. Run without -DryRun to actually clean up:" -ForegroundColor Gray
    Write-Host "     .\scripts\cleanup_processes.ps1" -ForegroundColor Gray
    Write-Host "  3. For large processes, use -Force with caution:" -ForegroundColor Gray
    Write-Host "     .\scripts\cleanup_processes.ps1 -Force" -ForegroundColor Gray
}

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""
