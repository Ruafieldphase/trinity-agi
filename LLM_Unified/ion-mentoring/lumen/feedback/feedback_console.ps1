#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Lumen Feedback Loop - Central Management Console

.DESCRIPTION
  Interactive menu-driven console for managing all aspects of feedback loop monitoring:
  - View live metrics
  - Manage scheduled tasks
  - Configure alert policies
  - Test notifications
  - Analyze distributions
  - Open dashboards

.EXAMPLE
  ./feedback_console.ps1
#>

$ErrorActionPreference = "Stop"

$ProjectId = "naeda-genesis"
$ServiceName = "lumen-gateway"
$DashboardId = "71f2f32c-29a4-49e2-b3c5-d840984828a6"
$ScriptsPath = "D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback"

function Show-Banner {
    Clear-Host
    Write-Host "╔═══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║      Lumen v1.7 - Feedback Loop Management Console    ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Project: $ProjectId" -ForegroundColor Gray
    Write-Host "  Service: $ServiceName" -ForegroundColor Gray
    Write-Host "  Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
    Write-Host ""
}

function Show-Menu {
    Write-Host "═══ Main Menu ═══" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  [1] [METRICS] View Live Metrics" -ForegroundColor Green
    Write-Host "  [2] [STATS] Open Dashboard" -ForegroundColor Green
    Write-Host "  [3] 📉 Analyze Distribution" -ForegroundColor Green
    Write-Host ""
    Write-Host "  [4] [SETTINGS]  Check Scheduled Task Status" -ForegroundColor Cyan
    Write-Host "  [5] ⏯️  Emit Metrics Once (Manual)" -ForegroundColor Cyan
    Write-Host "  [6] [SYNC] Restart Scheduled Task" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  [7] 🔔 View Alert Policies" -ForegroundColor Magenta
    Write-Host "  [8] [WARN]  Test Alert Triggers" -ForegroundColor Magenta
    Write-Host "  [9] 📧 Setup Notification Channels" -ForegroundColor Magenta
    Write-Host " [10] 💬 Test Slack Webhook" -ForegroundColor Magenta
    Write-Host ""
    Write-Host " [11] [SEARCH] Verify Data Flow" -ForegroundColor Yellow
    Write-Host " [12] 📚 Open Operations Runbook" -ForegroundColor Yellow
    Write-Host " [13] 🛠️  Tune Alert Thresholds" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  [0] 🚪 Exit" -ForegroundColor Red
    Write-Host ""
}

