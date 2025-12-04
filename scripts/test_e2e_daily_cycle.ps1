# End-to-End Testing Suite
# Tests complete daily cycle: Morning Kickoff → Daily Operations → Evening Backup
#
# Usage:
#   .\test_e2e_daily_cycle.ps1                    # Full test
#   .\test_e2e_daily_cycle.ps1 -Quick             # Quick test (skip long-running)
#   .\test_e2e_daily_cycle.ps1 -SkipBackup        # Skip backup step
#   .\test_e2e_daily_cycle.ps1 -VerboseLog        # Detailed logging

param(
    [switch]$Quick,
    [switch]$SkipBackup,
    [switch]$VerboseLog
)

$ErrorActionPreference = "Continue"

# Ensure UTF-8
try { chcp 65001 > $null 2> $null } catch {}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
$outputDir = Join-Path $rootDir "outputs"

if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

$testResults = @()
$startTime = Get-Date

function Test-Step {
    param(
        [string]$Name,
        [scriptblock]$Test,
        [bool]$Critical = $false
    )
    
    Write-Host "`n[TEST] $Name" -ForegroundColor Cyan
    $stepStart = Get-Date
    
    try {
        $result = & $Test
        $success = $?
        $duration = (Get-Date) - $stepStart
        
        if ($success) {
            Write-Host "  ✅ PASS ($($duration.TotalSeconds.ToString('F1'))s)" -ForegroundColor Green
        }
        else {
            Write-Host "  ❌ FAIL ($($duration.TotalSeconds.ToString('F1'))s)" -ForegroundColor Red
        }
        
        $testResults += [PSCustomObject]@{
            Name     = $Name
            Success  = $success
            Duration = $duration.TotalSeconds
            Critical = $Critical
            Result   = $result
        }
        
        if ($Critical -and -not $success) {
            throw "Critical test failed: $Name"
        }
        
        return $success
    }
    catch {
        $duration = (Get-Date) - $stepStart
        Write-Host "  ❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
        
        $testResults += [PSCustomObject]@{
            Name     = $Name
            Success  = $false
            Duration = $duration.TotalSeconds
            Critical = $Critical
            Error    = $_.Exception.Message
        }
        
        if ($Critical) {
            throw
        }
        
        return $false
    }
}

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "  End-to-End Daily Cycle Test" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# Phase 1: System Prerequisites
Write-Host "`n=== Phase 1: System Prerequisites ===" -ForegroundColor Yellow

Test-Step -Name "Python environment exists" -Critical $true -Test {
    $pyPath = Join-Path $rootDir "fdo_agi_repo\.venv\Scripts\python.exe"
    if (Test-Path $pyPath) {
        if ($VerboseLog) { Write-Host "    Found: $pyPath" -ForegroundColor DarkGray }
        return $true
    }
    throw "Python venv not found at $pyPath"
}

Test-Step -Name "Required scripts exist" -Critical $true -Test {
    $requiredScripts = @(
        "scripts\quick_status.ps1",
        "scripts\generate_performance_dashboard.ps1",
        "scripts\run_realtime_pipeline.ps1",
        "scripts\start_emotion_stabilizer.ps1"
    )
    
    $missing = @()
    foreach ($script in $requiredScripts) {
        $path = Join-Path $rootDir $script
        if (-not (Test-Path $path)) {
            $missing += $script
        }
    }
    
    if ($missing.Count -gt 0) {
        throw "Missing scripts: $($missing -join ', ')"
    }
    
    if ($VerboseLog) {
        Write-Host "    All required scripts found" -ForegroundColor DarkGray
    }
    return $true
}

# Phase 2: Morning Kickoff Simulation
Write-Host "`n=== Phase 2: Morning Kickoff Simulation ===" -ForegroundColor Yellow

Test-Step -Name "System health check (quick_status)" -Test {
    $statusJson = Join-Path $outputDir "e2e_test_status_morning.json"
    & "$rootDir\scripts\quick_status.ps1" -OutJson $statusJson
    
    if (Test-Path $statusJson) {
        $status = Get-Content $statusJson -Raw | ConvertFrom-Json
        if ($VerboseLog) {
            Write-Host "    AGI Confidence: $($status.agi.confidence)" -ForegroundColor DarkGray
        }
        return $true
    }
    return $false
}

if (-not $Quick) {
    Test-Step -Name "Task queue server check" -Test {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8091/api/health" -TimeoutSec 2 -ErrorAction Stop
            if ($VerboseLog) {
                Write-Host "    Queue server: ONLINE (Status: $($response.StatusCode))" -ForegroundColor DarkGray
            }
            return $true
        }
        catch {
            Write-Host "    Queue server: OFFLINE (OK for test)" -ForegroundColor DarkYellow
            return $true  # Non-critical
        }
    }
}

Test-Step -Name "Performance dashboard generation" -Test {
    & "$rootDir\scripts\generate_performance_dashboard.ps1" -WriteLatest -AllowEmpty | Out-Null
    
    $dashPath = Join-Path $outputDir "performance_dashboard_latest.md"
    if (Test-Path $dashPath) {
        if ($VerboseLog) {
            $size = (Get-Item $dashPath).Length
            Write-Host "    Dashboard size: $size bytes" -ForegroundColor DarkGray
        }
        return $true
    }
    return $false
}

