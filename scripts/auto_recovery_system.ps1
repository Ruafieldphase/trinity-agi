# Auto Recovery System for 6 Integrated Systems
# Monitors system health and auto-recovers on failures

param(
    [int]$CheckIntervalSeconds = 300,  # Check every 5 minutes
    [int]$MaxRetries = 3,
    [switch]$DryRun,
    [switch]$SendAlert
)

$ErrorActionPreference = "Continue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$outputDir = Join-Path (Split-Path -Parent $scriptDir) "outputs"
$logFile = Join-Path $outputDir "auto_recovery_log.jsonl"

Write-Host "`n" -NoNewline
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "`n  Auto Recovery System`n" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "`n"

function Test-SystemHealth {
    param([string]$SystemName, [string]$FilePath, [int]$MaxAgeHours)
    
    if (-not (Test-Path $FilePath)) {
        return @{
            Status = "MISSING"
            Age    = $null
            Reason = "File not found"
        }
    }
    
    $fileInfo = Get-Item $FilePath
    $ageHours = ((Get-Date) - $fileInfo.LastWriteTime).TotalHours
    
    if ($ageHours -gt $MaxAgeHours) {
        return @{
            Status = "STALE"
            Age    = $ageHours
            Reason = "File too old (${ageHours}h > ${MaxAgeHours}h)"
        }
    }
    
    return @{
        Status = "OK"
        Age    = $ageHours
        Reason = $null
    }
}

function Invoke-SystemRecovery {
    param([string]$SystemName, [string]$ScriptPath)
    
    Write-Host "  Attempting recovery for $SystemName..." -ForegroundColor Yellow
    
    if ($DryRun) {
        Write-Host "    [DRY-RUN] Would run: $ScriptPath" -ForegroundColor Gray
        return $true
    }
    
    try {
        & $ScriptPath -ErrorAction Stop
        Write-Host "    Recovery successful!" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "    Recovery failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Send-AlertNotification {
    param([string]$Message, [string]$Severity = "WARNING")
    
    $alertFile = Join-Path $outputDir "alerts_$(Get-Date -Format 'yyyy-MM-dd').txt"
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $alertEntry = "[$timestamp] [$Severity] $Message"
    
    Add-Content -Path $alertFile -Value $alertEntry
    
    # Could integrate with email/Slack/Teams here
    Write-Host "  [ALERT] $Message" -ForegroundColor $(if ($Severity -eq "ERROR") { "Red" } else { "Yellow" })
}

# System definitions
$systems = @(
    @{
        Name           = "Resonance Loop"
        FilePath       = Join-Path $scriptDir "..\fdo_agi_repo\outputs\resonance_core_integration_latest.md"
        MaxAgeHours    = 48
        RecoveryScript = Join-Path $scriptDir "run_resonance_core_integration.ps1"
    },
    @{
        Name           = "BQI Phase 6"
        FilePath       = Join-Path $scriptDir "..\fdo_agi_repo\outputs\bqi_core_integration_latest.md"
        MaxAgeHours    = 48
        RecoveryScript = Join-Path $scriptDir "run_bqi_core_integration.ps1"
    },
    @{
        Name           = "Intelligent Feedback"
        FilePath       = Join-Path $scriptDir "..\outputs\feedback_implementation_plan.md"
        MaxAgeHours    = 72
        RecoveryScript = Join-Path $scriptDir "run_intelligent_feedback.ps1"
    },
    @{
        Name           = "Orchestration"
        FilePath       = Join-Path $scriptDir "..\outputs\orchestration_latest.md"
        MaxAgeHours    = 48
        RecoveryScript = Join-Path $scriptDir "run_orchestration.ps1"
    },
    @{
        Name           = "Daily Briefing"
        FilePath       = Join-Path $scriptDir "..\outputs\daily_briefing_$(Get-Date -Format 'yyyy-MM-dd').md"
        MaxAgeHours    = 24
        RecoveryScript = Join-Path $scriptDir "generate_daily_briefing.ps1"
    }
)

Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Check Interval: ${CheckIntervalSeconds}s" -ForegroundColor Gray
Write-Host "  Max Retries: $MaxRetries" -ForegroundColor Gray
Write-Host "  Dry Run: $DryRun" -ForegroundColor Gray
Write-Host "  Alert: $SendAlert" -ForegroundColor Gray
Write-Host ""

$recoveryAttempts = @{}

# Main loop
$runCount = 0
while ($true) {
    $runCount++
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    Write-Host "`n[$timestamp] Health Check #$runCount" -ForegroundColor Cyan
    Write-Host ("-" * 70) -ForegroundColor Gray
    
    $issues = @()
    
    foreach ($system in $systems) {
        Write-Host "  Checking $($system.Name)..." -ForegroundColor White
        
        $health = Test-SystemHealth -SystemName $system.Name -FilePath $system.FilePath -MaxAgeHours $system.MaxAgeHours
        
        if ($health.Status -eq "OK") {
            Write-Host "    OK (age: $($health.Age.ToString('F1'))h)" -ForegroundColor Green
            # Reset retry counter on success
            $recoveryAttempts[$system.Name] = 0
        }
        else {
            Write-Host "    $($health.Status): $($health.Reason)" -ForegroundColor Yellow
            
            $issues += @{
                System = $system.Name
                Status = $health.Status
                Reason = $health.Reason
            }
            
            # Check retry limit
            if (-not $recoveryAttempts.ContainsKey($system.Name)) {
                $recoveryAttempts[$system.Name] = 0
            }
            
            if ($recoveryAttempts[$system.Name] -lt $MaxRetries) {
                $recoveryAttempts[$system.Name]++
                
                $recoverySuccess = Invoke-SystemRecovery -SystemName $system.Name -ScriptPath $system.RecoveryScript
                
                if ($recoverySuccess) {
                    $recoveryAttempts[$system.Name] = 0  # Reset on success
                }
                else {
                    if ($SendAlert) {
                        Send-AlertNotification -Message "Recovery failed for $($system.Name) (Attempt $($recoveryAttempts[$system.Name])/$MaxRetries)" -Severity "ERROR"
                    }
                }
            }
            else {
                Write-Host "    Max retries reached. Manual intervention required." -ForegroundColor Red
                if ($SendAlert) {
                    Send-AlertNotification -Message "Max retries reached for $($system.Name). Manual intervention required!" -Severity "CRITICAL"
                }
            }
        }
    }
    
    # Log results
    $logEntry = @{
        timestamp        = $timestamp
        runCount         = $runCount
        issuesFound      = $issues.Count
        issues           = $issues
        recoveryAttempts = $recoveryAttempts.Clone()
    } | ConvertTo-Json -Compress
    
    Add-Content -Path $logFile -Value $logEntry
    
    # Summary
    Write-Host "`nSummary:" -ForegroundColor Cyan
    Write-Host "  Systems Checked: $($systems.Count)" -ForegroundColor White
    Write-Host "  Issues Found: $($issues.Count)" -ForegroundColor $(if ($issues.Count -eq 0) { "Green" } else { "Yellow" })
    
    if ($issues.Count -eq 0) {
        Write-Host "  All systems healthy! " -ForegroundColor Green
    }
    
    # Wait for next check
    Write-Host "`nNext check in ${CheckIntervalSeconds}s..." -ForegroundColor Gray
    Write-Host ("-" * 70) -ForegroundColor Gray
    
    Start-Sleep -Seconds $CheckIntervalSeconds
}