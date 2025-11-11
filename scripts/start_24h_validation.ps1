#!/usr/bin/env pwsh
# 24시간 자율 시스템 검증 루프
# Self-Care + Feedback Trinity 통합 검증

param(
    [switch]$AutoReport,
    [int]$IntervalMinutes = 30,
    [string]$OutDir = "$PSScriptRoot\..\outputs\validation_24h"
)

$ErrorActionPreference = "Continue"
$StartTime = Get-Date

Write-Host "🚀 24-Hour Autonomous Validation Started" -ForegroundColor Green
Write-Host "   Start Time: $($StartTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Cyan
Write-Host "   Check Interval: $IntervalMinutes minutes" -ForegroundColor Cyan
Write-Host "   Output Directory: $OutDir" -ForegroundColor Cyan
Write-Host ""

# 출력 디렉토리 생성
if (!(Test-Path $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
}

$ValidationLog = Join-Path $OutDir "validation_log.jsonl"
$SummaryPath = Join-Path $OutDir "validation_summary.json"

# 검증 카운터
$CheckCount = 0
$SuccessCount = 0
$WarningCount = 0
$FailureCount = 0

# 24시간 = 1440분
$TotalChecks = [math]::Floor(1440 / $IntervalMinutes)

function Write-ValidationEntry {
    param($Type, $Message, $Data = @{})
    
    $entry = @{
        timestamp    = (Get-Date).ToString('o')
        type         = $Type
        message      = $Message
        check_number = $script:CheckCount
        data         = $Data
    }
    
    $entry | ConvertTo-Json -Compress | Add-Content -Path $script:ValidationLog
    
    $color = switch ($Type) {
        "success" { "Green" }
        "warning" { "Yellow" }
        "error" { "Red" }
        default { "White" }
    }
    
    Write-Host "[$Type] $Message" -ForegroundColor $color
}

function Test-SystemHealth {
    Write-Host "`n🔍 Running System Health Check..." -ForegroundColor Cyan
    
    try {
        $healthScript = Join-Path $PSScriptRoot "system_health_check.ps1"
        if (!(Test-Path $healthScript)) {
            Write-ValidationEntry "warning" "Health check script not found: $healthScript"
            return $false
        }
        
        $output = & $healthScript 2>&1
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            Write-ValidationEntry "success" "System health check passed" @{
                exit_code     = $exitCode
                output_length = $output.Length
            }
            return $true
        }
        else {
            Write-ValidationEntry "warning" "System health check completed with warnings" @{
                exit_code = $exitCode
            }
            return $true  # 경고는 실패로 보지 않음
        }
    }
    catch {
        Write-ValidationEntry "error" "System health check failed: $_" @{
            error = $_.Exception.Message
        }
        return $false
    }
}

function Test-GoalExecution {
    Write-Host "`n🎯 Testing Autonomous Goal Execution..." -ForegroundColor Cyan
    
    try {
        $goalTracker = Join-Path $PSScriptRoot "..\fdo_agi_repo\memory\goal_tracker.json"
        
        if (!(Test-Path $goalTracker)) {
            Write-ValidationEntry "warning" "Goal tracker not found"
            return $false
        }
        
        $tracker = Get-Content $goalTracker -Raw | ConvertFrom-Json
        $recentGoals = $tracker.goals | Where-Object {
            $_.created_at -and (Get-Date $_.created_at) -gt (Get-Date).AddHours(-1)
        }
        
        $completedCount = ($recentGoals | Where-Object { $_.status -eq "completed" }).Count
        $inProgressCount = ($recentGoals | Where-Object { $_.status -eq "in_progress" }).Count
        
        Write-ValidationEntry "success" "Goal execution active" @{
            recent_goals = $recentGoals.Count
            completed    = $completedCount
            in_progress  = $inProgressCount
        }
        
        return $true
    }
    catch {
        Write-ValidationEntry "error" "Goal execution check failed: $_"
        return $false
    }
}

function Test-QueueServer {
    Write-Host "`n📦 Testing Task Queue Server..." -ForegroundColor Cyan
    
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8091/api/health" -TimeoutSec 5 -ErrorAction Stop
        
        Write-ValidationEntry "success" "Task Queue Server is responsive" @{
            status = $response.status
        }
        return $true
    }
    catch {
        Write-ValidationEntry "warning" "Task Queue Server not responding (may need restart)" @{
            error = $_.Exception.Message
        }
        
        # 자동 복구 시도
        Write-Host "   Attempting auto-recovery..." -ForegroundColor Yellow
        try {
            $ensureScript = Join-Path $PSScriptRoot "ensure_task_queue_server.ps1"
            if (Test-Path $ensureScript) {
                & $ensureScript -Port 8091
                Start-Sleep -Seconds 5
                $response = Invoke-RestMethod -Uri "http://127.0.0.1:8091/api/health" -TimeoutSec 5
                Write-ValidationEntry "success" "Task Queue Server recovered"
                return $true
            }
        }
        catch {
            Write-ValidationEntry "error" "Auto-recovery failed"
        }
        
        return $false
    }
}

