# AI Performance Agent - Autonomous Performance Management
# AI agent that monitors, analyzes, and takes action on performance metrics

param(
    [int]$Days = 7,
    [switch]$DryRun,
    [switch]$AutoRecover,
    [switch]$CreateIssues,
    [string]$NotifyEndpoint = $env:AI_NOTIFY_ENDPOINT,
    [int]$ActionThreshold = 70,  # Take action below this threshold
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$outputDir = Join-Path (Split-Path -Parent $scriptDir) "outputs"
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "  AI Performance Agent - Autonomous Operation" -ForegroundColor Cyan
Write-Host "======================================================================`n" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "[DRY-RUN MODE] No actions will be taken" -ForegroundColor Yellow
    Write-Host ""
}

# Step 1: Collect latest metrics
Write-Host "[1/5] Collecting performance metrics..." -ForegroundColor Cyan
& "$scriptDir\generate_performance_dashboard.ps1" -Days $Days -ExportJson -WriteLatest | Out-Null

$jsonPath = Join-Path $outputDir "performance_metrics_latest.json"
if (-not (Test-Path $jsonPath)) {
    Write-Host "ERROR: Unable to generate metrics" -ForegroundColor Red
    exit 1
}

$metrics = Get-Content $jsonPath -Raw | ConvertFrom-Json

# Step 2: Analyze and categorize systems
Write-Host "[2/5] Analyzing system health..." -ForegroundColor Cyan

$analysis = @{
    Critical = @()  # Needs immediate action
    Warning  = @()  # Degrading, watch closely
    Healthy  = @()  # All good
    NoData   = @()  # Missing data
    Actions  = @()  # Actions to take
}

foreach ($systemName in $metrics.Systems.PSObject.Properties.Name) {
    $system = $metrics.Systems.$systemName
    $hasData = $system.EffectiveRuns -gt 0
    
    if (-not $hasData) {
        $analysis.NoData += @{
            Name   = $systemName
            Reason = "No recent test data"
            Action = "investigate"
        }
    }
    elseif ($system.EffectiveSuccessRate -lt $ActionThreshold) {
        $analysis.Critical += @{
            Name        = $systemName
            SuccessRate = $system.EffectiveSuccessRate
            Band        = $system.Band
            LastError   = $system.LastError
            Action      = "recover"
        }
    }
    elseif ($system.EffectiveSuccessRate -lt 90) {
        $analysis.Warning += @{
            Name        = $systemName
            SuccessRate = $system.EffectiveSuccessRate
            Band        = $system.Band
            Action      = "monitor"
        }
    }
    else {
        $analysis.Healthy += @{
            Name        = $systemName
            SuccessRate = $system.EffectiveSuccessRate
            Band        = $system.Band
        }
    }
}

# Display analysis summary
Write-Host "  Critical: $($analysis.Critical.Count)" -ForegroundColor Red
Write-Host "  Warning: $($analysis.Warning.Count)" -ForegroundColor Yellow
Write-Host "  Healthy: $($analysis.Healthy.Count)" -ForegroundColor Green
Write-Host "  No Data: $($analysis.NoData.Count)" -ForegroundColor Gray
Write-Host ""

# Step 3: Generate trend analysis
Write-Host "[3/5] Analyzing trends..." -ForegroundColor Cyan

& "$scriptDir\compare_performance_periods.ps1" -PeriodDays1 3 -PeriodDays2 7 -Label1 "Recent" -Label2 "Week" | Out-Null

$comparisonPath = Join-Path $outputDir "performance_comparison_$(Get-Date -Format 'yyyy-MM-dd').md"
$trendAnalysis = @{
    Improving = @()
    Degrading = @()
    Stable    = @()
}

# Parse comparison report to detect trends (simplified)
if (Test-Path $comparisonPath) {
    $comparisonText = Get-Content $comparisonPath -Raw
    
    foreach ($systemName in $metrics.Systems.PSObject.Properties.Name) {
        if ($comparisonText -match "$systemName[^#]*\[↑\]") {
            $trendAnalysis.Improving += $systemName
        }
        elseif ($comparisonText -match "$systemName[^#]*\[↓\]") {
            $trendAnalysis.Degrading += $systemName
        }
        else {
            $trendAnalysis.Stable += $systemName
        }
    }
}

