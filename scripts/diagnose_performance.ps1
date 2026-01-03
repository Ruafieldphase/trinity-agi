. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot

# System Performance Diagnosis Script
# Identifies potential bottlenecks and slowdowns

$ErrorActionPreference = "Continue"

Write-Host "`n" -NoNewline
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "  AGI System Performance Diagnosis" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

# 1. Running Processes
Write-Host "[1] Running AGI-Related Processes" -ForegroundColor Yellow
Write-Host ""

$pythonProcesses = Get-Process | Where-Object { $_.ProcessName -like '*python*' }
$lmStudio = Get-Process | Where-Object { $_.ProcessName -like '*LM*' } -ErrorAction SilentlyContinue
$nodeProcesses = Get-Process | Where-Object { $_.ProcessName -like '*node*' } -ErrorAction SilentlyContinue

Write-Host "Python Processes:" -ForegroundColor Cyan
if ($pythonProcesses) {
    foreach ($proc in $pythonProcesses) {
        $memMB = [math]::Round($proc.WorkingSet64 / 1MB, 1)
        $cpuTime = [math]::Round($proc.TotalProcessorTime.TotalSeconds, 1)
        Write-Host "  • $($proc.ProcessName) (PID: $($proc.Id)) - CPU: ${cpuTime}s, Memory: ${memMB}MB"
    }
} else {
    Write-Host "  (None running)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "LM Studio:" -ForegroundColor Cyan
if ($lmStudio) {
    $memMB = [math]::Round($lmStudio.WorkingSet64 / 1MB, 1)
    Write-Host "  • LM Studio (PID: $($lmStudio.Id)) - Memory: ${memMB}MB" -ForegroundColor Green
} else {
    Write-Host "  (Not running)" -ForegroundColor Yellow
}

# 2. Recent Performance Data
Write-Host ""
Write-Host "[2] Recent Performance Metrics (Last 24h)" -ForegroundColor Yellow
Write-Host ""

if (Test-Path "$WorkspaceRoot\outputs\monitoring_metrics_latest.json") {
    try {
        $metrics = Get-Content "$WorkspaceRoot\outputs\monitoring_metrics_latest.json" -Raw | ConvertFrom-Json

        Write-Host "Core Gateway:" -ForegroundColor Cyan
        Write-Host "  Mean: $($metrics.Channels.Gateway.Mean)ms" -ForegroundColor White
        Write-Host "  Median: $($metrics.Channels.Gateway.Median)ms" -ForegroundColor White
        Write-Host "  P95: $($metrics.Channels.Gateway.P95)ms" -ForegroundColor White
        Write-Host "  Std Dev: $($metrics.Channels.Gateway.Std)ms" -ForegroundColor White
        Write-Host "  Spikes: $($metrics.Channels.Gateway.Spikes)" -ForegroundColor $(if ($metrics.Channels.Gateway.Spikes -gt 5) { "Yellow" } else { "Green" })

        Write-Host ""
        Write-Host "Local LLM:" -ForegroundColor Cyan
        Write-Host "  Mean: $($metrics.Channels.Local.Mean)ms" -ForegroundColor White
        Write-Host "  Median: $($metrics.Channels.Local.Median)ms" -ForegroundColor White
        Write-Host "  P95: $($metrics.Channels.Local.P95)ms" -ForegroundColor White
        Write-Host "  Availability: $($metrics.Channels.Local.Availability)%" -ForegroundColor $(if ($metrics.Channels.Local.Availability -lt 99) { "Yellow" } else { "Green" })

        Write-Host ""
        Write-Host "Snapshot Count: $($metrics.SnapshotCount) samples" -ForegroundColor White

    } catch {
        Write-Host "Error reading metrics: $_" -ForegroundColor Red
    }
} else {
    Write-Host "No metrics file found" -ForegroundColor Yellow
}

# 3. Event Log Analysis
Write-Host ""
Write-Host "[3] System Activity (Last 24h)" -ForegroundColor Yellow
Write-Host ""

if (Test-Path "$WorkspaceRoot\fdo_agi_repo\memory\resonance_ledger.jsonl") {
    $eventLines = @(Get-Content "$WorkspaceRoot\fdo_agi_repo\memory\resonance_ledger.jsonl")
    $totalEvents = $eventLines.Count
    $eventRate = [math]::Round($totalEvents / (24 * 60), 2)

    Write-Host "Total Events: $totalEvents" -ForegroundColor White
    Write-Host "Event Rate: $eventRate events/minute" -ForegroundColor White

    # Check for recent events
    if ($eventLines.Count -gt 0) {
        $lastEvent = $eventLines[-1] | ConvertFrom-Json -ErrorAction SilentlyContinue
        if ($lastEvent) {
            Write-Host "Last Event: $($lastEvent.timestamp)" -ForegroundColor White
            $minutesSinceLastEvent = ((Get-Date) - [datetime]::Parse($lastEvent.timestamp)).TotalMinutes
            Write-Host "Minutes Since Last Event: $([math]::Round($minutesSinceLastEvent, 1))" -ForegroundColor $(if ($minutesSinceLastEvent -gt 10) { "Yellow" } else { "Green" })
        }
    }
} else {
    Write-Host "No event log found" -ForegroundColor Yellow
}

# 4. System Resources
Write-Host ""
Write-Host "[4] System Resources" -ForegroundColor Yellow
Write-Host ""

$os = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$disk = Get-Volume C -ErrorAction SilentlyContinue

$memUsagePercent = [math]::Round((($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / $os.TotalVisibleMemorySize) * 100, 1)
$memAvailableGB = [math]::Round($os.FreePhysicalMemory / 1MB / 1024, 1)
$memTotalGB = [math]::Round($os.TotalVisibleMemorySize / 1MB / 1024, 1)

Write-Host "CPU Load: $($cpu.LoadPercentage)%" -ForegroundColor $(if ($cpu.LoadPercentage -gt 80) { "Red" } elseif ($cpu.LoadPercentage -gt 50) { "Yellow" } else { "Green" })
Write-Host "Memory: $memUsagePercent% ($memAvailableGB GB / $memTotalGB GB available)" -ForegroundColor $(if ($memUsagePercent -gt 80) { "Red" } elseif ($memUsagePercent -gt 60) { "Yellow" } else { "Green" })

if ($disk) {
    $diskUsagePercent = [math]::Round(((($disk.Size - $disk.SizeRemaining) / $disk.Size) * 100), 1)
    Write-Host "Disk (C:): $diskUsagePercent% used" -ForegroundColor $(if ($diskUsagePercent -gt 90) { "Red" } elseif ($diskUsagePercent -gt 75) { "Yellow" } else { "Green" })
}

# 5. Identify Bottlenecks
Write-Host ""
Write-Host "[5] Performance Analysis & Recommendations" -ForegroundColor Yellow
Write-Host ""

$issues = @()

if ($cpu.LoadPercentage -gt 70) {
    $issues += "⚠️  HIGH CPU USAGE: Consider stopping non-essential processes"
}

if ($memUsagePercent -gt 80) {
    $issues += "⚠️  HIGH MEMORY USAGE: System may be paging to disk"
}

if ($pythonProcesses.Count -gt 5) {
    $issues += "⚠️  MULTIPLE PYTHON PROCESSES: Check for duplicate/redundant processes"
}

if ($lmStudio -and $lmStudio.WorkingSet64 / 1GB -gt 8) {
    $issues += "⚠️  LM STUDIO MEMORY USAGE: Model may be too large for available VRAM"
}

if ($minutesSinceLastEvent -gt 30) {
    $issues += "⚠️  INACTIVITY: No events in last $([math]::Round($minutesSinceLastEvent)) minutes"
}

if ($metrics.Channels.Gateway.Std -gt 150) {
    $issues += "⚠️  HIGH LATENCY VARIANCE: Network instability detected"
}

if ($issues.Count -gt 0) {
    foreach ($issue in $issues) {
        Write-Host $issue -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ No major bottlenecks detected" -ForegroundColor Green
}

# 6. Recent Changes Impact
Write-Host ""
Write-Host "[6] Impact of Recent Changes" -ForegroundColor Yellow
Write-Host ""

Write-Host "New Features Loaded:" -ForegroundColor Cyan
$newScripts = @(
    "circuit_breaker_router.py",
    "auto_restart_local_llm.ps1",
    "analyze_latency_spikes.ps1",
    "open_monitoring_dashboard.ps1"
)

foreach ($script in $newScripts) {
    $exists = Test-Path "$PSScriptRoot\$script"
    Write-Host "  $([char]8730) $script" -ForegroundColor $(if ($exists) { "Green" } else { "Red" })
}

Write-Host ""
Write-Host "Potential Sources of Slowdown:" -ForegroundColor Cyan
Write-Host "  1. Monitoring overhead: check_health.py running frequently"
Write-Host "  2. Auto-restart loop: Continuous monitoring may consume CPU"
Write-Host "  3. Scheduled tasks: Multiple overlapping schedules"
Write-Host "  4. Background processes: Python/Node services accumulating"
Write-Host ""

Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""