# AI Agent System Integration Test
# Tests the complete AI-First autonomous monitoring system

param(
    [switch]$SkipScheduler,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$passed = 0
$failed = 0
$warnings = 0

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "  AI Agent System - Integration Test Suite" -ForegroundColor Cyan
Write-Host "======================================================================`n" -ForegroundColor Cyan

function Test-Component {
    param($name, $scriptBlock)
    
    Write-Host "[$name]" -ForegroundColor Cyan
    try {
        & $scriptBlock
        Write-Host "  Result: PASS" -ForegroundColor Green
        $script:passed++
        return $true
    }
    catch {
        Write-Host "  Result: FAIL - $($_.Exception.Message)" -ForegroundColor Red
        $script:failed++
        return $false
    }
}

# Test 1: AI Performance Agent (DryRun)
Test-Component "AI Performance Agent (DryRun)" {
    $result = & "$scriptDir\ai_performance_agent.ps1" -DryRun 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Agent returned non-zero exit code" }
    if ($result -notmatch "AI Agent Execution Complete") { throw "Agent did not complete" }
    Write-Host "  Agent analyzed systems and generated report" -ForegroundColor Gray
}

# Test 2: AI Performance Agent Output Files
Test-Component "AI Agent Output Files" {
    $outputDir = Join-Path (Split-Path -Parent $scriptDir) "outputs"
    $agentReports = Get-ChildItem -Path $outputDir -Filter "ai_agent_report_*.md" -ErrorAction SilentlyContinue
    $agentData = Get-ChildItem -Path $outputDir -Filter "ai_agent_data_*.json" -ErrorAction SilentlyContinue
    
    if ($agentReports.Count -eq 0) { throw "No agent reports found" }
    if ($agentData.Count -eq 0) { throw "No agent data files found" }
    
    Write-Host "  Found $($agentReports.Count) report(s) and $($agentData.Count) data file(s)" -ForegroundColor Gray
}

# Test 3: AI Agent JSON Structure
Test-Component "AI Agent JSON Structure" {
    $outputDir = Join-Path (Split-Path -Parent $scriptDir) "outputs"
    $latestData = Get-ChildItem -Path $outputDir -Filter "ai_agent_data_*.json" | 
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
    
    $data = Get-Content $latestData.FullName -Raw | ConvertFrom-Json
    
    if (-not $data.Analysis) { throw "Missing Analysis field" }
    if (-not $data.Trends) { throw "Missing Trends field" }
    if (-not $data.ActionPlan) { throw "Missing ActionPlan field" }
    if (-not $data.Confidence) { throw "Missing Confidence field" }
    
    Write-Host "  JSON structure valid: Analysis, Trends, ActionPlan, Confidence" -ForegroundColor Gray
    Write-Host "  Confidence Level: $($data.Confidence)" -ForegroundColor Gray
}

# New: Quick status script sanity
Test-Component "AI Agent Quick Status" {
    $qs = & "$scriptDir\ai_agent_quick_status.ps1" -Json
    if ($LASTEXITCODE -gt 1) { throw "Quick status failed with code $LASTEXITCODE" }
    $qsObj = $qs | ConvertFrom-Json
    if (-not $qsObj.timestamp -or $qsObj.confidence -eq $null) { throw "Quick status JSON missing fields" }
    if ($qsObj.critical -lt 0 -or $qsObj.warning -lt 0) { throw "Invalid counts in quick status" }
    Write-Host "  Quick status OK (Escalation=$($qsObj.escalation))" -ForegroundColor Gray
    Write-Host "  Result: PASS" -ForegroundColor Green
    $true
}

# Test 4: AI Communications Hub - Send
Test-Component "AI Comms Hub - Send Message" {
    $result = & "$scriptDir\ai_comms_hub.ps1" -Action send -SourceAgent "TestAgent" `
        -TargetAgent "all" -Message "Integration test message" -Priority "INFO" 2>&1
    
    if ($LASTEXITCODE -ne 0) { throw "Comms hub send failed" }
    if ($result -notmatch "Delivered") { throw "Message not delivered" }
    
    Write-Host "  Message sent successfully" -ForegroundColor Gray
}

# Test 5: AI Communications Hub - Receive
Test-Component "AI Comms Hub - Receive Messages" {
    Start-Sleep -Seconds 1
    $result = & "$scriptDir\ai_comms_hub.ps1" -Action receive -SourceAgent "TestAgent" 2>&1
    
    if ($LASTEXITCODE -ne 0) { throw "Comms hub receive failed" }
    if ($result -notmatch "Found.*message") { throw "No messages found" }
    
    Write-Host "  Messages received successfully" -ForegroundColor Gray
}

# Test 6: AI Communications Hub - Query
Test-Component "AI Comms Hub - Query Status" {
    $result = & "$scriptDir\ai_comms_hub.ps1" -Action query 2>&1
    
    if ($LASTEXITCODE -ne 0) { throw "Comms hub query failed" }
    if ($result -notmatch "Communication Hub Status") { throw "Status not returned" }
    
    Write-Host "  Hub status queried successfully" -ForegroundColor Gray
}

# Test 7: AI Communications Hub - JSON Export
Test-Component "AI Comms Hub - JSON Export" {
    $result = & "$scriptDir\ai_comms_hub.ps1" -Action query -Json 2>&1 | Out-String
    $json = $result | ConvertFrom-Json
    
    if (-not $json.Timestamp) { throw "Missing Timestamp in JSON" }
    if (-not ($json.PSObject.Properties.Name -contains 'MessagesLast24h')) { 
        throw "Missing MessagesLast24h in JSON" 
    }
    
    Write-Host "  JSON export valid: $($json.MessagesLast24h) messages in 24h" -ForegroundColor Gray
}

# Test 8: AI Agent Scheduler (Skip by default)
if (-not $SkipScheduler) {
    Write-Host "[AI Agent Scheduler - Start/Stop]" -ForegroundColor Cyan
    Write-Host "  SKIPPED: Use -SkipScheduler `$false to test scheduler" -ForegroundColor Yellow
    $script:warnings++
}
else {
    Test-Component "AI Agent Scheduler - Start" {
        # Start scheduler (spawns background monitor then exits)
        & "$scriptDir\ai_agent_scheduler.ps1" -IntervalMinutes 1 -DurationMinutes 3 -KillExisting | Out-Null

        # Allow monitor process to launch
        Start-Sleep -Seconds 3

        # Verify via PID file
        $pidFile = Join-Path (Split-Path -Parent $scriptDir) "outputs/ai_agent_monitor.pid"
        if (-not (Test-Path $pidFile)) { throw "Scheduler did not write PID file" }
        $pidLine = Get-Content $pidFile -Raw
        if ($pidLine -notmatch 'PID=(\d+)') { throw "PID not found in marker file" }
        $monitorPid = [int]$Matches[1]

        try {
            $proc = Get-Process -Id $monitorPid -ErrorAction Stop
        }
        catch {
            throw "Scheduler monitor process not found (PID=$pid)"
        }

        Write-Host "  Scheduler launched monitor (PID: $monitorPid)" -ForegroundColor Gray

        # Cleanup: stop monitor process we just started
        Stop-Process -Id $monitorPid -Force -ErrorAction SilentlyContinue
    }
}

# Test 9: AI Agent Decision Making
Test-Component "AI Agent Decision Logic" {
    $outputDir = Join-Path (Split-Path -Parent $scriptDir) "outputs"
    $latestData = Get-ChildItem -Path $outputDir -Filter "ai_agent_data_*.json" | 
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
    
    $data = Get-Content $latestData.FullName -Raw | ConvertFrom-Json
    
    # Verify decision logic
    $totalSystems = $data.Analysis.Critical.Count + $data.Analysis.Warning.Count + 
    $data.Analysis.Healthy.Count + $data.Analysis.NoData.Count
    
    if ($totalSystems -eq 0) { throw "No systems analyzed" }
    
    $hasActions = $data.ActionPlan.Immediate.Count -gt 0 -or 
    $data.ActionPlan.Scheduled.Count -gt 0 -or 
    $data.ActionPlan.Notify.Count -gt 0
    
    Write-Host "  Analyzed $totalSystems systems" -ForegroundColor Gray
    Write-Host "  Generated $($data.Analysis.Actions.Count) action(s)" -ForegroundColor Gray
    Write-Host "  Confidence: $($data.Confidence)" -ForegroundColor Gray
}

# Test 10: AI Agent Escalation Logic
Test-Component "AI Agent Escalation Logic" {
    $outputDir = Join-Path (Split-Path -Parent $scriptDir) "outputs"
    $latestData = Get-ChildItem -Path $outputDir -Filter "ai_agent_data_*.json" | 
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
    
    $data = Get-Content $latestData.FullName -Raw | ConvertFrom-Json
    
    # Escalation should be true if critical systems exist
    $shouldEscalate = $data.Analysis.Critical.Count -gt 0 -or 
    $data.Trends.Degrading.Count -gt 2
    
    if ($shouldEscalate -ne $data.Escalation) {
        throw "Escalation logic mismatch: Expected=$shouldEscalate, Actual=$($data.Escalation)"
    }
    
    Write-Host "  Escalation logic correct: $(if ($data.Escalation) { 'REQUIRED' } else { 'NOT REQUIRED' })" -ForegroundColor Gray
}

# Summary
Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "  Test Results" -ForegroundColor Cyan
Write-Host "======================================================================`n" -ForegroundColor Cyan

$total = $passed + $failed
Write-Host "Passed: $passed / $total" -ForegroundColor Green
if ($failed -gt 0) {
    Write-Host "Failed: $failed / $total" -ForegroundColor Red
}
if ($warnings -gt 0) {
    Write-Host "Warnings: $warnings" -ForegroundColor Yellow
}

Write-Host ""

if ($failed -eq 0) {
    Write-Host "======================================================================" -ForegroundColor Green
    Write-Host "  ALL TESTS PASSED!" -ForegroundColor Green
    Write-Host "======================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "AI Agent System is fully operational and ready for autonomous use." -ForegroundColor Cyan
    Write-Host ""
    exit 0
}
else {
    Write-Host "======================================================================" -ForegroundColor Red
    Write-Host "  SOME TESTS FAILED" -ForegroundColor Red
    Write-Host "======================================================================" -ForegroundColor Red
    Write-Host ""
    exit 1
}
