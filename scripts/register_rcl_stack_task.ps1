<#
.SYNOPSIS
RCL Stack 자동 시작용 Windows 작업 등록기

.DESCRIPTION
Harmony Core Runner + Secure Bridge + Feedback Worker를 한 번에 켜는
`manage_rcl_stack.ps1`를 로그인 시 자동 실행하도록 Scheduled Task를 등록/관리합니다.

.PARAMETER Action
Register / Unregister / Status / RunNow (기본 Status)

.PARAMETER TaskName
생성할 작업 이름 (기본 RCLStackAutoStart)

.PARAMETER AdjustSecret
HMAC 서명에 사용할 비밀. 지정 시 사용자 환경 변수(RCL_ADJUST_SECRET, ADJUST_SECRET)를 갱신합니다.
지정하지 않으면 기존 환경 변수 값을 사용해야 합니다.

.PARAMETER RunnerPort
Harmony Core Runner 포트 (기본 8090)

.PARAMETER BridgePort
Secure Bridge 포트 (기본 8091)

.PARAMETER TickHz
Runner 틱 주파수 (기본 30)

.PARAMETER FeedbackIntervalSec
Feedback Worker 주기 (초, 기본 5)

.PARAMETER HiddenWindow
작업 실행 시 콘솔을 숨김 (기본 true)

.EXAMPLE
.\register_rcl_stack_task.ps1 -Action Register -AdjustSecret rcl_bridge_secret

.EXAMPLE
.\register_rcl_stack_task.ps1 -Action RunNow
#>

[CmdletBinding()]
param(
    [ValidateSet("Register", "Unregister", "Status", "RunNow")]
    [string]$Action = "Status",

    [string]$TaskName = "RCLStackAutoStart",

    [string]$AdjustSecret,
    [int]$RunnerPort = 8090,
    [int]$BridgePort = 8091,
    [int]$TickHz = 30,
    [int]$FeedbackIntervalSec = 5,
[switch]$HiddenWindow
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $PSBoundParameters.ContainsKey("HiddenWindow")) {
    $HiddenWindow = $true
}

$manageScript = Join-Path $PSScriptRoot "manage_rcl_stack.ps1"
if (-not (Test-Path $manageScript)) {
    throw "manage_rcl_stack.ps1 not found: $manageScript"
}

function Ensure-Secret {
    param([string]$Secret)
    if ($Secret) {
        [Environment]::SetEnvironmentVariable("RCL_ADJUST_SECRET", $Secret, "User")
        [Environment]::SetEnvironmentVariable("ADJUST_SECRET", $Secret, "User")
        $env:RCL_ADJUST_SECRET = $Secret
        $env:ADJUST_SECRET = $Secret
        return
    }
    $existing = [Environment]::GetEnvironmentVariable("RCL_ADJUST_SECRET", "User")
    if (-not $existing) {
        $existing = [Environment]::GetEnvironmentVariable("ADJUST_SECRET", "User")
    }
    if (-not $existing) {
        throw "Adjust secret not provided. Pass -AdjustSecret once or set RCL_ADJUST_SECRET user env var."
    }
}

function Get-Task {
    try {
        return Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    }
    catch {
        return $null
    }
}

function Register-Task {
    Ensure-Secret -Secret $AdjustSecret

    $arguments = @(
        "-NoProfile"
        "-ExecutionPolicy Bypass"
        "-File `"$manageScript`""
        "-Action Start"
        "-RunnerPort $RunnerPort"
        "-BridgePort $BridgePort"
        "-TickHz $TickHz"
        "-FeedbackIntervalSec $FeedbackIntervalSec"
    )
    $windowSwitch = if ($HiddenWindow) { "-WindowStyle Hidden" } else { "" }
    if ($windowSwitch) {
        $arguments = @($windowSwitch) + $arguments
    }
    $argumentString = ($arguments | Where-Object { $_ -ne "" }) -join " "

    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $argumentString
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
        -Description "Auto-start RCL stack (Runner/Bridge/Feedback Worker)" `
        -Settings $settings -User $env:USERNAME -Force | Out-Null

    Write-Host "✅ Scheduled Task '$TaskName' registered (logon trigger)." -ForegroundColor Green
}

function Unregister-Task {
    if (Get-Task) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "🗑️  Scheduled Task '$TaskName' removed." -ForegroundColor Yellow
    }
    else {
        Write-Host "ℹ️  Task '$TaskName' not found." -ForegroundColor Cyan
    }
}

function Show-Status {
    $task = Get-Task
    if ($task) {
        $info = @{
            TaskName = $task.TaskName
            State    = $task.State
            NextRun  = $task.NextRunTime
            LastRun  = $task.LastRunTime
        }
        $info.GetEnumerator() | ForEach-Object {
            Write-Host ("{0,-10}: {1}" -f $_.Key, $_.Value)
        }
    }
    else {
        Write-Host "⚪ Task '$TaskName' not found." -ForegroundColor Gray
    }
}

function Run-Now {
    $task = Get-Task
    if (-not $task) {
        throw "Task '$TaskName' not registered."
    }
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "▶️  Task '$TaskName' started." -ForegroundColor Green
}

switch ($Action) {
    "Register" { Register-Task }
    "Unregister" { Unregister-Task }
    "Status" { Show-Status }
    "RunNow" { Run-Now }
}