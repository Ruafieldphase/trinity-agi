param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [string]$TaskName = "MonitoringSnapshotRotationDaily",
    [string]$Time = "03:15",
    [string]$WorkspaceRoot = "D:\\nas_backup",
    [string]$RotateScript = "D:\\nas_backup\\scripts\\rotate_status_snapshots.ps1",
    [string]$FilePath = "D:\\nas_backup\\outputs\\status_snapshots.jsonl",
    [string]$ArchiveDir = "D:\\nas_backup\\outputs\\archive",
    [int]$MaxLines = 50000,
    [int]$MaxSizeMB = 50,
    [int]$RetentionDays = 30,
    [switch]$Zip,
    [switch]$DryRun,
    [switch]$RunNow,
    [switch]$NoWake,
    [switch]$AllowOnBatteries,
    [string]$Description = "Rotate status snapshots daily when exceeding thresholds (lines/size).",
    [string]$LogPath,
    [switch]$RunAsSystem,
    [string]$TaskUser,
    [string]$TaskPassword,
    [string]$TaskFolder
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO] $msg" }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

if (-not (Test-Path $RotateScript)) {
    Write-Err "Rotate script not found: $RotateScript"
    exit 1
}

if ( ($Register -and $Unregister) -or ($Register -and $Status) -or ($Unregister -and $Status) ) {
    Write-Err "Use exactly one action among -Register, -Unregister, -Status."
    exit 1
}

if (-not $Register -and -not $Unregister -and -not $Status) {
    Write-Warn "No action specified. Use -Register, -Unregister or -Status."
    exit 2
}

# Validate principal options
if ($RunAsSystem -and $TaskUser) {
    Write-Err "Use either -RunAsSystem or -TaskUser/-TaskPassword, not both."
    exit 1
}
if ($TaskPassword -and -not $TaskUser) {
    Write-Err "-TaskPassword requires -TaskUser."
    exit 1
}

# Normalize task path (folder)
$taskPath = "\\"  # default root
if ($TaskFolder) {
    $taskPath = $TaskFolder
    if (-not $taskPath.StartsWith("\\")) { $taskPath = "\\" + $taskPath }
    if (-not $taskPath.EndsWith("\\")) { $taskPath += "\\" }
}

# Build PowerShell arguments
$rotateArgsBase = "-NoProfile -ExecutionPolicy Bypass -File `"$RotateScript`" -FilePath `"$FilePath`" -ArchiveDir `"$ArchiveDir`" -MaxLines $MaxLines -MaxSizeMB $MaxSizeMB -RetentionDays $RetentionDays"
if ($Zip) { $rotateArgsBase += " -Zip" }

# The scheduled task should never persist -DryRun; only ad-hoc runs can.
$rotateArgsForTask = $rotateArgsBase
$rotateArgsForRunOnce = $rotateArgsBase
if ($DryRun) { $rotateArgsForRunOnce += " -DryRun" }

