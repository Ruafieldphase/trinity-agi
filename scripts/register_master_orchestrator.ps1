#Requires -Version 5.1
<#
.SYNOPSIS
    Windows Scheduled Task 등록 - Master Orchestrator를 로그온 시 자동 실행
.DESCRIPTION
    사용자가 로그인하면 자동으로 Master Orchestrator를 실행하여
    모든 핵심 프로세스를 시작합니다.
#>

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [string]$TaskName = "AGI_Master_Orchestrator"
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$MasterScript = "$WorkspaceRoot\scripts\master_orchestrator.ps1"
$RunRegPath = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$RunRegName = 'AGI_Master_Orchestrator'

function Get-RegistryStartup {
    try {
        $prop = Get-ItemProperty -Path $RunRegPath -Name $RunRegName -ErrorAction SilentlyContinue
        return $prop.$RunRegName
    }
    catch { return $null }
}

function Register-StartupViaRegistry {
    $inner = "Start-Sleep -Seconds 300; & '" + $MasterScript + "'"
    $cmd = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -Command `"$inner`""
    New-ItemProperty -Path $RunRegPath -Name $RunRegName -Value $cmd -PropertyType String -Force | Out-Null
}

function Unregister-StartupViaRegistry {
    Remove-ItemProperty -Path $RunRegPath -Name $RunRegName -ErrorAction SilentlyContinue
}

function Show-Status {
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($task) {
            Write-Host "`n✓ Task '$TaskName' is registered" -ForegroundColor Green
            Write-Host "  State: $($task.State)" -ForegroundColor Cyan
            Write-Host "  Trigger: At logon" -ForegroundColor Cyan
            Write-Host "  Script: $MasterScript" -ForegroundColor Gray
            
            # Show last run info
            $info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue
            if ($info) {
                Write-Host "  Last Run: $($info.LastRunTime)" -ForegroundColor Gray
                Write-Host "  Last Result: $($info.LastTaskResult)" -ForegroundColor Gray
            }
        }
        else {
            Write-Host "`n✗ Task '$TaskName' is NOT registered" -ForegroundColor Yellow
            Write-Host "  Run with -Register to enable auto-start on boot" -ForegroundColor Gray
        }
        $reg = Get-RegistryStartup
        if ($reg) {
            Write-Host "  ✓ Registry Run entry present (fallback): $RunRegName" -ForegroundColor Green
        }
        else {
            Write-Host "  ☐ Registry Run entry not present (fallback disabled)" -ForegroundColor DarkGray
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
        Unregister-StartupViaRegistry
        Write-Host "  ✓ Registry Run fallback removed" -ForegroundColor Green
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
        -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$MasterScript`""
    
    # Create trigger (at logon, with 5 minute delay for system stability)
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $trigger.Delay = "PT5M"  # 5 minutes delay (ISO 8601 duration)
    
    # Create settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false `
        -DontStopOnIdleEnd `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
    
    # Create principal (run as current user)
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive
    
    # Register task
    try {
        Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Principal $principal `
            -Description "AGI Master Orchestrator - Auto-starts all core processes on logon" `
            -Force | Out-Null
        
        Write-Host "`n✓ Task '$TaskName' registered successfully" -ForegroundColor Green
        Write-Host "  Trigger: At logon + 5 minutes delay (for system stability)" -ForegroundColor Cyan
        Write-Host "  Script: $MasterScript" -ForegroundColor Gray
        Write-Host "`nAll core processes will auto-start 5 minutes after you log in!" -ForegroundColor Green
        
        # Show test option
        Write-Host "`nTest now:" -ForegroundColor Yellow
        Write-Host "  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
        
        exit 0
    }
    catch {
        Write-Host "`n⚠️  Failed to register scheduled task: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "   Falling back to Registry Run (no admin required)." -ForegroundColor Yellow
        try {
            Register-StartupViaRegistry
            Write-Host "  ✓ Registry Run entry created. Master Orchestrator will auto-start ~5 minutes after logon." -ForegroundColor Green
            exit 0
        }
        catch {
            Write-Host "  ✗ Fallback failed: $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    }
}