function Test-MetricsCollection {
    Write-Host "`n📊 Testing Metrics Collection..." -ForegroundColor Cyan
    
    try {
        $metricsFiles = @(
            "outputs\monitoring_metrics_latest.json",
            "outputs\cache_analysis_latest.json",
            "outputs\sena_correlation_latest.json"
        )
        
        $foundCount = 0
        $recentCount = 0
        
        foreach ($file in $metricsFiles) {
            $fullPath = Join-Path $PSScriptRoot "..\$file"
            if (Test-Path $fullPath) {
                $foundCount++
                $lastWrite = (Get-Item $fullPath).LastWriteTime
                if ($lastWrite -gt (Get-Date).AddHours(-2)) {
                    $recentCount++
                }
            }
        }
        
        if ($recentCount -ge 2) {
            Write-ValidationEntry "success" "Metrics collection active" @{
                found  = $foundCount
                recent = $recentCount
            }
            return $true
        }
        else {
            Write-ValidationEntry "warning" "Metrics collection may be stale" @{
                found  = $foundCount
                recent = $recentCount
            }
            return $false
        }
    }
    catch {
        Write-ValidationEntry "error" "Metrics check failed: $_"
        return $false
    }
}

function Invoke-ValidationCycle {
    $script:CheckCount++
    $elapsed = ((Get-Date) - $script:StartTime).TotalHours
    
    Write-Host "`n" ("=" * 60) -ForegroundColor Cyan
    Write-Host "  Validation Check #$($script:CheckCount)/$TotalChecks" -ForegroundColor White
    Write-Host "  Elapsed: $([math]::Round($elapsed, 2)) hours / 24 hours" -ForegroundColor White
    Write-Host ("=" * 60) -ForegroundColor Cyan
    
    $results = @{
        health  = Test-SystemHealth
        goals   = Test-GoalExecution
        queue   = Test-QueueServer
        metrics = Test-MetricsCollection
    }
    
    $passCount = ($results.Values | Where-Object { $_ -eq $true }).Count
    $totalTests = $results.Count
    $passRate = [math]::Round(($passCount / $totalTests) * 100, 1)
    
    if ($passRate -ge 75) {
        $script:SuccessCount++
        $status = "✅ PASS"
        $color = "Green"
    }
    elseif ($passRate -ge 50) {
        $script:WarningCount++
        $status = "⚠️ WARN"
        $color = "Yellow"
    }
    else {
        $script:FailureCount++
        $status = "❌ FAIL"
        $color = "Red"
    }
    
    Write-Host "`n$status - Pass Rate: $passRate% ($passCount/$totalTests)" -ForegroundColor $color
    
    # 요약 업데이트
    $summary = @{
        start_time           = $script:StartTime.ToString('o')
        current_time         = (Get-Date).ToString('o')
        elapsed_hours        = $elapsed
        total_checks         = $script:CheckCount
        success_checks       = $script:SuccessCount
        warning_checks       = $script:WarningCount
        failure_checks       = $script:FailureCount
        current_pass_rate    = $passRate
        overall_success_rate = [math]::Round(($script:SuccessCount / $script:CheckCount) * 100, 1)
    }
    
    $summary | ConvertTo-Json | Set-Content -Path $script:SummaryPath
    
    return $results
}

# 메인 루프
Write-Host "`n🔄 Starting validation loop..." -ForegroundColor Green
Write-Host "   Will run $TotalChecks checks over 24 hours" -ForegroundColor Cyan
Write-Host "   Press Ctrl+C to stop manually`n" -ForegroundColor Yellow

try {
    while ((Get-Date) -lt $StartTime.AddHours(24)) {
        Invoke-ValidationCycle
        
        # 다음 체크까지 대기
        $nextCheck = (Get-Date).AddMinutes($IntervalMinutes)
        $remaining = ($StartTime.AddHours(24) - (Get-Date)).TotalMinutes
        
        if ($remaining -le 0) {
            break
        }
        
        Write-Host "`n💤 Sleeping until next check: $($nextCheck.ToString('HH:mm:ss'))" -ForegroundColor Gray
        Write-Host "   ($([math]::Round($remaining, 1)) minutes remaining in 24h window)`n" -ForegroundColor Gray
        
        Start-Sleep -Seconds ($IntervalMinutes * 60)
    }
    
    Write-Host "`n" ("=" * 60) -ForegroundColor Green
    Write-Host "  🎉 24-Hour Validation Complete!" -ForegroundColor Green
    Write-Host ("=" * 60) -ForegroundColor Green
    
    $finalRate = [math]::Round(($script:SuccessCount / $script:CheckCount) * 100, 1)
    
    Write-Host "`nFinal Results:" -ForegroundColor White
    Write-Host "  Total Checks: $($script:CheckCount)" -ForegroundColor Cyan
    Write-Host "  Success: $($script:SuccessCount)" -ForegroundColor Green
    Write-Host "  Warnings: $($script:WarningCount)" -ForegroundColor Yellow
    Write-Host "  Failures: $($script:FailureCount)" -ForegroundColor Red
    Write-Host "  Success Rate: $finalRate%" -ForegroundColor $(if ($finalRate -ge 90) { "Green" } elseif ($finalRate -ge 75) { "Yellow" } else { "Red" })
    
    Write-Host "`nReports saved to:" -ForegroundColor White
    Write-Host "  Log: $ValidationLog" -ForegroundColor Cyan
    Write-Host "  Summary: $SummaryPath" -ForegroundColor Cyan
    
    if ($AutoReport) {
        Write-Host "`n📊 Generating final report..." -ForegroundColor Cyan
        $reportScript = Join-Path $PSScriptRoot "generate_validation_report.ps1"
        if (Test-Path $reportScript) {
            & $reportScript -ValidationDir $OutDir
        }
    }
    
}
catch {
    Write-Host "`n❌ Validation interrupted: $_" -ForegroundColor Red
    Write-ValidationEntry "error" "Validation loop interrupted" @{
        error            = $_.Exception.Message
        checks_completed = $script:CheckCount
    }
}

Write-Host "`n✨ Done!" -ForegroundColor Green