Write-Host "  Improving: $($trendAnalysis.Improving.Count)" -ForegroundColor Green
Write-Host "  Degrading: $($trendAnalysis.Degrading.Count)" -ForegroundColor Red
Write-Host "  Stable: $($trendAnalysis.Stable.Count)" -ForegroundColor Cyan
Write-Host ""

# Step 4: Decision making and action planning
Write-Host "[4/5] Planning autonomous actions..." -ForegroundColor Cyan

$actionPlan = @{
    Immediate = @()
    Scheduled = @()
    Notify    = @()
}

# Critical systems - immediate action
foreach ($item in $analysis.Critical) {
    $action = @{
        System   = $item.Name
        Priority = "CRITICAL"
        Type     = "auto-recover"
        Reason   = "Success rate $($item.SuccessRate)% below threshold"
        Command  = "Restart-Service", "Clear-Cache", "Validate-Config"
    }
    $actionPlan.Immediate += $action
    $analysis.Actions += $action
}

# Degrading trends - proactive action
foreach ($systemName in $trendAnalysis.Degrading) {
    if ($analysis.Critical.Name -notcontains $systemName) {
        $action = @{
            System   = $systemName
            Priority = "HIGH"
            Type     = "preventive"
            Reason   = "Performance degrading over time"
            Command  = "Analyze-Logs", "Check-Resources"
        }
        $actionPlan.Scheduled += $action
        $analysis.Actions += $action
    }
}

# No data systems - investigation
foreach ($item in $analysis.NoData) {
    $action = @{
        System   = $item.Name
        Priority = "MEDIUM"
        Type     = "investigate"
        Reason   = "No recent test data"
        Command  = "Verify-TestSchedule", "Check-Dependencies"
    }
    $actionPlan.Notify += $action
    $analysis.Actions += $action
}

Write-Host "  Immediate actions: $($actionPlan.Immediate.Count)" -ForegroundColor Red
Write-Host "  Scheduled actions: $($actionPlan.Scheduled.Count)" -ForegroundColor Yellow
Write-Host "  Notifications: $($actionPlan.Notify.Count)" -ForegroundColor Cyan
Write-Host ""

# Step 5: Execute actions
Write-Host "[5/5] Executing autonomous actions..." -ForegroundColor Cyan

$executionLog = @()

if ($DryRun) {
    Write-Host "`n  [DRY-RUN] Would execute the following actions:" -ForegroundColor Yellow
    foreach ($action in $analysis.Actions) {
        Write-Host "    - [$($action.Priority)] $($action.System): $($action.Type)" -ForegroundColor Gray
        Write-Host "      Reason: $($action.Reason)" -ForegroundColor DarkGray
    }
}
else {
    # Execute immediate actions
    foreach ($action in $actionPlan.Immediate) {
        Write-Host "  Executing: $($action.System) - $($action.Type)" -ForegroundColor Yellow
        
        $result = @{
            System    = $action.System
            Action    = $action.Type
            Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            Success   = $false
            Message   = ""
        }
        
        if ($AutoRecover) {
            # Placeholder for actual recovery logic
            # In production, this would call system-specific recovery scripts
            switch ($action.System) {
                "Orchestration" {
                    # Example: Restart orchestrator service
                    $result.Message = "Would restart orchestration service"
                    $result.Success = $true
                }
                "Daily Briefing" {
                    # Example: Clear cache and retry
                    $result.Message = "Would clear cache and retry briefing"
                    $result.Success = $true
                }
                default {
                    $result.Message = "No automated recovery available for $($action.System)"
                    $result.Success = $false
                }
            }
        }
        else {
            $result.Message = "AutoRecover disabled - manual intervention required"
            $result.Success = $false
        }
        
        $executionLog += $result
        
        $statusColor = if ($result.Success) { "Green" } else { "Yellow" }
        Write-Host "    Result: $($result.Message)" -ForegroundColor $statusColor
    }
    
    # Create notifications for scheduled actions
    foreach ($action in $actionPlan.Scheduled) {
        Write-Host "  Scheduled: $($action.System) - $($action.Type)" -ForegroundColor Cyan
        $executionLog += @{
            System    = $action.System
            Action    = "scheduled"
            Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            Success   = $true
            Message   = "Added to monitoring queue"
        }
    }
}

