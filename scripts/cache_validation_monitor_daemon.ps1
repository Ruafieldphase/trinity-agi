#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Cache Validation Monitor Daemon (Background Worker)
.DESCRIPTION
    Runs in background, checks schedule every 5 minutes, auto-executes validations.
    NO ADMIN REQUIRED - Pure PowerShell background job.
#>

$ErrorActionPreference = "Continue"
$RepoRoot = "C:\workspace\agi"
$LogFile = "$RepoRoot\outputs\cache_validation_monitor.log"
$ScheduleFile = "$RepoRoot\outputs\cache_validation_schedule.json"
$StateFile = "$RepoRoot\outputs\cache_validation_state.json"
$ValidationScript = "$RepoRoot\scripts\auto_cache_validation.ps1"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logLine = "[$timestamp] [$Level] $Message"
    Add-Content -Path $LogFile -Value $logLine -Encoding UTF8
    
    if ($Level -eq "ERROR") {
        Write-Host $logLine -ForegroundColor Red
    }
    elseif ($Level -eq "WARN") {
        Write-Host $logLine -ForegroundColor Yellow
    }
    else {
        Write-Host $logLine -ForegroundColor Gray
    }
}

function Load-Schedule {
    if (Test-Path $ScheduleFile) {
        try {
            return Get-Content $ScheduleFile -Raw | ConvertFrom-Json
        }
        catch {
            Write-Log "Failed to load schedule: $_" "ERROR"
            return $null
        }
    }
    return $null
}

function Load-State {
    if (Test-Path $StateFile) {
        try {
            return Get-Content $StateFile -Raw | ConvertFrom-Json
        }
        catch {
            Write-Log "Failed to load state: $_" "WARN"
        }
    }
    return @{
        executed_12h = $false
        executed_24h = $false
        executed_7d  = $false
        last_check   = $null
    }
}

function Save-State {
    param($State)
    try {
        $State | ConvertTo-Json | Out-File -FilePath $StateFile -Encoding UTF8
    }
    catch {
        Write-Log "Failed to save state: $_" "ERROR"
    }
}

function Should-ExecuteValidation {
    param($ScheduledTime, $AlreadyExecuted)
    
    if ($AlreadyExecuted) {
        return $false
    }
    
    $now = Get-Date
    $scheduled = [DateTime]::Parse($ScheduledTime)
    
    # Execute if current time is past scheduled time
    return $now -ge $scheduled
}

function Execute-Validation {
    param([string]$Checkpoint, [int]$Hours)
    
    Write-Log "?? Executing $Checkpoint validation..." "INFO"
    
    try {
        $output = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ValidationScript -Hours $Hours -SendNotification 2>&1
        
        Write-Log "??$Checkpoint validation completed" "INFO"
        Write-Log "Output: $output" "INFO"
        
        return $true
    }
    catch {
        Write-Log "??$Checkpoint validation failed: $_" "ERROR"
        return $false
    }
}

# Main daemon loop
Write-Log "?§ñ Cache Validation Monitor Daemon Started" "INFO"
Write-Log "   PID: $PID" "INFO"
Write-Log "   Check interval: 5 minutes" "INFO"

$checkInterval = 300 # 5 minutes in seconds
$loopCount = 0

while ($true) {
    try {
        $loopCount++
        $schedule = Load-Schedule
        
        if (-not $schedule) {
            Write-Log "?†Ô∏è  No schedule found, waiting..." "WARN"
            Start-Sleep -Seconds $checkInterval
            continue
        }
        
        $state = Load-State
        $now = Get-Date
        $state.last_check = $now.ToString("yyyy-MM-dd HH:mm:ss")
        
        # Check 12h validation
        if (Should-ExecuteValidation -ScheduledTime $schedule.Check12h -AlreadyExecuted $state.executed_12h) {
            Write-Log "??12h checkpoint reached!" "INFO"
            if (Execute-Validation -Checkpoint "12h" -Hours 12) {
                $state.executed_12h = $true
                Save-State $state
            }
        }
        
        # Check 24h validation
        if (Should-ExecuteValidation -ScheduledTime $schedule.Check24h -AlreadyExecuted $state.executed_24h) {
            Write-Log "??24h checkpoint reached!" "INFO"
            if (Execute-Validation -Checkpoint "24h" -Hours 24) {
                $state.executed_24h = $true
                Save-State $state
            }
        }
        
        # Check 7d validation
        if (Should-ExecuteValidation -ScheduledTime $schedule.Check7d -AlreadyExecuted $state.executed_7d) {
            Write-Log "??7d checkpoint reached!" "INFO"
            if (Execute-Validation -Checkpoint "7d" -Hours 168) {
                $state.executed_7d = $true
                Save-State $state
                
                # All validations complete, daemon can stop
                Write-Log "??All validations complete! Daemon stopping." "INFO"
                break
            }
        }
        
        # Save state after each check
        Save-State $state
        
        # Log heartbeat every 12 checks (1 hour)
        if ($loopCount % 12 -eq 0) {
            Write-Log "?íì Heartbeat #$loopCount - Next check in 5 minutes" "INFO"
            Write-Log "   Status: 12h=$($state.executed_12h) | 24h=$($state.executed_24h) | 7d=$($state.executed_7d)" "INFO"
        }
        
        # Wait for next check
        Start-Sleep -Seconds $checkInterval
        
    }
    catch {
        Write-Log "??Error in monitor loop: $_" "ERROR"
        Start-Sleep -Seconds 60 # Wait 1 minute on error
    }
}

Write-Log "?õë Cache Validation Monitor Daemon Stopped" "INFO"