function Wait-ForKey {
    Write-Host ""
    Write-Host "Press any key to return to menu..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

function Get-LatestMetrics {
    $logFilter = "jsonPayload.component=`"feedback_loop`""
    $logCmd = "gcloud logging read `"$logFilter`" --project=$ProjectId --limit=1 --format=json --freshness=10m 2>&1"
    $logJson = cmd /c $logCmd
  
    if ($LASTEXITCODE -eq 0) {
        $logEntries = $logJson | ConvertFrom-Json
        if ($logEntries.Count -gt 0) {
            return $logEntries[0]
        }
    }
    return $null
}

while ($true) {
    Show-Banner
  
    # Quick status
    $latest = Get-LatestMetrics
    if ($latest) {
        $payload = $latest.jsonPayload
        $timestamp = [DateTime]::Parse($latest.timestamp).ToLocalTime()
    
        Write-Host "═══ Quick Status ═══" -ForegroundColor Cyan
        Write-Host "  Last Update: $timestamp" -ForegroundColor Gray
        Write-Host "  Hit Rate: $($payload.cache_hit_rate * 100)%" -ForegroundColor $(if ($payload.cache_hit_rate -ge 0.7) { "Green" } else { "Yellow" })
        Write-Host "  Memory: $($payload.cache_memory_usage_percent)%" -ForegroundColor $(if ($payload.cache_memory_usage_percent -le 75) { "Green" } else { "Yellow" })
        Write-Host "  Health: $($payload.unified_health_score)/100" -ForegroundColor $(if ($payload.unified_health_score -ge 80) { "Green" } else { "Yellow" })
        Write-Host ""
    }
    else {
        Write-Host "═══ Quick Status ═══" -ForegroundColor Cyan
        Write-Host "  No recent metrics (waiting for next emission...)" -ForegroundColor Yellow
        Write-Host ""
    }
  
    Show-Menu
  
    $choice = Read-Host "Select option"
  
    switch ($choice) {
        "1" {
            Show-Banner
            Write-Host "Starting live metrics monitor..." -ForegroundColor Yellow
            Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
            Write-Host ""
            Start-Sleep -Seconds 2
            & "$ScriptsPath/watch_metrics_live.ps1" -RefreshSeconds 5
        }
    
        "2" {
            Show-Banner
            Write-Host "Opening dashboard..." -ForegroundColor Yellow
            & "$ScriptsPath/open_dashboard.ps1" -ProjectId $ProjectId -DashboardId $DashboardId
            Wait-ForKey
        }
    
        "3" {
            Show-Banner
            Write-Host "Analyzing metric distributions..." -ForegroundColor Yellow
            Write-Host ""
            & "$ScriptsPath/analyze_metrics_distribution.ps1" -ProjectId $ProjectId -Hours 24
            Wait-ForKey
        }
    
        "4" {
            Show-Banner
            Write-Host "Scheduled Task Status:" -ForegroundColor Yellow
            Write-Host ""
            $task = Get-ScheduledTask -TaskName "LumenFeedbackEmitter" -ErrorAction SilentlyContinue
            if ($task) {
                $taskInfo = Get-ScheduledTaskInfo -TaskName "LumenFeedbackEmitter"
                Write-Host "  Name: LumenFeedbackEmitter" -ForegroundColor Cyan
                Write-Host "  State: $($task.State)" -ForegroundColor $(if ($task.State -eq "Ready") { "Green" } else { "Red" })
                Write-Host "  Last Run: $($taskInfo.LastRunTime)" -ForegroundColor Gray
                Write-Host "  Last Result: $($taskInfo.LastTaskResult) $(if ($taskInfo.LastTaskResult -eq 0) { '(Success)' } else { '(Failed)' })" -ForegroundColor $(if ($taskInfo.LastTaskResult -eq 0) { "Green" } else { "Red" })
                Write-Host "  Next Run: $($taskInfo.NextRunTime)" -ForegroundColor Cyan
                Write-Host "  Missed Runs: $($taskInfo.NumberOfMissedRuns)" -ForegroundColor Gray
            }
            else {
                Write-Host "  [ERROR] Task not found!" -ForegroundColor Red
                Write-Host ""
                Write-Host "  Would you like to register it now? (y/n)" -ForegroundColor Yellow
                $register = Read-Host
                if ($register -eq "y") {
                    & "$ScriptsPath/register_feedback_metrics_emitter.ps1" -TaskName "LumenFeedbackEmitter" -IntervalMinutes 5 -Force -ProjectId $ProjectId -ServiceName $ServiceName -BudgetUSD 200.0
                }
            }
            Wait-ForKey
        }
    
        "5" {
            Show-Banner
            Write-Host "Emitting metrics once..." -ForegroundColor Yellow
            Write-Host ""
            & "$ScriptsPath/run_emit_feedback_metrics_once.ps1" -ProjectId $ProjectId -ServiceName $ServiceName -BudgetUSD 200.0
            Wait-ForKey
        }
    
        "6" {
            Show-Banner
            Write-Host "Restarting scheduled task..." -ForegroundColor Yellow
            Write-Host ""
            & "$ScriptsPath/register_feedback_metrics_emitter.ps1" -TaskName "LumenFeedbackEmitter" -IntervalMinutes 5 -Force -ProjectId $ProjectId -ServiceName $ServiceName -BudgetUSD 200.0
            Wait-ForKey
        }
    
        "7" {
            Show-Banner
            Write-Host "Alert Policies:" -ForegroundColor Yellow
            Write-Host ""
            gcloud monitoring policies list --project=$ProjectId --filter='displayName:"Lumen:"' --format="table(displayName,enabled,conditions[0].conditionThreshold.filter)"
            Wait-ForKey
        }
    
        "8" {
            Show-Banner
            Write-Host "Test Alert Triggers" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "  [1] Test Cache Hit Rate Alert (low)" -ForegroundColor Gray
            Write-Host "  [2] Test Memory Usage Alert (high)" -ForegroundColor Gray
            Write-Host "  [3] Test Health Score Alert (low)" -ForegroundColor Gray
            Write-Host "  [4] Test All Alerts" -ForegroundColor Gray
            Write-Host ""
            $testChoice = Read-Host "Select test"
      
            $scenario = switch ($testChoice) {
                "1" { "hit-rate" }
                "2" { "memory" }
                "3" { "health" }
                "4" { "all" }
                default { "" }
            }
      
            if ($scenario) {
                & "$ScriptsPath/test_alert_triggers.ps1" -ProjectId $ProjectId -TestScenario $scenario
            }
            Wait-ForKey
        }
    
        "9" {
            Show-Banner
            Write-Host "Setup Notification Channels" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Enter email address (or press Enter to skip):" -ForegroundColor Cyan
            $email = Read-Host
      
            Write-Host "Enter Slack webhook URL (or press Enter to skip):" -ForegroundColor Cyan
            $slack = Read-Host
      
            if ($email -or $slack) {
                $args = @("-ProjectId", $ProjectId)
                if ($email) { $args += @("-EmailAddress", $email) }
                if ($slack) { $args += @("-SlackWebhookUrl", $slack) }
        
                & "$ScriptsPath/setup_notification_channels.ps1" @args
            }
            else {
                Write-Host "No channels specified." -ForegroundColor Yellow
            }
            Wait-ForKey
        }
    
        "10" {
            Show-Banner
            Write-Host "Test Slack Webhook" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Enter Slack webhook URL:" -ForegroundColor Cyan
            $webhookUrl = Read-Host
      
            if ($webhookUrl) {
                Write-Host ""
                Write-Host "  [1] Simple test" -ForegroundColor Gray
                Write-Host "  [2] Alert notification" -ForegroundColor Gray
                Write-Host "  [3] Dashboard summary" -ForegroundColor Gray
                Write-Host "  [4] Real-time metrics" -ForegroundColor Gray
                Write-Host ""
                $testType = Read-Host "Select test type"
        
                $type = switch ($testType) {
                    "1" { "simple" }
                    "2" { "alert" }
                    "3" { "dashboard" }
                    "4" { "metrics" }
                    default { "simple" }
                }
        
                & "$ScriptsPath/test_slack_webhook.ps1" -WebhookUrl $webhookUrl -TestType $type
            }
            Wait-ForKey
        }
    
        "11" {
            Show-Banner
            Write-Host "Verifying data flow..." -ForegroundColor Yellow
            Write-Host ""
            & "$ScriptsPath/verify_data_flow.ps1" -ProjectId $ProjectId
            Wait-ForKey
        }
    
        "12" {
            Show-Banner
            Write-Host "Opening Operations Runbook..." -ForegroundColor Yellow
            $runbookPath = "$ScriptsPath/OPERATIONS_RUNBOOK.md"
            if (Test-Path $runbookPath) {
                code $runbookPath
            }
            else {
                Write-Host "Runbook not found at: $runbookPath" -ForegroundColor Red
            }
            Wait-ForKey
        }
    
        "13" {
            Show-Banner
            Write-Host "Tune Alert Thresholds" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "First, analyze current distributions..." -ForegroundColor Cyan
            & "$ScriptsPath/analyze_metrics_distribution.ps1" -ProjectId $ProjectId -Hours 24
            Write-Host ""
            Write-Host "Do you want to apply recommended thresholds? (y/n)" -ForegroundColor Yellow
            $apply = Read-Host
      
            if ($apply -eq "y") {
                Write-Host ""
                Write-Host "Enter HitRateThresholdPercent (current: 50):" -ForegroundColor Cyan
                $hitRate = Read-Host
                Write-Host "Enter MemoryThresholdPercent (current: 90):" -ForegroundColor Cyan
                $memory = Read-Host
                Write-Host "Enter HealthThreshold (current: 60):" -ForegroundColor Cyan
                $health = Read-Host
        
                $args = @("-ProjectId", $ProjectId)
                if ($hitRate) { $args += @("-HitRateThresholdPercent", $hitRate) }
                if ($memory) { $args += @("-MemoryThresholdPercent", $memory) }
                if ($health) { $args += @("-HealthThreshold", $health) }
        
                & "$ScriptsPath/setup_alert_policies.ps1" @args
            }
            Wait-ForKey
        }
    
        "0" {
            Show-Banner
            Write-Host "Exiting..." -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Feedback Loop monitoring infrastructure is running." -ForegroundColor Green
            Write-Host "Scheduled task will continue emitting metrics every 5 minutes." -ForegroundColor Gray
            Write-Host ""
            exit 0
        }
    
        default {
            Write-Host "Invalid option. Please try again." -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    }
}
