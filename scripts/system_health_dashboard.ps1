#Requires -Version 5.1
<parameter name="content">#Requires -Version 5.1
<#
.SYNOPSIS
    통합 상태 체크 대시보드 - 재부팅 후 모든 것이 정상인지 확인
.DESCRIPTION
    모든 핵심 프로세스와 설정을 자동으로 검증하고 시각적으로 표시합니다.
    문제 발견 시 자동 복구를 시도합니다.
#>

param(
    [switch]$AutoFix,
    [switch]$Quiet,
    [int]$ServerPort = 8091
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Continue"
$checks = @()

function Add-Check {
    param([string]$Name, [bool]$Pass, [string]$Details = "", [scriptblock]$FixAction = $null)
    $script:checks += @{
        name      = $Name
        pass      = $Pass
        details   = $Details
        fixAction = $FixAction
    }
}

function Show-Results {
    Write-Host "`n╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║   System Health Dashboard - Post-Reboot     ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════╝`n" -ForegroundColor Cyan
    
    $passed = 0
    $failed = 0
    
    foreach ($check in $script:checks) {
        $status = if ($check.pass) { "✓" } else { "✗" }
        $color = if ($check.pass) { "Green" } else { "Red" }
        
        Write-Host "  $status " -NoNewline -ForegroundColor $color
        Write-Host "$($check.name)" -NoNewline
        if ($check.details) {
            Write-Host " - $($check.details)" -ForegroundColor Gray
        }
        else {
            Write-Host ""
        }
        
        if ($check.pass) { $passed++ } else { $failed++ }
    }
    
    Write-Host "`n───────────────────────────────────────────────" -ForegroundColor Gray
    $totalPercent = [math]::Round(($passed / $script:checks.Count) * 100)
    Write-Host "  Status: $passed/$($script:checks.Count) checks passed ($totalPercent%)" -ForegroundColor Cyan
    
    if ($failed -eq 0) {
        Write-Host "  System Status: " -NoNewline
        Write-Host "🟢 ALL SYSTEMS OPERATIONAL" -ForegroundColor Green
    }
    elseif ($failed -le 2) {
        Write-Host "  System Status: " -NoNewline
        Write-Host "🟡 DEGRADED ($failed issues)" -ForegroundColor Yellow
    }
    else {
        Write-Host "  System Status: " -NoNewline
        Write-Host "🔴 CRITICAL ($failed failures)" -ForegroundColor Red
    }
    
    Write-Host "───────────────────────────────────────────────`n" -ForegroundColor Gray
    
    return ($failed -eq 0)
}

if (-not $Quiet) {
    Write-Host "Running system health checks..." -ForegroundColor Cyan
}

# Check 1: Task Queue Server
$serverHealthy = $false
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:${ServerPort}/api/health" -TimeoutSec 3 -UseBasicParsing -ErrorAction SilentlyContinue
    $serverHealthy = ($resp.StatusCode -eq 200)
}
catch { }

Add-Check -Name "Task Queue Server (8091)" -Pass $serverHealthy -Details $(if ($serverHealthy) { "Running" } else { "Not responding" }) -FixAction {
    & "$PSScriptRoot\ensure_task_queue_server.ps1" -Port 8091
}

