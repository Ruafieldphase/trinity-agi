# 24-Hour Stability Monitoring Setup
# ====================================
# 
# Creates baseline snapshot and sets up 24-hour stability check
# 
# Usage:
#   .\scripts\monitor_stability_24h.ps1 -Action Baseline    # Take baseline snapshot
#   .\scripts\monitor_stability_24h.ps1 -Action Check       # Check after 24h
#   .\scripts\monitor_stability_24h.ps1 -Action Report      # Generate comparison report

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("Baseline", "Check", "Report")]
    [string]$Action,
    
    [string]$OutputDir = "outputs"
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptRoot

$OutputPath = Join-Path $RootDir $OutputDir
if (-not (Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
}

$BaselineFile = Join-Path $OutputPath "stability_baseline.json"
$CheckFile = Join-Path $OutputPath "stability_check_$(Get-Date -Format 'yyyy-MM-dd_HHmm').json"
$ReportFile = Join-Path $OutputPath "stability_report_$(Get-Date -Format 'yyyy-MM-dd').md"

function Get-SystemSnapshot {
    Write-Host "📸 Capturing system snapshot..." -ForegroundColor Cyan
    
    $Snapshot = @{
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        UnixTime  = [DateTimeOffset]::Now.ToUnixTimeSeconds()
    }
    
    # 1. AGI Status
    Write-Host "   Checking AGI status..." -ForegroundColor Gray
    try {
        $agiStatus = & "$RootDir\scripts\quick_status.ps1" 2>&1 | Out-String
        
        # Parse key metrics from output
        $Snapshot.AGI = @{
            Status    = if ($agiStatus -match "HEALTHY") { "HEALTHY" } else { "UNHEALTHY" }
            RawOutput = $agiStatus
        }
        
        # Extract metrics
        if ($agiStatus -match "Confidence:\s+([\d.]+)") {
            $Snapshot.AGI.Confidence = [double]$matches[1]
        }
        if ($agiStatus -match "Quality:\s+([\d.]+)") {
            $Snapshot.AGI.Quality = [double]$matches[1]
        }
        if ($agiStatus -match "2nd Pass:\s+([\d.]+)") {
            $Snapshot.AGI.SecondPass = [double]$matches[1]
        }
    }
    catch {
        $Snapshot.AGI = @{ Status = "ERROR"; Error = $_.Exception.Message }
    }
    
    # 2. Recent ledger events (last 100)
    Write-Host "   Analyzing recent events..." -ForegroundColor Gray
    $LedgerPath = Join-Path $RootDir "fdo_agi_repo\memory\resonance_ledger.jsonl"
    if (Test-Path $LedgerPath) {
        $RecentLines = Get-Content $LedgerPath | Select-Object -Last 100
        $RecentEvents = @()
        $SuccessCount = 0
        $ReplanCount = 0
        $QualityScores = @()
        
        foreach ($line in $RecentLines) {
            try {
                $event = $line | ConvertFrom-Json
                $RecentEvents += $event
                
                if ($event.event -eq "eval" -and $event.quality) {
                    $QualityScores += $event.quality
                }
                if ($event.event -eq "rune" -and $event.rune.replan -eq $true) {
                    $ReplanCount++
                }
            }
            catch {
                # Skip invalid lines
            }
        }
        
        $Snapshot.RecentActivity = @{
            TotalEvents = $RecentEvents.Count
            ReplanCount = $ReplanCount
            AvgQuality  = if ($QualityScores.Count -gt 0) { 
                [math]::Round(($QualityScores | Measure-Object -Average).Average, 3) 
            }
            else { 0 }
        }
    }
    
    # 3. System resources
    Write-Host "   Collecting resource metrics..." -ForegroundColor Gray
    try {
        $cpu = Get-WmiObject Win32_Processor | Measure-Object -Property LoadPercentage -Average
        $mem = Get-WmiObject Win32_OperatingSystem
        
        $Snapshot.Resources = @{
            CPU           = [math]::Round($cpu.Average, 1)
            MemoryUsedGB  = [math]::Round(($mem.TotalVisibleMemorySize - $mem.FreePhysicalMemory) / 1MB, 2)
            MemoryTotalGB = [math]::Round($mem.TotalVisibleMemorySize / 1MB, 2)
            MemoryPercent = [math]::Round((($mem.TotalVisibleMemorySize - $mem.FreePhysicalMemory) / $mem.TotalVisibleMemorySize) * 100, 1)
        }
    }
    catch {
        $Snapshot.Resources = @{ Error = $_.Exception.Message }
    }
    
    # 4. Port status
    Write-Host "   Checking port 18090..." -ForegroundColor Gray
    try {
        $portCheck = netstat -ano | Select-String "18090" | Select-Object -First 1
        $Snapshot.Port18090 = if ($portCheck) { "LISTENING" } else { "DOWN" }
    }
    catch {
        $Snapshot.Port18090 = "ERROR"
    }
    
    # 5. Background jobs
    Write-Host "   Checking background jobs..." -ForegroundColor Gray
    $jobs = Get-Job
    $Snapshot.BackgroundJobs = @{
        Total   = $jobs.Count
        Running = ($jobs | Where-Object { $_.State -eq "Running" }).Count
        Failed  = ($jobs | Where-Object { $_.State -eq "Failed" }).Count
        Jobs    = $jobs | Select-Object Id, Name, State | ForEach-Object { 
            @{ Id = $_.Id; Name = $_.Name; State = $_.State.ToString() }
        }
    }
    
    # 6. File counts
    Write-Host "   Counting files..." -ForegroundColor Gray
    $Snapshot.Files = @{
        BatchValidations = (Get-ChildItem "$OutputPath\batch_validation_*.json" -ErrorAction SilentlyContinue).Count
        WeeklyReports    = (Get-ChildItem "$OutputPath\weekly_report_*.md" -ErrorAction SilentlyContinue).Count
        Dashboards       = (Get-ChildItem "$OutputPath\agi_performance_dashboard.html" -ErrorAction SilentlyContinue).Count
    }
    
    return $Snapshot
}

function Compare-Snapshots {
    param(
        [hashtable]$Baseline,
        [hashtable]$Current
    )
    
    Write-Host "[INFO] Comparing snapshots..." -ForegroundColor Cyan
    
    $Comparison = @{
        TimeDiff  = @{
            Hours        = [math]::Round(($Current.UnixTime - $Baseline.UnixTime) / 3600, 1)
            BaselineTime = $Baseline.Timestamp
            CurrentTime  = $Current.Timestamp
        }
        AGI       = @{}
        Resources = @{}
        Activity  = @{}
        Issues    = @()
        Warnings  = @()
    }
    
    # Compare AGI status
    if ($Baseline.AGI.Status -ne $Current.AGI.Status) {
        $Comparison.Issues += "AGI Status changed: $($Baseline.AGI.Status) -> $($Current.AGI.Status)"
    }
    
    if ($Baseline.AGI.Quality -and $Current.AGI.Quality) {
        $qualityDiff = [math]::Round($Current.AGI.Quality - $Baseline.AGI.Quality, 3)
        $Comparison.AGI.QualityChange = $qualityDiff
        if ([math]::Abs($qualityDiff) -gt 0.1) {
            $Comparison.Warnings += "Quality changed by $qualityDiff"
        }
    }
    
    if ($Baseline.AGI.Confidence -and $Current.AGI.Confidence) {
        $confDiff = [math]::Round($Current.AGI.Confidence - $Baseline.AGI.Confidence, 3)
        $Comparison.AGI.ConfidenceChange = $confDiff
        if ([math]::Abs($confDiff) -gt 0.1) {
            $Comparison.Warnings += "Confidence changed by $confDiff"
        }
    }
    
    # Compare resources
    if ($Baseline.Resources.CPU -and $Current.Resources.CPU) {
        $cpuDiff = [math]::Round($Current.Resources.CPU - $Baseline.Resources.CPU, 1)
        $Comparison.Resources.CPUChange = $cpuDiff
        if ([math]::Abs($cpuDiff) -gt 20) {
            $Comparison.Warnings += "CPU usage changed significantly: ${cpuDiff}%"
        }
    }
    
    if ($Baseline.Resources.MemoryPercent -and $Current.Resources.MemoryPercent) {
        $memDiff = [math]::Round($Current.Resources.MemoryPercent - $Baseline.Resources.MemoryPercent, 1)
        $Comparison.Resources.MemoryChange = $memDiff
        if ([math]::Abs($memDiff) -gt 10) {
            $Comparison.Warnings += "Memory usage changed: ${memDiff}%"
        }
    }
    
    # Compare activity
    if ($Baseline.RecentActivity -and $Current.RecentActivity) {
        $Comparison.Activity.EventsBaseline = $Baseline.RecentActivity.TotalEvents
        $Comparison.Activity.EventsCurrent = $Current.RecentActivity.TotalEvents
        $Comparison.Activity.ReplanBaseline = $Baseline.RecentActivity.ReplanCount
        $Comparison.Activity.ReplanCurrent = $Current.RecentActivity.ReplanCount
    }
    
    # Port check
    if ($Baseline.Port18090 -ne $Current.Port18090) {
        $Comparison.Issues += "Port 18090 status changed: $($Baseline.Port18090) -> $($Current.Port18090)"
    }
    
    # Background jobs
    if ($Baseline.BackgroundJobs.Running -ne $Current.BackgroundJobs.Running) {
        $jobDiff = $Current.BackgroundJobs.Running - $Baseline.BackgroundJobs.Running
        $Comparison.Warnings += "Background jobs changed by $jobDiff"
    }
    
    return $Comparison
}

# Main execution
switch ($Action) {
    "Baseline" {
        Write-Host "`n=== Creating 24h Stability Baseline ===" -ForegroundColor Green
        Write-Host ""
        
        $snapshot = Get-SystemSnapshot
        
        # Save baseline
        $snapshot | ConvertTo-Json -Depth 10 | Out-File -FilePath $BaselineFile -Encoding UTF8 -Force
        
        Write-Host "`n[OK] Baseline snapshot created!" -ForegroundColor Green
        Write-Host "   File: $BaselineFile" -ForegroundColor White
        Write-Host ""
        Write-Host "📅 Next steps:" -ForegroundColor Cyan
        Write-Host "   1. Wait 24 hours" -ForegroundColor White
        Write-Host "   2. Run: .\scripts\monitor_stability_24h.ps1 -Action Check" -ForegroundColor Yellow
        Write-Host "   3. Review stability report" -ForegroundColor White
        Write-Host ""
        Write-Host "[TIME] Check time: $((Get-Date).AddHours(24).ToString('yyyy-MM-dd HH:mm'))" -ForegroundColor Gray
    }
    
    "Check" {
        Write-Host "`n=== 24h Stability Check ===" -ForegroundColor Green
        Write-Host ""
        
        if (-not (Test-Path $BaselineFile)) {
            Write-Host "[ERROR] No baseline found! Run with -Action Baseline first." -ForegroundColor Red
            exit 1
        }
        
        # Load baseline
        $baseline = Get-Content $BaselineFile -Raw | ConvertFrom-Json
        Write-Host "📁 Baseline loaded from: $(Get-Date $baseline.Timestamp)" -ForegroundColor Gray
        Write-Host ""
        
        # Get current snapshot
        $current = Get-SystemSnapshot
        
        # Save check snapshot
        $current | ConvertTo-Json -Depth 10 | Out-File -FilePath $CheckFile -Encoding UTF8 -Force
        
        Write-Host "`n[OK] Check snapshot created!" -ForegroundColor Green
        Write-Host "   File: $CheckFile" -ForegroundColor White
        Write-Host ""
        Write-Host "[INFO] Run report generation: .\scripts\monitor_stability_24h.ps1 -Action Report" -ForegroundColor Yellow
    }
    
    "Report" {
        Write-Host "`n=== Generating Stability Report ===" -ForegroundColor Green
        Write-Host ""
        
        if (-not (Test-Path $BaselineFile)) {
            Write-Host "[ERROR] No baseline found!" -ForegroundColor Red
            exit 1
        }
        
        # Find most recent check file
        $checkFiles = Get-ChildItem "$OutputPath\stability_check_*.json" | Sort-Object LastWriteTime -Descending
        if ($checkFiles.Count -eq 0) {
            Write-Host "[ERROR] No check snapshots found! Run with -Action Check first." -ForegroundColor Red
            exit 1
        }
        
        $latestCheck = $checkFiles[0]
        Write-Host "📁 Using check file: $($latestCheck.Name)" -ForegroundColor Gray
        
        # Load data
        $baseline = Get-Content $BaselineFile -Raw | ConvertFrom-Json -AsHashtable
        $current = Get-Content $latestCheck.FullName -Raw | ConvertFrom-Json -AsHashtable
        
        # Compare
        $comparison = Compare-Snapshots -Baseline $baseline -Current $current
        
        # Generate markdown report
        $report = @"
# 24-Hour Stability Report

**Report Date**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")  
**Monitoring Period**: $($comparison.TimeDiff.Hours) hours  
**Baseline**: $($comparison.TimeDiff.BaselineTime)  
**Check**: $($comparison.TimeDiff.CurrentTime)

---

## Executive Summary

**Overall Status**: $(if ($comparison.Issues.Count -eq 0) { "[OK] STABLE" } else { "[WARN] ISSUES DETECTED" })

- **Critical Issues**: $($comparison.Issues.Count)
- **Warnings**: $($comparison.Warnings.Count)
- **Monitoring Duration**: $($comparison.TimeDiff.Hours) hours

---

## AGI Performance

| Metric | Baseline | Current | Change |
|--------|----------|---------|--------|
| **Status** | $($baseline.AGI.Status) | $($current.AGI.Status) | $(if ($baseline.AGI.Status -eq $current.AGI.Status) { "No change" } else { "CHANGED" }) |
| **Quality** | $($baseline.AGI.Quality) | $($current.AGI.Quality) | $($comparison.AGI.QualityChange) |
| **Confidence** | $($baseline.AGI.Confidence) | $($current.AGI.Confidence) | $($comparison.AGI.ConfidenceChange) |

---

## System Resources

| Resource | Baseline | Current | Change |
|----------|----------|---------|--------|
| **CPU Usage** | $($baseline.Resources.CPU)% | $($current.Resources.CPU)% | $($comparison.Resources.CPUChange)% |
| **Memory** | $($baseline.Resources.MemoryPercent)% | $($current.Resources.MemoryPercent)% | $($comparison.Resources.MemoryChange)% |
| **Memory (GB)** | $($baseline.Resources.MemoryUsedGB) / $($baseline.Resources.MemoryTotalGB) | $($current.Resources.MemoryUsedGB) / $($current.Resources.MemoryTotalGB) | - |

---

## Activity Summary

| Metric | Baseline | Current |
|--------|----------|---------|
| **Recent Events** | $($comparison.Activity.EventsBaseline) | $($comparison.Activity.EventsCurrent) |
| **Replan Count** | $($comparison.Activity.ReplanBaseline) | $($comparison.Activity.ReplanCurrent) |
| **Port 18090** | $($baseline.Port18090) | $($current.Port18090) |
| **Background Jobs** | $($baseline.BackgroundJobs.Running) running | $($current.BackgroundJobs.Running) running |

---

## Issues & Warnings

"@

        if ($comparison.Issues.Count -gt 0) {
            $report += "`n### Critical Issues`n`n"
            foreach ($issue in $comparison.Issues) {
                $report += "- [ERROR] $issue`n"
            }
        }
        
        if ($comparison.Warnings.Count -gt 0) {
            $report += "`n### Warnings`n`n"
            foreach ($warning in $comparison.Warnings) {
                $report += "- [WARN] $warning`n"
            }
        }
        
        if ($comparison.Issues.Count -eq 0 -and $comparison.Warnings.Count -eq 0) {
            $report += "`n[OK] **No issues or warnings detected. System is stable.**`n"
        }
        
        $report += @"

---

## Recommendations

"@

        if ($comparison.Issues.Count -gt 0) {
            $report += "- 🔴 **Immediate Action Required**: Review critical issues above`n"
        }
        
        if ($comparison.Warnings.Count -gt 0) {
            $report += "- 🟡 **Monitor Closely**: Track warnings for trends`n"
        }
        
        if ($comparison.Issues.Count -eq 0) {
            $report += "- [OK] System demonstrating good stability`n"
            $report += "- [INFO] Continue monitoring with weekly reports`n"
            $report += "- [RELOAD] Consider extending monitoring to 7 days`n"
        }
        
        $report += @"

---

## Data Files

- **Baseline**: ``$($BaselineFile.Replace($RootDir, ''))``
- **Check**: ``$($latestCheck.FullName.Replace($RootDir, ''))``
- **Report**: ``$($ReportFile.Replace($RootDir, ''))``

---

**Generated by**: AGI Stability Monitor  
**Script**: ``scripts/monitor_stability_24h.ps1``
"@

        # Save report
        $report | Out-File -FilePath $ReportFile -Encoding UTF8 -Force
        
        Write-Host "[OK] Report generated!" -ForegroundColor Green
        Write-Host "   File: $ReportFile" -ForegroundColor White
        Write-Host ""
        
        # Print summary
        if ($comparison.Issues.Count -gt 0) {
            Write-Host "[WARN]  Status: ISSUES DETECTED" -ForegroundColor Yellow
            foreach ($issue in $comparison.Issues) {
                Write-Host "   - $issue" -ForegroundColor Red
            }
        }
        else {
            Write-Host "[OK] Status: STABLE" -ForegroundColor Green
        }
        
        if ($comparison.Warnings.Count -gt 0) {
            Write-Host ""
            Write-Host "Warnings:" -ForegroundColor Yellow
            foreach ($warning in $comparison.Warnings) {
                Write-Host "   - $warning" -ForegroundColor Yellow
            }
        }
        
        Write-Host ""
        Write-Host "📖 Open report: Start-Process '$ReportFile'" -ForegroundColor Gray
    }
}