# Optional log redirection
if ($LogPath) {
    try {
        $logDir = Split-Path -Path $LogPath -Parent
        if ($logDir -and -not (Test-Path $logDir)) {
            New-Item -Path $logDir -ItemType Directory -Force | Out-Null
        }
    } catch {
        Write-Err "Failed to prepare LogPath directory: $($_.Exception.Message)"
        exit 1
    }
    # Redirect all streams in PowerShell for the scheduled task
    $rotateArgsForTask += " *> `"$LogPath`""
}

if ($Register) {
    Write-Info "Registering snapshot rotation task '$TaskName' at $Time daily"
    if ($DryRun) {
        Write-Warn "-DryRun is not persisted in the scheduled task. It applies only to one-off runs (use with -RunNow to verify)."
    }

    # Parse time (HH:mm)
    try {
        $today = Get-Date
        $runAt = Get-Date ("{0} {1}" -f $today.ToString('yyyy-MM-dd'), $Time)
        if ($runAt -lt $today) { $runAt = $runAt.AddDays(1) }
    }
    catch {
        Write-Err "Invalid -Time format. Use HH:mm (e.g., 03:15)."
        exit 1
    }

    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $rotateArgsForTask -WorkingDirectory $WorkspaceRoot
    $trigger = New-ScheduledTaskTrigger -Once -At $runAt -RepetitionInterval (New-TimeSpan -Days 1) -RepetitionDuration (New-TimeSpan -Days 3650)

    # Settings: power policy and wake behavior
    $allowStartIfOnBatteries = $false
    $dontStopIfGoingOnBatteries = $false
    if ($AllowOnBatteries) {
        $allowStartIfOnBatteries = $true
        $dontStopIfGoingOnBatteries = $true
    }

    if ($NoWake) {
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries:$allowStartIfOnBatteries -DontStopIfGoingOnBatteries:$dontStopIfGoingOnBatteries -StartWhenAvailable
$settings.Hidden = $true
    }
    else {
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries:$allowStartIfOnBatteries -DontStopIfGoingOnBatteries:$dontStopIfGoingOnBatteries -StartWhenAvailable
$settings.Hidden = $true -WakeToRun
    }
    # Choose principal
    $principal = $null
    if ($RunAsSystem) {
        Write-Info "Using SYSTEM account for scheduled task."
        $principal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\\SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    }
    elseif ($TaskUser) {
        Write-Info "Task will run under specified user '$TaskUser' (credentials used at registration)."
        # With -User/-Password we must not pass -Principal later
    }
    else {
        $who = $env:USERNAME
        Write-Info "Using interactive user for scheduled task: $who"
        $principal = New-ScheduledTaskPrincipal -UserId $who -LogonType Interactive -RunLevel Limited
    }

    try {
        if (Get-ScheduledTask -TaskName $TaskName -TaskPath $taskPath -ErrorAction SilentlyContinue) {
            Unregister-ScheduledTask -TaskName $TaskName -TaskPath $taskPath -Confirm:$false
            Write-Info "Existing task '$TaskName' removed."
        }
        if ($TaskUser) {
            if (-not $TaskPassword) {
                Write-Err "-TaskUser requires -TaskPassword to register the task."
                exit 1
            }
            Register-ScheduledTask -TaskName $TaskName -TaskPath $taskPath -Action $action -Trigger $trigger -Settings $settings -User $TaskUser -Password $TaskPassword -Description $Description | Out-Null
        }
        elseif ($principal) {
            Register-ScheduledTask -TaskName $TaskName -TaskPath $taskPath -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description $Description | Out-Null
        }
        else {
            # Fallback (shouldn't happen): interactive
            Register-ScheduledTask -TaskName $TaskName -TaskPath $taskPath -Action $action -Trigger $trigger -Settings $settings -Description $Description | Out-Null
        }
        Write-Info "Task '$TaskName' registered for daily run at $Time."
        Write-Info "You can trigger it with: Start-ScheduledTask -TaskName '$TaskName' -TaskPath '$taskPath'"

        # Show next run info
        try {
            $info = Get-ScheduledTaskInfo -TaskName $TaskName -TaskPath $taskPath
            Write-Info ("NextRunTime: {0}, LastRunTime: {1}, LastTaskResult: {2}" -f $info.NextRunTime, $info.LastRunTime, $info.LastTaskResult)
        } catch { }

        if (-not $NoWake) {
            Write-Warn "WakeToRun is enabled. If the PC doesn't wake as expected, verify wake timer support (e.g., run fdo_agi_repo\\scripts\\check_wake_timer_support.ps1)."
        }

        if ($RunNow) {
            if ($DryRun) {
                Write-Warn "-DryRun was provided. The scheduled task does NOT persist DryRun. Executing a one-off DryRun now for verification."
                & powershell.exe $rotateArgsForRunOnce
            }
            else {
                Write-Info "Running task now (-RunNow) to verify configuration..."
                Start-ScheduledTask -TaskName $TaskName -TaskPath $taskPath
            }
        }
    }
    catch {
        Write-Err "Failed to register rotation task: $($_.Exception.Message)"
        exit 1
    }
}
elseif ($Unregister) {
    Write-Info "Unregistering snapshot rotation task '$TaskName'"
    try {
        if (Get-ScheduledTask -TaskName $TaskName -TaskPath $taskPath -ErrorAction SilentlyContinue) {
            Unregister-ScheduledTask -TaskName $TaskName -TaskPath $taskPath -Confirm:$false
            Write-Info "Task '$TaskName' removed."
        }
        else {
            Write-Warn "Task '$TaskName' not found. Nothing to do."
        }
    }
    catch {
        Write-Err "Failed to unregister task: $($_.Exception.Message)"
        exit 1
    }
}
elseif ($Status) {
    Write-Info "Status for scheduled task '$TaskName'"
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -TaskPath $taskPath -ErrorAction SilentlyContinue
        if (-not $task) {
            Write-Warn "Task '$TaskName' not found."
            Write-Info "Register with: powershell -NoProfile -File scripts\\register_snapshot_rotation_task.ps1 -Register -Time '$Time'"
            exit 3
        }

        $info = Get-ScheduledTaskInfo -TaskName $TaskName -TaskPath $taskPath
        Write-Info ("State: {0}" -f $task.State)
        Write-Info ("WakeToRun: {0}" -f $task.Settings.WakeToRun)
        Write-Info ("StartWhenAvailable: {0}" -f $task.Settings.StartWhenAvailable)
        Write-Info ("NextRunTime: {0}" -f $info.NextRunTime)
        Write-Info ("LastRunTime: {0}" -f $info.LastRunTime)
        Write-Info ("LastTaskResult: {0}" -f $info.LastTaskResult)
        Write-Info ("TaskPath: {0}" -f $taskPath)

        if ($task.Triggers) {
            foreach ($t in $task.Triggers) {
                Write-Info ("Trigger: {0}" -f $t)
            }
        }

        if ($task.Actions) {
            foreach ($a in $task.Actions) {
                Write-Info ("Action: {0} {1}" -f $a.Execute, $a.Arguments)
            }
        }
        if ($LogPath) {
            Write-Info "LogPath (requested): $LogPath"
        }
    }
    catch {
        Write-Err "Failed to query task status: $($_.Exception.Message)"
        exit 1
    }
}