# Check 2: RPA Worker
$workerRunning = (Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*rpa_worker.py*" }).Count -gt 0
Add-Check -Name "RPA Worker" -Pass $workerRunning -Details $(if ($workerRunning) { "Active" } else { "Not running" }) -FixAction {
    & "$PSScriptRoot\ensure_rpa_worker.ps1" -EnforceSingle
}

# Check 3: Monitoring Daemon
$monitorRunning = (Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*monitoring_daemon.py*" }).Count -gt 0
Add-Check -Name "Monitoring Daemon" -Pass $monitorRunning -Details $(if ($monitorRunning) { "Collecting metrics" } else { "Not running" })

# Check 4: Watchdog
$watchdogRunning = (Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*self_healing_watchdog.ps1*" }).Count -gt 0
Add-Check -Name "Self-Healing Watchdog" -Pass $watchdogRunning -Details $(if ($watchdogRunning) { "Monitoring" } else { "Not active" })

# Check 5: Master Orchestrator scheduled task
$masterTask = Get-ScheduledTask -TaskName "AGI_Master_Orchestrator" -ErrorAction SilentlyContinue
$masterTaskOk = ($null -ne $masterTask -and $masterTask.State -ne "Disabled")
Add-Check -Name "Auto-Start on Boot" -Pass $masterTaskOk -Details $(if ($masterTaskOk) { "Enabled" } else { "Not registered" }) -FixAction {
    & "$PSScriptRoot\register_master_orchestrator.ps1" -Register
}

# Check 6: Auto-Backup scheduled task
$backupTask = Get-ScheduledTask -TaskName "AGI_Auto_Backup" -ErrorAction SilentlyContinue
$backupTaskOk = ($null -ne $backupTask -and $backupTask.State -ne "Disabled")
Add-Check -Name "Daily Auto-Backup" -Pass $backupTaskOk -Details $(if ($backupTaskOk) { "Scheduled" } else { "Not configured" }) -FixAction {
    & "$PSScriptRoot\register_auto_backup.ps1" -Register
}

# Check 7: Python venv
$venvPython = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
$venvExists = Test-Path $venvPython
Add-Check -Name "Python Virtual Env" -Pass $venvExists -Details $(if ($venvExists) { "Ready" } else { "Missing" })

# Check 8: Recent outputs
$outputDir = "$WorkspaceRoot\outputs"
$recentOutput = $false
if (Test-Path $outputDir) {
    $latestFiles = Get-ChildItem -Path $outputDir -Filter "*latest*" -File -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-24) }
    $recentOutput = $latestFiles.Count -gt 0
}
Add-Check -Name "Recent Output Files (24h)" -Pass $recentOutput -Details $(if ($recentOutput) { "$($latestFiles.Count) files" } else { "No recent outputs" })

# Show results
$allPass = Show-Results

# Determine critical failures separately so exit code reflects only critical issues
$criticalNames = @(
    'Task Queue Server (8091)',
    'RPA Worker',
    'Python Virtual Env'
)
$criticalFailed = @($checks | Where-Object { -not $_.pass -and ($criticalNames -contains $_.name) })

# Auto-fix if requested
if ($AutoFix -and -not $allPass) {
    Write-Host "`n🔧 Attempting auto-fix..." -ForegroundColor Yellow
    $fixed = 0
    foreach ($check in $script:checks) {
        if (-not $check.pass -and $null -ne $check.fixAction) {
            Write-Host "  Fixing: $($check.name)..." -ForegroundColor Cyan
            try {
                & $check.fixAction
                $fixed++
            }
            catch {
                Write-Host "    Failed: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
    Write-Host "  ✓ $fixed issues fixed`n" -ForegroundColor Green

    # Re-evaluate key checks after AutoFix to update pass/fail status
    foreach ($check in $script:checks) {
        switch ($check.name) {
            'Task Queue Server (8091)' {
                try {
                    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:${ServerPort}/api/health" -TimeoutSec 3 -UseBasicParsing -ErrorAction SilentlyContinue
                    $isOk = ($resp.StatusCode -eq 200)
                    $check.pass = $isOk
                    $check.details = $(if ($isOk) { 'Running' } else { 'Not responding' })
                }
                catch { }
            }
            'RPA Worker' {
                $isOk = (Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*rpa_worker.py*" }).Count -gt 0
                $check.pass = $isOk
                $check.details = $(if ($isOk) { 'Active' } else { 'Not running' })
            }
            'Monitoring Daemon' {
                $isOk = (Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*monitoring_daemon.py*" }).Count -gt 0
                $check.pass = $isOk
                $check.details = $(if ($isOk) { 'Collecting metrics' } else { 'Not running' })
            }
            'Self-Healing Watchdog' {
                $isOk = (Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*self_healing_watchdog.ps1*" }).Count -gt 0
                $check.pass = $isOk
                $check.details = $(if ($isOk) { 'Monitoring' } else { 'Not active' })
            }
            'Auto-Start on Boot' {
                $task = Get-ScheduledTask -TaskName 'AGI_Master_Orchestrator' -ErrorAction SilentlyContinue
                $isOk = ($null -ne $task -and $task.State -ne 'Disabled')
                $check.pass = $isOk
                $check.details = $(if ($isOk) { 'Enabled' } else { 'Not registered' })
            }
            'Daily Auto-Backup' {
                $task = Get-ScheduledTask -TaskName 'AGI_Auto_Backup' -ErrorAction SilentlyContinue
                $isOk = ($null -ne $task -and $task.State -ne 'Disabled')
                $check.pass = $isOk
                $check.details = $(if ($isOk) { 'Scheduled' } else { 'Not configured' })
            }
            'Python Virtual Env' {
                $venvPython = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
                $isOk = Test-Path $venvPython
                $check.pass = $isOk
                $check.details = $(if ($isOk) { 'Ready' } else { 'Missing' })
            }
            'Recent Output Files (24h)' {
                $outputDir = "$WorkspaceRoot\outputs"
                $isOk = $false
                $count = 0
                if (Test-Path $outputDir) {
                    $latestFiles = Get-ChildItem -Path $outputDir -Filter '*latest*' -File -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-24) }
                    $count = $latestFiles.Count
                    $isOk = $count -gt 0
                }
                $check.pass = $isOk
                $check.details = $(if ($isOk) { "$count files" } else { 'No recent outputs' })
            }
        }
    }

    # Refresh critical failure set after re-evaluation
    $criticalFailed = @($checks | Where-Object { -not $_.pass -and ($criticalNames -contains $_.name) })
    # Show updated summary (quiet)
    $null = Show-Results
}
# Exit with non-zero only when critical checks fail; treat non-critical misses as warnings
$exitCode = if ($criticalFailed.Count -gt 0) { 1 } else { 0 }
exit $exitCode