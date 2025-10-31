<#
.SYNOPSIS
Continuously retry alert policy creation until metrics exist

.DESCRIPTION
Polls for metric availability every 30 seconds and creates alert policies
once metrics are queryable. Runs as background job or foreground loop.

.PARAMETER MaxRetries
Maximum retry attempts (default: 20 = 10 minutes)

.PARAMETER RetryIntervalSeconds
Seconds between retries (default: 30)

.PARAMETER Background
Run as background job

.EXAMPLE
.\auto_create_alert_policies.ps1 -MaxRetries 20 -RetryIntervalSeconds 30
#>

[CmdletBinding()]
param(
    [int]$MaxRetries = 20,
    [int]$RetryIntervalSeconds = 30,
    [switch]$Background
)

$ErrorActionPreference = "Stop"
$ProjectId = "naeda-genesis"

function Test-MetricExists {
    param([string]$MetricName)
    
    try {
        $result = gcloud logging metrics describe $MetricName --project=$ProjectId 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
        
        return $false
    }
    catch {
        return $false
    }
}

function Invoke-PolicyCreation {
    Write-Host "[OK] Metrics detected! Creating alert policies..." -ForegroundColor Green
    
    $scriptPath = Join-Path $PSScriptRoot "create_feedback_alert_policies.ps1"
    
    & $scriptPath
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Alert policies created successfully!" -ForegroundColor Green
        return $true
    }
    else {
        Write-Host "[ERROR] Failed to create alert policies (exit code: $LASTEXITCODE)" -ForegroundColor Red
        return $false
    }
}

function Start-PolicyCreationLoop {
    Write-Host "[SEARCH] Monitoring for metric availability..." -ForegroundColor Cyan
    Write-Host "Project: $ProjectId" -ForegroundColor Gray
    Write-Host "Max Retries: $MaxRetries" -ForegroundColor Gray
    Write-Host "Retry Interval: $RetryIntervalSeconds seconds" -ForegroundColor Gray
    Write-Host ""
    
    $attempt = 0
    
    while ($attempt -lt $MaxRetries) {
        $attempt++
        
        $timestamp = Get-Date -Format "HH:mm:ss"
        Write-Host "[$timestamp] Attempt $attempt/$MaxRetries - Checking metric: unified_health_score..." -ForegroundColor Cyan
        
        if (Test-MetricExists -MetricName "unified_health_score") {
            Write-Host "[$timestamp] [OK] Metric 'unified_health_score' exists!" -ForegroundColor Green
            
            # Also check cache_hit_rate
            if (Test-MetricExists -MetricName "cache_hit_rate") {
                Write-Host "[$timestamp] [OK] Metric 'cache_hit_rate' exists!" -ForegroundColor Green
                
                # Create policies
                if (Invoke-PolicyCreation) {
                    return $true
                }
                else {
                    Write-Host "[WARN] Policy creation failed, but metrics exist. Check script." -ForegroundColor Yellow
                    return $false
                }
            }
            else {
                Write-Host "[$timestamp] [WAIT] Metric 'cache_hit_rate' not yet available..." -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "[$timestamp] [WAIT] Metric 'unified_health_score' not yet available..." -ForegroundColor Yellow
        }
        
        if ($attempt -lt $MaxRetries) {
            Write-Host "[$timestamp] Waiting $RetryIntervalSeconds seconds before next attempt..." -ForegroundColor Gray
            Start-Sleep -Seconds $RetryIntervalSeconds
        }
    }
    
    Write-Host ""
    Write-Host "[ERROR] Max retries reached. Metrics still not available." -ForegroundColor Red
    Write-Host "Possible causes:" -ForegroundColor Yellow
    Write-Host "  1. Orchestrator not emitting metrics (check scheduled task)" -ForegroundColor Yellow
    Write-Host "  2. Propagation taking longer than expected (wait 5 more minutes)" -ForegroundColor Yellow
    Write-Host "  3. Metric names incorrect (check emit_feedback_metrics_once.py)" -ForegroundColor Yellow
    
    return $false
}

# Main execution
if ($Background) {
    # Run as background job
    $job = Start-Job -ScriptBlock {
        param($ScriptPath, $MaxRetries, $RetryInterval, $ProjectId)
        
        & $ScriptPath -MaxRetries $MaxRetries -RetryIntervalSeconds $RetryInterval
    } -ArgumentList $PSCommandPath, $MaxRetries, $RetryIntervalSeconds, $ProjectId
    
    Write-Host "[OK] Background job started: $($job.Name)" -ForegroundColor Green
    Write-Host "Monitor with: Receive-Job -Id $($job.Id) -Keep" -ForegroundColor Cyan
    Write-Host "Wait for completion: Wait-Job -Id $($job.Id)" -ForegroundColor Cyan
}
else {
    # Run in foreground
    $success = Start-PolicyCreationLoop
    
    if ($success) {
        exit 0
    }
    else {
        exit 1
    }
}
