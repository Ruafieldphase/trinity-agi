param(
    [string]$TaskName = "AGI_ForcedEvidenceCheck_Daily",
    [string]$Time = "03:00",
    [int]$LastHours = 24,
    [int]$MinAdded = 1,
    [switch]$SendAlert,
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Once,
    [string]$User,
    [securestring]$Password
)

$ErrorActionPreference = 'Stop'

function Get-RepoRoot {
    $here = Split-Path -Parent $PSCommandPath
    $candidate = Split-Path -Parent $here
    # If already at fdo_agi_repo, return it; else navigate up to workspace root
    if ($candidate -match 'fdo_agi_repo$') { return Split-Path -Parent $candidate }
    return $candidate
}

function Get-TaskExists([string]$name) {
    try {
        Get-ScheduledTask -TaskName $name -ErrorAction Stop | Out-Null
        return $true
    }
    catch { return $false }
}

function New-TaskAction([string]$repoRoot, [int]$lastHours, [int]$minAdded, [switch]$sendAlert) {
    $psExe = (Get-Command powershell.exe -ErrorAction Stop).Source
    $script = Join-Path $repoRoot 'fdo_agi_repo\scripts\run_forced_evidence_check.ps1'
    if (-not (Test-Path -LiteralPath $script)) { throw "Script not found: $script" }

    $psArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $script, '-LastHours', $lastHours, '-MinAdded', $minAdded)
    if ($sendAlert) { $psArgs += '-SendAlert' }

    return New-ScheduledTaskAction -Execute $psExe -Argument ($psArgs -join ' ')
}

function New-TaskTrigger([string]$time, [switch]$once) {
    if ($once) {
        $dt = [datetime]::ParseExact($time, 'HH:mm', $null)
        $todayRun = (Get-Date -Hour $dt.Hour -Minute $dt.Minute -Second 0)
        if ($todayRun -lt (Get-Date)) { $todayRun = $todayRun.AddDays(1) }
        return New-ScheduledTaskTrigger -Once -At $todayRun
    }
    else {
        $parts = $time.Split(':')
        if ($parts.Count -lt 2) { throw "Invalid time format. Use HH:mm (e.g. 03:00)" }
        $h = [int]$parts[0]; $m = [int]$parts[1]
        return New-ScheduledTaskTrigger -Daily -At (Get-Date -Hour $h -Minute $m -Second 0)
    }
}

function New-TaskPrincipal([string]$user, [securestring]$password) {
    if ($user -and $password) {
        return New-ScheduledTaskPrincipal -UserId $user -LogonType Password -RunLevel Highest
    }
    else {
        # Current user, highest privileges
        return New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
    }
}

try {
    $repoRoot = Get-RepoRoot

    if ($Unregister) {
        if (Get-TaskExists -name $TaskName) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
            Write-Host "Scheduled task removed: $TaskName" -ForegroundColor Yellow
        }
        else {
            Write-Host "Scheduled task not found: $TaskName" -ForegroundColor DarkYellow
        }
        exit 0
    }

    # Default to Register when no explicit action
    if (-not $Register -and -not $Unregister) { $Register = $true }

    if ($Register) {
        $action = New-TaskAction -repoRoot $repoRoot -lastHours $LastHours -minAdded $MinAdded -sendAlert:$SendAlert
        $trigger = New-TaskTrigger -time $Time -once:$Once
        $principal = New-TaskPrincipal -user $User -password $Password

        if (Get-TaskExists -name $TaskName) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
        }

        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
$settings.Hidden = $true
        $task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings

        if ($User -and $Password) {
            Register-ScheduledTask -TaskName $TaskName -InputObject $task -User $User -Password (New-Object System.Net.NetworkCredential('u', $Password).Password) -Force | Out-Null
        }
        else {
            Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null
        }

        Write-Host "Scheduled task registered: $TaskName @ $Time (Daily=$(-not $Once))" -ForegroundColor Green
        Write-Host "Action: run_forced_evidence_check.ps1 -LastHours $LastHours -MinAdded $MinAdded $(if($SendAlert){'-SendAlert'})" -ForegroundColor Gray
        exit 0
    }
}
catch {
    Write-Error $_
    exit 1
}
