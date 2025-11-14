<#
.SYNOPSIS
RCL(Harmony Runner + Secure Bridge + Feedback Worker) 통합 스택 관리자

.DESCRIPTION
루프 생명체 설계서에서 정의한 Harmony Core Runner(30Hz), Secure Bridge v1.3,
Feedback Worker를 PowerShell Job으로 실행/중지/상태 확인합니다.

.PARAMETER Action
Start / Stop / Status / Restart 중 선택 (기본 Status)

.PARAMETER AdjustSecret
Secure Bridge와 Feedback Worker가 사용할 HMAC 비밀 값.
미지정 시 환경 변수 ADJUST_SECRET 또는 RCL_ADJUST_SECRET을 사용.

.PARAMETER RunnerPort
Harmony Core Runner 포트 (기본 8090)

.PARAMETER BridgePort
Secure Bridge 포트 (기본 8091)

.PARAMETER TickHz
Runner 틱 주파수(Hz). 기본 30.

.PARAMETER FeedbackIntervalSec
Feedback Worker 주기(초). 기본 5.

.PARAMETER Force
Start 시 기존 Job이 있으면 강제로 중단 후 재시작.

.EXAMPLE
.\manage_rcl_stack.ps1 -Action Start -AdjustSecret rcl_bridge_secret

.EXAMPLE
.\manage_rcl_stack.ps1 -Action Status
#>

