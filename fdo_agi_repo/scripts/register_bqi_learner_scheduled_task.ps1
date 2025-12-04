# Requires: Windows PowerShell 5.1+
# Purpose: Register/Unregister a daily Windows Scheduled Task to run the BQI learner.
[CmdletBinding(DefaultParameterSetName = 'Register')]
param(
    [Parameter(ParameterSetName = 'Register')]
    [switch] $Register,

    [Parameter(ParameterSetName = 'Unregister')]
    [switch] $Unregister,

    [Parameter(ParameterSetName = 'Register')]
    [string] $Time = '03:10',

    [string] $TaskName = 'BqiLearnerDaily'
)

$ErrorActionPreference = 'Stop'

function Get-RepoRoot {
    return (Split-Path -Parent $PSScriptRoot)
}

function Get-Pwsh {
    # Use Windows PowerShell to match environment used in the workspace
    return (Get-Command powershell).Source
}

function Get-RunScriptPath {
    param([string] $RepoRoot)
    return (Join-Path $RepoRoot 'scripts\run_bqi_learner.ps1')
}

try {
    $repo = Get-RepoRoot
    $runner = Get-RunScriptPath -RepoRoot $repo
    if (!(Test-Path $runner)) {
        throw "Runner script not found: $runner"
    }

    if ($PSCmdlet.ParameterSetName -eq 'Unregister' -or $Unregister) {
        if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Host "[BQI] Unregistered scheduled task: $TaskName" -ForegroundColor Yellow
        }
        else {
            Write-Host "[BQI] Scheduled task not found: $TaskName" -ForegroundColor Yellow
        }
        exit 0
    }

    # Register a daily task at the specified time
    $pwsh = Get-Pwsh
    $action = New-ScheduledTaskAction -Execute $pwsh -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runner`""
    $trigger = New-ScheduledTaskTrigger -Daily -At (Get-Date $Time)
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Limited -LogonType Interactive

    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null
    }

    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal | Out-Null
    Write-Host "[BQI] Registered scheduled task: $TaskName at $Time daily" -ForegroundColor Green
    Write-Host "       Action: $pwsh -NoProfile -ExecutionPolicy Bypass -File $runner"
    exit 0
}
catch {
    Write-Error $_
    exit 1
}
