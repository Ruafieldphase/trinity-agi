#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Quick Session Start - 30??에 ?체 ?스???태 ?악

.DESCRIPTION
    ???션 ?작 ??AGI, Canary, Core, System ?태?빠르??인?는 ?크립트

.EXAMPLE
    .\scripts\quick_session_start.ps1
    
.EXAMPLE
    .\scripts\quick_session_start.ps1 -Detailed
#>

param(
    [switch]$Detailed,
    [switch]$Json
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Continue"
$BaseDir = "$WorkspaceRoot"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Quick Session Start - System Overview" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. AGI Health Check
Write-Host "AGI Orchestrator" -ForegroundColor Green
Write-Host "-----------------------------------------------------------" -ForegroundColor DarkGray

try {
    $healthResult = & "$BaseDir\fdo_agi_repo\scripts\check_health.ps1" 2>&1 | Out-String
    
    if ($healthResult -match "HEALTH: (PASS|FAIL)") {
        $healthStatus = $matches[1]
        if ($healthStatus -eq "PASS") {
            Write-Host "   Status: PASS" -ForegroundColor Green
        }
        else {
            Write-Host "   Status: FAIL" -ForegroundColor Red
        }
    }
    
    if ($healthResult -match '"avg_confidence": ([\d\.]+)') {
        $conf = [math]::Round([double]$matches[1], 3)
        Write-Host "   Confidence: $conf" -ForegroundColor White
    }
    
    if ($healthResult -match '"avg_quality": ([\d\.]+)') {
        $qual = [math]::Round([double]$matches[1], 3)
        Write-Host "   Quality: $qual" -ForegroundColor White
    }
    
    if ($healthResult -match '"second_pass_rate_per_task": ([\d\.]+)') {
        $sp = [math]::Round([double]$matches[1] * 100, 1)
        Write-Host "   Second Pass: $sp%" -ForegroundColor White
    }
}
catch {
    Write-Host "   Status: Check Failed" -ForegroundColor Yellow
}

Write-Host ""

# 2. Canary Deployment Status
Write-Host "Canary Deployment" -ForegroundColor Green
Write-Host "-----------------------------------------------------------" -ForegroundColor DarkGray

try {
    # Check monitoring loop
    $logDir = "$BaseDir\LLM_Unified\ion-mentoring\logs"
    $latestLog = Get-ChildItem $logDir -Filter "monitor_loop_*.log" -ErrorAction SilentlyContinue | 
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
    
    if ($latestLog) {
        $ageMinutes = [math]::Round(((Get-Date) - $latestLog.LastWriteTime).TotalMinutes, 1)
        
        if ($ageMinutes -lt 35) {
            Write-Host "   Monitoring: Running ($ageMinutes min ago)" -ForegroundColor Green
        }
        else {
            Write-Host "   Monitoring: Stale ($ageMinutes min ago)" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "   Monitoring: Not found" -ForegroundColor Red
    }
    
    # Check probe results (최근 ?행 결과)
    $probeFiles = Get-ChildItem "$logDir\probe_iter_*.json" -ErrorAction SilentlyContinue | 
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
    
    if ($probeFiles) {
        $probeData = Get-Content $probeFiles.FullName -Raw | ConvertFrom-Json
        $probeAge = ((Get-Date) - $probeFiles.LastWriteTime).TotalMinutes
        
        if ($probeAge -lt 60) {
            Write-Host "   Probe: $([math]::Round($probeAge, 0))m ago" -ForegroundColor Gray
            $legacyRate = $probeData.legacy.success_rate
            $canaryRate = $probeData.canary.success_rate
            Write-Host "     Legacy: $legacyRate% ($($probeData.legacy.avg_response_ms)ms)" -ForegroundColor White
            Write-Host "     Canary: $canaryRate% ($($probeData.canary.avg_response_ms)ms)" -ForegroundColor White
        }
        else {
            Write-Host "   Probe: Stale ($([math]::Round($probeAge, 0))m ago)" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "   Probe: No recent data" -ForegroundColor Gray
    }
}
catch {
    Write-Host "   Canary check failed" -ForegroundColor Yellow
}

Write-Host ""

# 3. Recent Activity (Last 6 hours)
Write-Host "Recent Activity (Last 6 hours)" -ForegroundColor Green
Write-Host "-----------------------------------------------------------" -ForegroundColor DarkGray

try {
    $ledgerFile = "$BaseDir\fdo_agi_repo\memory\resonance_ledger.jsonl"
    
    if (Test-Path $ledgerFile) {
        $sixHoursAgo = (Get-Date).AddHours(-6)
        
        $events = Get-Content $ledgerFile -Tail 200 | 
        ForEach-Object { 
            try { $_ | ConvertFrom-Json } catch { $null }
        } | 
        Where-Object { $_ -and $_.timestamp } |
        Where-Object { 
            try {
                [datetime]::Parse($_.timestamp) -gt $sixHoursAgo
            }
            catch {
                $false
            }
        }
        
        $taskCount = ($events | Where-Object { $_.event -eq "run_config" }).Count
        $evalCount = ($events | Where-Object { $_.event -eq "eval" }).Count
        $replanCount = ($events | Where-Object { $_.event -eq "replan" }).Count
        
        Write-Host "   Tasks: $taskCount" -ForegroundColor White
        Write-Host "   Evaluations: $evalCount" -ForegroundColor White
        Write-Host "   Replans: $replanCount" -ForegroundColor White
        
        if ($evalCount -gt 0) {
            $avgQuality = ($events | Where-Object { $_.event -eq "eval" } | 
                Measure-Object -Property quality -Average).Average
            $avgQuality = [math]::Round($avgQuality, 3)
            Write-Host "   Avg Quality: $avgQuality" -ForegroundColor White
        }
    }
}
catch {
    Write-Host "   Activity check failed" -ForegroundColor Yellow
}

Write-Host ""

# 4. System Resources
Write-Host "System Resources" -ForegroundColor Green
Write-Host "-----------------------------------------------------------" -ForegroundColor DarkGray

try {
    $cpu = [math]::Round((Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples.CookedValue, 1)
    $mem = [math]::Round((Get-Counter '\Memory\% Committed Bytes In Use').CounterSamples.CookedValue, 1)
    
    $cpuStatus = if ($cpu -lt 80) { "OK" } else { "HIGH" }
    $memStatus = if ($mem -lt 80) { "OK" } else { "HIGH" }
    
    Write-Host "   CPU: $cpuStatus $cpu%" -ForegroundColor White
    Write-Host "   Memory: $memStatus $mem%" -ForegroundColor White
}
catch {
    Write-Host "   Resource check failed" -ForegroundColor Yellow
}

Write-Host ""

# 5. Quick Actions
Write-Host "Quick Actions" -ForegroundColor Cyan
Write-Host "-----------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "   Ctrl+Shift+P -> 'ChatOps' search" -ForegroundColor White
Write-Host "   .\scripts\chatops_router.ps1 -Say 'status'" -ForegroundColor DarkGray
Write-Host "   .\scripts\chatops_router.ps1 -Say 'AGI status'" -ForegroundColor DarkGray
Write-Host "   .\scripts\chatops_router.ps1 -Say 'canary status'" -ForegroundColor DarkGray

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Detailed mode
if ($Detailed) {
    Write-Host "Detailed Status (running full dashboard...)" -ForegroundColor Yellow
    Write-Host ""
    & "$BaseDir\fdo_agi_repo\scripts\ops_dashboard.ps1"
}

# JSON output
if ($Json) {
    $output = @{
        timestamp = Get-Date -Format "o"
        agi       = @{
            health = if ($healthStatus -eq "PASS") { "healthy" } else { "unhealthy" }
        }
        canary    = @{
            monitoring = if ($ageMinutes -lt 35) { "running" } else { "stale" }
        }
        system    = @{
            cpu_percent    = $cpu
            memory_percent = $mem
        }
    }
    
    $output | ConvertTo-Json -Depth 3
}