[CmdletBinding()]
param(
    [ValidateSet("Start", "Stop", "Status", "Restart")]
    [string]$Action = "Status",

    [string]$AdjustSecret,
    [int]$RunnerPort = 8090,
    [int]$BridgePort = 8091,
    [int]$TickHz = 30,
    [int]$FeedbackIntervalSec = 5,
    [switch]$Force,
    [switch]$OutputJson
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$workspaceRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $workspaceRoot ".venv\Scripts\python.exe"
$pythonExe = if (Test-Path $venvPython) { $venvPython } else { "python" }

$nodeExe = "node"

$runnerJob = "RCLHarmonyRunner"
$bridgeJob = "RCLSecureBridge"
$feedbackJob = "RCLFeedbackWorker"

function Get-JobSafe([string]$Name) {
    return Get-Job -Name $Name -ErrorAction SilentlyContinue
}

function Stop-JobSafe([string]$Name) {
    $job = Get-JobSafe $Name
    if ($job) {
        Stop-Job -Job $job -Force -ErrorAction SilentlyContinue
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    }
}

function Ensure-AdjustSecret([string]$Secret, [string]$Mode) {
    if ($Secret) { return $Secret }
    $candidate = $env:ADJUST_SECRET
    if (-not $candidate) { $candidate = $env:RCL_ADJUST_SECRET }
    if ($candidate) { return $candidate }
    throw "Adjust secret is required for '$Mode'. Provide -AdjustSecret or set ADJUST_SECRET."
}

function Start-RunnerJob($Python, $WorkspacePath, $Port, $TickHz) {
    if (Get-JobSafe $runnerJob) {
        if (-not $Force) {
            throw "Runner job already running. Use -Force or -Action Restart."
        }
        Stop-JobSafe $runnerJob
    }

    $scriptBlock = {
        param($pythonPath, $workspacePath, $port, $tickHz)
        $env:HARMONY_RUNNER_PORT = $port
        $env:HARMONY_TICK_HZ = $tickHz
        Set-Location $workspacePath
        & $pythonPath -m rcl_system.harmony_core_runner
    }

    Start-Job -Name $runnerJob -ScriptBlock $scriptBlock -ArgumentList $Python, $WorkspacePath, $Port, $TickHz | Out-Null
}

function Start-BridgeJob($Python, $WorkspacePath, $Port, $RunnerPort, $Secret) {
    if (Get-JobSafe $bridgeJob) {
        if (-not $Force) {
            throw "Bridge job already running. Use -Force or -Action Restart."
        }
        Stop-JobSafe $bridgeJob
    }

    $scriptBlock = {
        param($pythonPath, $workspacePath, $bridgePort, $runnerPort, $secret)
        $env:ADJUST_SECRET = $secret
        $env:RUNNER_URL = "http://127.0.0.1:$runnerPort"
        $env:RCL_BRIDGE_HOST = "127.0.0.1"
        $env:RCL_BRIDGE_PORT = $bridgePort
        Set-Location $workspacePath
        & $pythonPath -m rcl_system.bridge_server_v1_3
    }

    Start-Job -Name $bridgeJob -ScriptBlock $scriptBlock -ArgumentList $Python, $WorkspacePath, $Port, $RunnerPort, $Secret | Out-Null
}

function Start-FeedbackJob($Node, $WorkspacePath, $BridgePort, $RunnerPort, $Secret, $Interval) {
    if (Get-JobSafe $feedbackJob) {
        if (-not $Force) {
            throw "Feedback job already running. Use -Force or -Action Restart."
        }
        Stop-JobSafe $feedbackJob
    }

    $scriptBlock = {
        param($nodePath, $workspacePath, $bridgePort, $runnerPort, $secret, $interval)
        $env:ADJUST_SECRET = $secret
        $env:RCL_BRIDGE_URL = "http://127.0.0.1:$bridgePort"
        $env:HARMONY_STATUS_URL = "http://127.0.0.1:$runnerPort/status"
        $env:RCL_FEEDBACK_INTERVAL = $interval
        Set-Location $workspacePath
        & $nodePath scripts/feedback_worker.js
    }

    Start-Job -Name $feedbackJob -ScriptBlock $scriptBlock -ArgumentList $Node, $WorkspacePath, $BridgePort, $RunnerPort, $Secret, $Interval | Out-Null
}

function Show-Status {
    $status = [ordered]@{
        runner_port        = $RunnerPort
        bridge_port        = $BridgePort
        tick_hz            = $TickHz
        feedback_interval  = $FeedbackIntervalSec
        jobs               = @()
    }

    $jobs = @(
        @{ Name = $runnerJob; Job = Get-JobSafe $runnerJob },
        @{ Name = $bridgeJob; Job = Get-JobSafe $bridgeJob },
        @{ Name = $feedbackJob; Job = Get-JobSafe $feedbackJob }
    )

    foreach ($entry in $jobs) {
        $job = $entry.Job
        $status.jobs += [ordered]@{
            name    = $entry.Name
            running = [bool]$job
            state   = if ($job) { $job.State } else { $null }
            id      = if ($job) { $job.Id } else { $null }
            started = if ($job) { $job.PSBeginTime } else { $null }
        }
    }

    if ($OutputJson) {
        $status | ConvertTo-Json -Depth 5
        return
    }

    Write-Host "📡 RCL Stack Status" -ForegroundColor Cyan
    Write-Host "  Runner Port : $($status.runner_port)"
    Write-Host "  Bridge Port : $($status.bridge_port)"
    Write-Host "  Tick Hz     : $($status.tick_hz)"
    Write-Host "  Feedback Int: $($status.feedback_interval) sec"
    Write-Host ""

    foreach ($jobInfo in $status.jobs) {
        if ($jobInfo.running) {
            Write-Host "✅ $($jobInfo.name) → $($jobInfo.state) (Id=$($jobInfo.id), Started=$($jobInfo.started))"
        }
        else {
            Write-Host "⚪ $($jobInfo.name) → Not running"
        }
    }

    Write-Host ""
    Write-Host "ℹ️  로그 확인: Get-Job -Name <Name> | Receive-Job -Keep"

    return $status
}

switch ($Action) {
    "Start" {
        $secret = Ensure-AdjustSecret $AdjustSecret "Start"
        Start-RunnerJob $pythonExe $workspaceRoot $RunnerPort $TickHz
        Start-BridgeJob $pythonExe $workspaceRoot $BridgePort $RunnerPort $secret
        Start-FeedbackJob $nodeExe $workspaceRoot $BridgePort $RunnerPort $secret $FeedbackIntervalSec
        Start-Sleep -Seconds 1
        Show-Status
    }
    "Stop" {
        Stop-JobSafe $feedbackJob
        Stop-JobSafe $bridgeJob
        Stop-JobSafe $runnerJob
        Write-Host "🛑 모든 RCL Job 중지 완료" -ForegroundColor Yellow
        Show-Status
    }
    "Status" {
        Show-Status
    }
    "Restart" {
        $secret = Ensure-AdjustSecret $AdjustSecret "Restart"
        Stop-JobSafe $feedbackJob
        Stop-JobSafe $bridgeJob
        Stop-JobSafe $runnerJob
        Start-RunnerJob $pythonExe $workspaceRoot $RunnerPort $TickHz
        Start-BridgeJob $pythonExe $workspaceRoot $BridgePort $RunnerPort $secret
        Start-FeedbackJob $nodeExe $workspaceRoot $BridgePort $RunnerPort $secret $FeedbackIntervalSec
        Start-Sleep -Seconds 1
        Show-Status
    }
}
