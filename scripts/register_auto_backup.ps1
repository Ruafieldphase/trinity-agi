#Requires -Version 5.1
<#
.SYNOPSIS
    Windows Scheduled Task 등록 - 자동 백업을 매일 03:30에 실행
.DESCRIPTION
    매일 03:30에 자동으로 백업 스크립트를 실행하여 핵심 파일을 보호합니다.
#>

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [string]$TaskName = "AGI_Auto_Backup",
    [string]$Time = "03:30"
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$BackupScript = "$WorkspaceRoot\scripts\auto_backup.ps1"

function Show-Status {
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($task) {
            Write-Host "`n✓ Task '$TaskName' is registered" -ForegroundColor Green
            Write-Host "  State: $($task.State)" -ForegroundColor Cyan
            Write-Host "  Schedule: Daily at $Time" -ForegroundColor Cyan
            Write-Host "  Script: $BackupScript" -ForegroundColor Gray
            
            $info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue
            if ($info) {
                Write-Host "  Last Run: $($info.LastRunTime)" -ForegroundColor Gray
                Write-Host "  Last Result: $($info.LastTaskResult)" -ForegroundColor Gray
            }
        }
        else {
            Write-Host "`n✗ Task '$TaskName' is NOT registered" -ForegroundColor Yellow
            Write-Host "  Run with -Register to enable daily backups" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "`n✗ Error checking status: $($_.Exception.Message)" -ForegroundColor Red
    }
}

if ($Status -or (-not $Register -and -not $Unregister)) {
    Show-Status
    exit 0
}

if ($Unregister) {
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "`n✓ Task '$TaskName' unregistered" -ForegroundColor Green
        exit 0
    }
    catch {
        Write-Host "`n✗ Failed to unregister: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

if ($Register) {
    # Unregister if exists
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    
    # Create action
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$BackupScript`""
    
    # Create trigger (daily at specified time)
    $trigger = New-ScheduledTaskTrigger -Daily -At $Time
    
    # Create settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false `
        -DontStopOnIdleEnd `
        -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
        -WakeToRun
    
    # Create principal (run as current user, highest privileges)
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest
    
    # Register task
    try {
        Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Principal $principal `
            -Description "AGI Auto Backup - Daily backup of critical files at $Time" `
            -Force | Out-Null
        
        Write-Host "`n✓ Task '$TaskName' registered successfully" -ForegroundColor Green
        Write-Host "  Schedule: Daily at $Time" -ForegroundColor Cyan
        Write-Host "  Script: $BackupScript" -ForegroundColor Gray
        Write-Host "`nDaily backups will now run automatically!" -ForegroundColor Green
        
        # Show test option
        Write-Host "`nTest now:" -ForegroundColor Yellow
        Write-Host "  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
        
        exit 0
    }
    catch {
        Write-Host "`n✗ Failed to register: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}