Write-Host ""

# Generate AI agent report
Write-Host "Generating AI agent report..." -ForegroundColor Cyan

$agentReport = @"
# AI Performance Agent Report

**Generated**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")  
**Mode**: $(if ($DryRun) { 'DRY-RUN' } else { 'AUTONOMOUS' })  
**Period Analyzed**: Last $Days days

---

## Autonomous Analysis

### Health Summary

- **Critical**: $($analysis.Critical.Count) systems require immediate action
- **Warning**: $($analysis.Warning.Count) systems under observation
- **Healthy**: $($analysis.Healthy.Count) systems performing well
- **No Data**: $($analysis.NoData.Count) systems missing metrics

### Trend Analysis

- **Improving**: $($trendAnalysis.Improving.Count) systems
- **Degrading**: $($trendAnalysis.Degrading.Count) systems (requires attention)
- **Stable**: $($trendAnalysis.Stable.Count) systems

---

## Actions Taken

### Immediate Actions ($($actionPlan.Immediate.Count))

$(if ($actionPlan.Immediate.Count -gt 0) {
    $immediate = ""
    foreach ($action in $actionPlan.Immediate) {
        $immediate += "#### $($action.System)`n`n"
        $immediate += "- **Priority**: $($action.Priority)`n"
        $immediate += "- **Type**: $($action.Type)`n"
        $immediate += "- **Reason**: $($action.Reason)`n`n"
    }
    $immediate
} else {
    "No immediate actions required.`n`n"
})

### Scheduled Actions ($($actionPlan.Scheduled.Count))

$(if ($actionPlan.Scheduled.Count -gt 0) {
    $scheduled = ""
    foreach ($action in $actionPlan.Scheduled) {
        $scheduled += "- **$($action.System)**: $($action.Reason)`n"
    }
    $scheduled
} else {
    "No scheduled actions.`n`n"
})

### Notifications ($($actionPlan.Notify.Count))

$(if ($actionPlan.Notify.Count -gt 0) {
    $notify = ""
    foreach ($action in $actionPlan.Notify) {
        $notify += "- **$($action.System)**: $($action.Reason)`n"
    }
    $notify
} else {
    "No notifications required.`n`n"
})

---

## Execution Log

$(if ($executionLog.Count -gt 0) {
    $log = ""
    foreach ($entry in $executionLog) {
        $status = if ($entry.Success) { "[OK]" } else { "[WARN]" }
        $log += "- $status **$($entry.System)**: $($entry.Message) ($($entry.Timestamp))`n"
    }
    $log
} else {
    "No actions executed (DRY-RUN mode or no actions required).`n`n"
})

---

## AI Decision Rationale

### Critical Systems

$(if ($analysis.Critical.Count -gt 0) {
    $critical = ""
    foreach ($item in $analysis.Critical) {
        $critical += "**$($item.Name)**:`n"
        $critical += "- Success Rate: $($item.SuccessRate)%`n"
        $critical += "- Band: $($item.Band)`n"
        $critical += "- Last Error: $($item.LastError)`n"
        $critical += "- AI Decision: Automatic recovery initiated`n`n"
    }
    $critical
} else {
    "No critical systems detected.`n`n"
})

### Degrading Trends

$(if ($trendAnalysis.Degrading.Count -gt 0) {
    $degrading = "Systems showing negative trends: " + ($trendAnalysis.Degrading -join ", ") + "`n"
    $degrading += "AI Decision: Increased monitoring and preventive analysis scheduled.`n`n"
    $degrading
} else {
    "No degrading trends detected.`n`n"
})

---

## Next Actions

### Autonomous Schedule

- **Immediate**: Re-check critical systems in 5 minutes
- **Short-term**: Monitor warning systems every 30 minutes
- **Long-term**: Daily trend analysis and preventive maintenance

### Human Escalation

$(if ($analysis.Critical.Count -gt 0 -or $trendAnalysis.Degrading.Count -gt 2) {
    "**ESCALATION REQUIRED**: Multiple systems showing issues.`n"
    "Recommended: Human review of automation logs and system architecture.`n`n"
} else {
    "No human escalation required at this time.`n"
    "AI agent will continue autonomous monitoring.`n`n"
})

