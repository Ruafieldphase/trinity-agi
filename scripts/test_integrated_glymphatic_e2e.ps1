#!/usr/bin/env pwsh
#Requires -Version 5.1

<#
.SYNOPSIS
    Integrated E2E Test for Adaptive Glymphatic System
.DESCRIPTION
    Full end-to-end test including:
    - Goal Tracker integration
    - Glymphatic system state
    - Autonomous loops
    - Session continuity
.NOTES
    File: test_integrated_glymphatic_e2e.ps1
    Date: 2025-11-07
#>

[CmdletBinding()]
param(
    [switch]$SkipGoalExecution,
    [switch]$VerboseLog
)

$ErrorActionPreference = 'Stop'
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$script:workspaceRoot = Split-Path -Parent $PSScriptRoot
$script:testResults = @{
    StartTime = Get-Date
    Tests     = @()
    Passed    = 0
    Failed    = 0
}

# Helper functions
function Write-TestHeader {
    param([string]$Title)
    Write-Host "`n$('=' * 60)" -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host "$('=' * 60)`n" -ForegroundColor Cyan
}

function Write-TestStep {
    param([string]$Message)
    Write-Host "  🔍 $Message" -ForegroundColor Yellow
}

function Write-TestPass {
    param([string]$Message)
    Write-Host "  ✅ $Message" -ForegroundColor Green
    $script:testResults.Passed++
}

function Write-TestFail {
    param([string]$Message)
    Write-Host "  ❌ $Message" -ForegroundColor Red
    $script:testResults.Failed++
}

function Invoke-TestCase {
    param(
        [string]$Name,
        [scriptblock]$TestBlock
    )
    
    $test = @{
        Name      = $Name
        StartTime = Get-Date
        Status    = 'unknown'
        Error     = $null
    }
    
    try {
        Write-TestStep $Name
        & $TestBlock
        $test.Status = 'passed'
        Write-TestPass $Name
    }
    catch {
        $test.Status = 'failed'
        $test.Error = $_.Exception.Message
        Write-TestFail "$Name - $($_.Exception.Message)"
    }
    finally {
        $test.Duration = (Get-Date) - $test.StartTime
        $script:testResults.Tests += $test
    }
}

# Test 1: Python environment
Write-TestHeader "Test 1: Python Environment"
Invoke-TestCase "Python executable exists" {
    $pyPath = Join-Path $workspaceRoot 'fdo_agi_repo\.venv\Scripts\python.exe'
    if (-not (Test-Path $pyPath)) {
        throw "Python not found at: $pyPath"
    }
}

# Test 2: Glymphatic state file
Write-TestHeader "Test 2: Glymphatic System State"
Invoke-TestCase "State file exists and is valid" {
    $statePath = Join-Path $workspaceRoot 'fdo_agi_repo\memory\glymphatic_state.json'
    if (-not (Test-Path $statePath)) {
        throw "State file not found: $statePath"
    }
    
    $state = Get-Content $statePath -Raw | ConvertFrom-Json
    if (-not $state.enabled) {
        Write-Host "    ℹ️  System is disabled (expected for testing)" -ForegroundColor Cyan
    }
}

# Test 3: CLI functionality
Write-TestHeader "Test 3: CLI Functionality"
Invoke-TestCase "CLI check command works" {
    $cliPath = Join-Path $workspaceRoot 'scripts\glymphatic_control.ps1'
    $output = & $cliPath check 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "CLI check failed with exit code: $LASTEXITCODE"
    }
}

# Test 4: Goal Tracker integration
Write-TestHeader "Test 4: Goal Tracker Integration"
Invoke-TestCase "Goal tracker file exists" {
    $trackerPath = Join-Path $workspaceRoot 'fdo_agi_repo\memory\goal_tracker.json'
    if (-not (Test-Path $trackerPath)) {
        throw "Goal tracker not found: $trackerPath"
    }
    
    $tracker = Get-Content $trackerPath -Raw | ConvertFrom-Json
    Write-Host "    📊 Total goals: $($tracker.goals.Count)" -ForegroundColor Cyan
    
    $glymphaticGoals = $tracker.goals | Where-Object { 
        $_.title -like "*glymphatic*" -or 
        $_.title -like "*cleanup*" -or
        $_.executable.script -like "*glymphatic*"
    }
    
    if ($glymphaticGoals) {
        Write-Host "    🧠 Glymphatic-related goals: $($glymphaticGoals.Count)" -ForegroundColor Cyan
    }
}

