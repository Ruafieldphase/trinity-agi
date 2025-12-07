# AGI Windows Auto-Start Setup
# =============================
# Creates Windows Task Scheduler task to auto-start Shion daemon on boot

param(
    [switch]$Remove  # Remove the scheduled task instead of creating it
)

$TaskName = "AGI_Shion_AutoStart"
$ScriptPath = Join-Path $PSScriptRoot "autonomous_collaboration_daemon.ps1"
$WorkingDir = Split-Path -Parent $PSScriptRoot

function Create-AutoStartTask {
    Write-Host "Setting up AGI Shion Auto-Start..." -ForegroundColor Cyan

    # Check if task already exists
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "⚠️  Task '$TaskName' already exists. Removing..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }

    # Create action
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`" -Action start" `
        -WorkingDirectory $WorkingDir

    # Create trigger (at startup, with 30 second delay to ensure network is ready)
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $trigger.Delay = "PT30S"

    # Create settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1)

    # Create principal (run as current user)
    $principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -LogonType Interactive `
        -RunLevel Limited

    # Register task
    try {
        Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Principal $principal `
            -Description "Auto-starts AGI Shion Auto-Responder daemon on Windows boot" `
            -ErrorAction Stop

        Write-Host "✅ Task '$TaskName' created successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Configuration:" -ForegroundColor Cyan
        Write-Host "  - Trigger: At system startup (30s delay)"
        Write-Host "  - Action: Start Shion daemon"
        Write-Host "  - Auto-restart: Yes (up to 3 times)"
        Write-Host ""
        Write-Host "To test manually:" -ForegroundColor Yellow
        Write-Host "  Start-ScheduledTask -TaskName '$TaskName'"
        Write-Host ""
        Write-Host "To view status:" -ForegroundColor Yellow
        Write-Host "  Get-ScheduledTask -TaskName '$TaskName' | Select-Object State,LastRunTime"

    }
    catch {
        Write-Host "❌ Failed to create scheduled task: $_" -ForegroundColor Red
        exit 1
    }
}

function Remove-AutoStartTask {
    Write-Host "Removing AGI Shion Auto-Start task..." -ForegroundColor Cyan

    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        try {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
            Write-Host "✅ Task '$TaskName' removed successfully!" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Failed to remove task: $_" -ForegroundColor Red
            exit 1
        }
    }
    else {
        Write-Host "⚠️  Task '$TaskName' not found." -ForegroundColor Yellow
    }
}

# Main execution
if ($Remove) {
    Remove-AutoStartTask
}
else {
    Create-AutoStartTask
}