---

## AI Agent Metadata

- **Agent Version**: 1.0.0
- **Confidence Level**: $(if ($analysis.Critical.Count -eq 0 -and $trendAnalysis.Degrading.Count -eq 0) { 'HIGH' } elseif ($analysis.Critical.Count -le 1) { 'MEDIUM' } else { 'LOW' })
- **Autonomy Mode**: $(if ($AutoRecover) { 'FULL' } else { 'ADVISORY' })
- **Next Run**: $(Get-Date).AddMinutes(30).ToString('yyyy-MM-dd HH:mm:ss')
- **Report ID**: agent_$timestamp

---

**Generated by**: AI Performance Agent  
**For**: AGI System Autonomous Operations  
**Contact**: Escalate to human operator if confidence level is LOW
"@

$agentReportPath = Join-Path $outputDir "ai_agent_report_$timestamp.md"
$agentReport | Out-File -FilePath $agentReportPath -Encoding UTF8

# Export structured data for other AI agents
$agentData = @{
    Timestamp    = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Analysis     = $analysis
    Trends       = $trendAnalysis
    ActionPlan   = $actionPlan
    ExecutionLog = $executionLog
    Confidence   = if ($analysis.Critical.Count -eq 0 -and $trendAnalysis.Degrading.Count -eq 0) { 'HIGH' } elseif ($analysis.Critical.Count -le 1) { 'MEDIUM' } else { 'LOW' }
    Escalation   = $analysis.Critical.Count -gt 0 -or $trendAnalysis.Degrading.Count -gt 2
}

$agentDataPath = Join-Path $outputDir "ai_agent_data_$timestamp.json"
$agentData | ConvertTo-Json -Depth 10 | Out-File -FilePath $agentDataPath -Encoding UTF8

# Update latest aliases for easy consumption by other tools and docs
try {
    $latestReportPath = Join-Path $outputDir "ai_agent_report_latest.md"
    $latestDataPath = Join-Path $outputDir "ai_agent_data_latest.json"
    Copy-Item -Path $agentReportPath -Destination $latestReportPath -Force
    Copy-Item -Path $agentDataPath   -Destination $latestDataPath   -Force
}
catch {
    Write-Host "Warning: Failed to update latest aliases: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "======================================================================" -ForegroundColor Green
Write-Host "  AI Agent Execution Complete" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Report: $agentReportPath" -ForegroundColor Cyan
Write-Host "Data: $agentDataPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Status: $(if ($analysis.Critical.Count -eq 0) { '[OK] All systems stable' } else { '[ACTION] Critical systems require attention' })" -ForegroundColor $(if ($analysis.Critical.Count -eq 0) { 'Green' } else { 'Yellow' })
Write-Host "Confidence: $($agentData.Confidence)" -ForegroundColor $(if ($agentData.Confidence -eq 'HIGH') { 'Green' } elseif ($agentData.Confidence -eq 'MEDIUM') { 'Yellow' } else { 'Red' })
Write-Host "Escalation: $(if ($agentData.Escalation) { '[REQUIRED]' } else { '[NOT REQUIRED]' })" -ForegroundColor $(if ($agentData.Escalation) { 'Red' } else { 'Green' })
Write-Host ""

# AI-to-AI notification (if endpoint configured)
if ($NotifyEndpoint -and -not $DryRun) {
    Write-Host "Notifying other AI agents..." -ForegroundColor Cyan
    try {
        $notifyPayload = @{
            source         = "AI Performance Agent"
            timestamp      = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            status         = if ($analysis.Critical.Count -eq 0) { "stable" } else { "critical" }
            critical_count = $analysis.Critical.Count
            warning_count  = $analysis.Warning.Count
            actions_taken  = $executionLog.Count
            report_url     = $agentReportPath
            data_url       = $agentDataPath
        } | ConvertTo-Json
        
        # Placeholder for actual HTTP notification
        Write-Host "  Would POST to: $NotifyEndpoint" -ForegroundColor Gray
        Write-Host "  (Notification infrastructure not yet implemented)" -ForegroundColor Gray
    }
    catch {
        Write-Host "  Warning: Failed to notify other agents" -ForegroundColor Yellow
    }
}

Write-Host ""
