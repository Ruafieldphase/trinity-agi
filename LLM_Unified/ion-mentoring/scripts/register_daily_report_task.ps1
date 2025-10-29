# Requires: Windows PowerShell 5.1 or PowerShell 7+
# Usage:
#   .\register_daily_report_task.ps1 -ReportScriptPath "D:\nas_backup\LLM_Unified\ion-mentoring\scripts\generate_daily_report.ps1"

param(
    [Parameter(Mandatory = $true)]
    [string] $ReportScriptPath,

    [string] $TaskName = "ION Daily Report",
    [string] $StartTime = "08:00",
    [switch] $Force
)

if (-not (Test-Path $ReportScriptPath)) {
    throw "Report script not found: $ReportScriptPath"
}

try {
    $action = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ReportScriptPath`" -Hours 24"

    $trigger = New-ScheduledTaskTrigger -Daily -At $StartTime

    $options = @{
        TaskName = $TaskName
        Trigger  = $trigger
        Action   = $action
        RunLevel = "Highest"
    }
    if ($Force) {
        $options["Force"] = $true
    }

    Register-ScheduledTask @options

    $nextRun = Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo | Select-Object -ExpandProperty NextRunTime
    Write-Output "Scheduled task '$TaskName' registered. Next run: $nextRun"
}
catch {
    Write-Error "Failed to register scheduled task: $($_.Exception.Message)"
    throw
}