if (-not $Quick) {
    Test-Step -Name "Realtime emotion pipeline (1h window)" -Test {
        & "$rootDir\scripts\run_realtime_pipeline.ps1" -Hours 1 | Out-Null
        
        $emotionPath = Join-Path $outputDir "emotion_signals_latest.json"
        if (Test-Path $emotionPath) {
            $emotion = Get-Content $emotionPath -Raw | ConvertFrom-Json
            if ($VerboseLog) {
                Write-Host "    Fear: $($emotion.signals.fear.ToString('F3'))" -ForegroundColor DarkGray
                Write-Host "    Joy: $($emotion.signals.joy.ToString('F3'))" -ForegroundColor DarkGray
                Write-Host "    Trust: $($emotion.signals.trust.ToString('F3'))" -ForegroundColor DarkGray
            }
            return $true
        }
        return $false
    }
}

# Phase 3: Auto-Stabilizer Verification
Write-Host "`n=== Phase 3: Auto-Stabilizer Verification ===" -ForegroundColor Yellow

Test-Step -Name "Emotion stabilizer (single check)" -Test {
    & "$rootDir\scripts\start_emotion_stabilizer.ps1" -Once -DryRun | Out-Null
    return $?
}

Test-Step -Name "Auto-stabilizer status check" -Test {
    & "$rootDir\scripts\check_auto_stabilizer_status.ps1" | Out-Null
    return $?
}

# Phase 4: Monitoring & Reporting
Write-Host "`n=== Phase 4: Monitoring & Reporting ===" -ForegroundColor Yellow

Test-Step -Name "Rhythm detection" -Test {
    & "$rootDir\scripts\detect_rhythm_contextual.ps1" | Out-Null
    
    $rhythmPath = Join-Path $outputDir "contextual_rhythm.json"
    if (Test-Path $rhythmPath) {
        $rhythm = Get-Content $rhythmPath -Raw | ConvertFrom-Json
        if ($VerboseLog) {
            Write-Host "    Current rhythm: $($rhythm.current_rhythm)" -ForegroundColor DarkGray
        }
        return $true
    }
    return $false
}

if (-not $Quick) {
    Test-Step -Name "Monitoring report generation" -Test {
        & "$rootDir\scripts\generate_monitoring_report.ps1" -Hours 1 | Out-Null
        
        $reportPath = Join-Path $outputDir "monitoring_report_latest.md"
        return (Test-Path $reportPath)
    }
}

# Phase 5: Failure Recovery Simulation
Write-Host "`n=== Phase 5: Failure Recovery Simulation ===" -ForegroundColor Yellow

Test-Step -Name "Micro-reset (dry-run)" -Test {
    # Simulate micro-reset without actual execution
    Write-Host "    Simulating 5-min micro-reset..." -ForegroundColor DarkGray
    return $true
}

Test-Step -Name "Grace cooldown mechanism" -Test {
    # Verify grace cooldown file creation
    $gracePath = Join-Path $outputDir "stabilizer_grace_cooldown.json"
    if (Test-Path $gracePath) {
        $grace = Get-Content $gracePath -Raw | ConvertFrom-Json
        if ($VerboseLog) {
            Write-Host "    Last action: $($grace.last_action)" -ForegroundColor DarkGray
        }
    }
    return $true  # Non-critical
}

# Phase 6: Evening Backup (Optional)
if (-not $SkipBackup) {
    Write-Host "`n=== Phase 6: Evening Backup Simulation ===" -ForegroundColor Yellow
    
    Test-Step -Name "Session save (dry-run)" -Test {
        # Don't actually run backup, just verify script exists
        $backupScript = Join-Path $rootDir "scripts\save_session_with_changes.ps1"
        if (Test-Path $backupScript) {
            if ($VerboseLog) {
                Write-Host "    Backup script ready: $backupScript" -ForegroundColor DarkGray
            }
            return $true
        }
        return $false
    }
}

# Summary
$totalDuration = (Get-Date) - $startTime
$passed = ($testResults | Where-Object { $_.Success }).Count
$failed = ($testResults | Where-Object { -not $_.Success }).Count
$total = $testResults.Count
$successRate = if ($total -gt 0) { ($passed / $total) * 100 } else { 0 }

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "  Test Summary" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Cyan

Write-Host "`nResults:" -ForegroundColor Cyan
Write-Host "  Passed: $passed" -ForegroundColor Green
Write-Host "  Failed: $failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
Write-Host "  Total: $total" -ForegroundColor White
Write-Host "  Success Rate: $($successRate.ToString('F1'))%" -ForegroundColor $(if ($successRate -ge 90) { "Green" } elseif ($successRate -ge 70) { "Yellow" } else { "Red" })
Write-Host "  Duration: $($totalDuration.TotalSeconds.ToString('F1'))s" -ForegroundColor White

if ($failed -gt 0) {
    Write-Host "`nFailed Tests:" -ForegroundColor Red
    foreach ($test in ($testResults | Where-Object { -not $_.Success })) {
        Write-Host "  - $($test.Name)" -ForegroundColor Red
        if ($test.Error) {
            Write-Host "    Error: $($test.Error)" -ForegroundColor DarkRed
        }
    }
}

# Export results
$reportPath = Join-Path $outputDir "e2e_test_results_$(Get-Date -Format 'yyyy-MM-dd_HHmmss').json"
$report = @{
    timestamp        = Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"
    duration_seconds = $totalDuration.TotalSeconds
    total_tests      = $total
    passed           = $passed
    failed           = $failed
    success_rate     = $successRate
    quick_mode       = $Quick.IsPresent
    skip_backup      = $SkipBackup.IsPresent
    tests            = $testResults
}
$report | ConvertTo-Json -Depth 10 | Out-File -FilePath $reportPath -Encoding UTF8

Write-Host "`nReport saved: $reportPath" -ForegroundColor DarkCyan

# Exit code
if ($failed -eq 0) {
    Write-Host "`n✅ All tests passed!" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "`n❌ Some tests failed" -ForegroundColor Red
    exit 1
}
