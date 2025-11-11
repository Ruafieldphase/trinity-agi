<#
.SYNOPSIS
Self-Care 텔레메트리 요약 작업을 Windows 작업 스케줄러에 등록/관리합니다.

.DESCRIPTION
`scripts/update_self_care_metrics.ps1`를 주기적으로 실행하여
`outputs/self_care_metrics_summary.json`을 최신 상태로 유지하도록 도와줍니다.

.PARAMETER Register
작업을 새로 등록합니다.

.PARAMETER Unregister
기존 작업을 제거합니다.

.PARAMETER Status
작업 등록 상태를 확인합니다.

.PARAMETER RunNow
작업을 즉시 실행합니다 (`Register` 없이도 사용 가능).

.PARAMETER TaskName
작업 스케줄러에 사용할 이름 (기본: "AGI Self-Care Metrics Rollup").

.PARAMETER IntervalMinutes
작업 반복 간격(분). 기본 60분.

.PARAMETER Hours
Python 집계 스크립트에 전달할 집계 범위(시간, 기본 24).

.PARAMETER PythonExe
집계 실행에 사용할 파이썬 실행 파일 경로 (기본 "python").

.PARAMETER WorkingDirectory
집계 스크립트를 실행할 작업 디렉터리 (기본: 저장소 루트).
#>
param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [switch]$RunNow,
    [string]$TaskName = "AGI Self-Care Metrics Rollup",
    [int]$IntervalMinutes = 60,
    [int]$Hours = 24,
    [string]$PythonExe = "python",
    [string]$WorkingDirectory
)

function Get-Task {
    param($Name)
    try {
        return Get-ScheduledTask -TaskName $Name -ErrorAction Stop
    }
    catch {
        return $null
    }
}

$RepoRoot = if ($WorkingDirectory) { Resolve-Path $WorkingDirectory } else { Split-Path -Parent $PSScriptRoot }
$ScriptPath = Join-Path $RepoRoot "scripts\update_self_care_metrics.ps1"

if (-not (Test-Path $ScriptPath)) {
    throw "update_self_care_metrics.ps1 not found at $ScriptPath"
}

if ($IntervalMinutes -lt 5) {
    throw "IntervalMinutes must be >= 5"
}

if ($Register) {
    $existing = Get-Task -Name $TaskName
    if ($existing) {
        Write-Warning "Task '$TaskName' already exists. Use -Unregister first if you need to replace it."
    }
    else {
        Write-Host "▶ Registering scheduled task '$TaskName'..."
        $argumentBuilder = @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", ("`"{0}`"" -f $ScriptPath),
            "-Hours", $Hours,
            "-PythonExe", ("`"{0}`"" -f $PythonExe)
        )
        $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ($argumentBuilder -join " ") -WorkingDirectory $RepoRoot
        $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1)
        $trigger.RepetitionInterval = (New-TimeSpan -Minutes $IntervalMinutes)
        $trigger.RepetitionDuration = [TimeSpan]::MaxValue

        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Description "Rolls up Self-Care telemetry metrics every $IntervalMinutes minutes."
        Write-Host "✅ Task '$TaskName' registered (interval: ${IntervalMinutes}m, hours: $Hours)."
    }
}

if ($Unregister) {
    if (Get-Task -Name $TaskName) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "🗑️ Task '$TaskName' removed."
    }
    else {
        Write-Warning "Task '$TaskName' is not registered."
    }
}

if ($Status) {
    $task = Get-Task -Name $TaskName
    if ($task) {
        $state = ($task.State.ToString())
        Write-Host "📌 Task '$TaskName' is registered. State: $state"
        $task.Triggers | ForEach-Object {
            Write-Host ("  - Trigger: {0}, Repetition: {1}" -f $_.StartBoundary, $_.Repetition.Interval)
        }
    }
    else {
        Write-Warning "Task '$TaskName' is not registered."
    }
}

if ($RunNow) {
    Write-Host "🚀 Running update_self_care_metrics.ps1 once..."
    Push-Location $RepoRoot
    try {
        & $ScriptPath -Hours $Hours -PythonExe $PythonExe -Json -OpenSummary
        if ($LASTEXITCODE -ne 0) {
            throw "update_self_care_metrics.ps1 exited with code $LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }
}
