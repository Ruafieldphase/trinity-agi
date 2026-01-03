param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [switch]$RunNow,
    [int]$IntervalMinutes = 120,
    [string]$TaskName = 'ReplanTrendUpdater'
)

$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host $msg -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host $msg -ForegroundColor Green }
function Write-Err($msg) { Write-Host $msg -ForegroundColor Red }

try {
    $ws = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
    $ps = Join-Path $ws 'scripts/generate_report_and_update_trend.ps1'
    if (-not (Test-Path -LiteralPath $ps)) {
        Write-Err "Missing script: $ps"
        exit 1
    }

    if ($Unregister) {
        if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Ok "Scheduled task '$TaskName' unregistered."
        }
        else {
            Write-Info "Scheduled task '$TaskName' not found."
        }
        exit 0
    }

    if ($Status) {
        $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($t) {
            $info = [PSCustomObject]@{
                TaskName = $t.TaskName
                State    = $t.State
                LastRun  = ($t | Get-ScheduledTaskInfo).LastRunTime
                NextRun  = ($t | Get-ScheduledTaskInfo).NextRunTime
                Interval = "$IntervalMinutes minutes (configured on register)"
            }
            $info | ConvertTo-Json -Depth 5 | Write-Output
        }
        else {
            Write-Info "Scheduled task '$TaskName' not found."
        }
        exit 0
    }

    if ($Register) {
        if ($IntervalMinutes -lt 5) { Write-Err "IntervalMinutes must be >= 5"; exit 1 }

        $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ps`" -Hours 24"
        $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Days 3650)

        if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        }

        $task = New-ScheduledTask -Action $action -Trigger $trigger -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable)
        Register-ScheduledTask -TaskName $TaskName -InputObject $task | Out-Null
        Write-Ok "Scheduled task '$TaskName' registered to run every $IntervalMinutes minutes."

        if ($RunNow) {
            Start-ScheduledTask -TaskName $TaskName
            Write-Info "Triggered first run for '$TaskName'."
        }
        $tinfo = Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo
        Write-Info ("NextRunTime: " + $tinfo.NextRunTime)
        exit 0
    }

    Write-Err "Please specify -Register, -Unregister, or -Status"
    exit 1
}
catch {
    Write-Err $_.Exception.Message
    exit 1
}