# Test 5: Python module import
Write-TestHeader "Test 5: Python Module Import"
Invoke-TestCase "Can import adaptive_glymphatic module" {
    $pyPath = Join-Path $workspaceRoot 'fdo_agi_repo\.venv\Scripts\python.exe'
    $testScript = @"
import sys
sys.path.insert(0, r'$workspaceRoot\fdo_agi_repo')
from scripts.autonomous.adaptive_glymphatic import AdaptiveGlymphaticSystem
print('SUCCESS')
"@
    
    $output = & $pyPath -c $testScript 2>&1
    if ($output -notcontains 'SUCCESS') {
        throw "Module import failed: $output"
    }
}

# Test 6: Adaptive decision logic
Write-TestHeader "Test 6: Adaptive Decision Logic"
Invoke-TestCase "Decision logic produces valid output" {
    $pyPath = Join-Path $workspaceRoot 'fdo_agi_repo\.venv\Scripts\python.exe'
    $testScript = Join-Path $workspaceRoot 'scripts\test_adaptive_glymphatic.py'
    
    if (-not (Test-Path $testScript)) {
        # Create minimal test script
        $miniTest = @"
import sys
sys.path.insert(0, r'$workspaceRoot\fdo_agi_repo')
from scripts.autonomous.adaptive_glymphatic import AdaptiveGlymphaticSystem

system = AdaptiveGlymphaticSystem()
decision = system.monitor_and_decide()

assert 'action' in decision, 'No action in decision'
assert 'delay_minutes' in decision, 'No delay in decision'
print(f'Decision: {decision["action"]} (delay: {decision["delay_minutes"]}m)')
"@
        $miniTest | Out-File -FilePath $testScript -Encoding utf8
    }
    
    $output = & $pyPath $testScript 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Test script failed: $output"
    }
}

# Test 7: Session continuity
Write-TestHeader "Test 7: Session Continuity"
Invoke-TestCase "Session continuity files exist" {
    $sessionFiles = @(
        'outputs\session_continuity_latest.md'
        'outputs\.copilot_context_summary.md'
    )
    
    foreach ($file in $sessionFiles) {
        $path = Join-Path $workspaceRoot $file
        if (-not (Test-Path $path)) {
            Write-Host "    ⚠️  Optional file missing: $file" -ForegroundColor Yellow
        }
        else {
            Write-Host "    ✓ Found: $file" -ForegroundColor Green
        }
    }
}

# Test 8: Glymphatic execution (optional)
if (-not $SkipGoalExecution) {
    Write-TestHeader "Test 8: Glymphatic Execution (Dry Run)"
    Invoke-TestCase "Register glymphatic goal" {
        $pyPath = Join-Path $workspaceRoot 'fdo_agi_repo\.venv\Scripts\python.exe'
        $scriptPath = Join-Path $workspaceRoot 'scripts\register_glymphatic_goal.py'
        
        # Test registration only (dry run)
        $testCmd = @"
import sys
sys.path.insert(0, r'$workspaceRoot\fdo_agi_repo')
from scripts.register_glymphatic_goal import register_glymphatic_cleanup_goal

# This would register but we're just testing the function exists
print('Registration function available')
"@
        $output = & $pyPath -c $testCmd 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Registration test failed: $output"
        }
    }
}

# Generate report
Write-TestHeader "Test Summary"

$duration = (Get-Date) - $script:testResults.StartTime
$total = $script:testResults.Passed + $script:testResults.Failed
$passRate = if ($total -gt 0) { [math]::Round(($script:testResults.Passed / $total) * 100, 1) } else { 0 }

Write-Host "  ⏱️  Duration: $($duration.TotalSeconds.ToString('F2'))s" -ForegroundColor Cyan
Write-Host "  ✅ Passed: $($script:testResults.Passed)" -ForegroundColor Green
Write-Host "  ❌ Failed: $($script:testResults.Failed)" -ForegroundColor Red
Write-Host "  📊 Pass Rate: $passRate%" -ForegroundColor $(if ($passRate -ge 80) { 'Green' } else { 'Yellow' })

# Save detailed report
$reportPath = Join-Path $workspaceRoot 'outputs\glymphatic_e2e_test_report.json'
$script:testResults | ConvertTo-Json -Depth 5 | Out-File -FilePath $reportPath -Encoding utf8
Write-Host "`n  📄 Detailed report: $reportPath" -ForegroundColor Cyan

# Exit with appropriate code
if ($script:testResults.Failed -gt 0) {
    Write-Host "`n❌ Some tests failed!" -ForegroundColor Red
    exit 1
}
else {
    Write-Host "`n✅ All tests passed!" -ForegroundColor Green
    exit 0
}