<#
Register Trigger Automation (Windows)

목표:
- "코어(무의식) → 트리거 파일 생성 → 루빛(실행) 처리"를 Windows에서도 안정적으로 돌린다.
- 관리자 권한 없이(Interactive, Limited) 등록 가능한 방식만 사용한다.
- 백그라운드(창 없음): pythonw.exe 사용.

구성:
- AGI_LuaAutoPolicy: 주기적으로 `scripts/self_expansion/auto_policy.py`를 실행해 트리거 파일을 생성(덮어쓰기 금지).
- AGI_TriggerOnce: 주기적으로 `scripts/run_trigger_once.py`를 실행해 트리거가 있으면 1회 처리.

주의:
- Task Scheduler의 OnLogon/AtStartup 트리거는 환경에 따라 권한 제약이 있을 수 있어,
  여기서는 "Once + Repetition + StartWhenAvailable" 조합을 사용한다.
#>

param(
    [switch]$Silent
)

$ErrorActionPreference = 'Continue'

try {
    $ws = Split-Path -Parent $PSScriptRoot
    $pythonw = Join-Path $ws '.venv\Scripts\pythonw.exe'
    if (-not (Test-Path $pythonw)) { $pythonw = 'pythonw.exe' }

    function Register-RepeatTask {
        param(
            [Parameter(Mandatory=$true)][string]$Name,
            [Parameter(Mandatory=$true)][string]$ScriptRel,
            [Parameter(Mandatory=$true)][TimeSpan]$Interval,
            [Parameter(Mandatory=$true)][TimeSpan]$MaxRuntime,
            [int]$DelaySeconds = 15
        )

        $scriptPath = Join-Path $ws $ScriptRel
        if (-not (Test-Path $scriptPath)) { throw "missing script: $scriptPath" }

        try { Unregister-ScheduledTask -TaskName $Name -Confirm:$false -ErrorAction SilentlyContinue | Out-Null } catch { }

        $action = New-ScheduledTaskAction -Execute $pythonw -Argument $scriptPath -WorkingDirectory $ws
        $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddSeconds($DelaySeconds) -RepetitionInterval $Interval -RepetitionDuration (New-TimeSpan -Days 3650)
        $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
        $settings = New-ScheduledTaskSettingsSet `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -ExecutionTimeLimit $MaxRuntime `
            -StartWhenAvailable `
            -Hidden `
            -MultipleInstances IgnoreNew

        Register-ScheduledTask -TaskName $Name -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
        Start-ScheduledTask -TaskName $Name | Out-Null
    }

    Register-RepeatTask -Name 'AGI_TriggerOnce' -ScriptRel 'scripts\run_trigger_once.py' -Interval (New-TimeSpan -Minutes 1) -MaxRuntime (New-TimeSpan -Hours 6) -DelaySeconds 10
    Register-RepeatTask -Name 'AGI_LuaAutoPolicy' -ScriptRel 'scripts\self_expansion\auto_policy.py' -Interval (New-TimeSpan -Minutes 5) -MaxRuntime (New-TimeSpan -Minutes 5) -DelaySeconds 20

    # Browser exploration suggestion (Windows supervised body, only when armed + idle)
    Register-RepeatTask -Name 'AGI_BrowserSuggest' -ScriptRel 'scripts\windows\suggest_browser_exploration_task.py' -Interval (New-TimeSpan -Minutes 10) -MaxRuntime (New-TimeSpan -Minutes 2) -DelaySeconds 30

    if (-not $Silent) {
        Get-ScheduledTask | Where-Object { $_.TaskName -in @('AGI_TriggerOnce','AGI_LuaAutoPolicy','AGI_BrowserSuggest') } |
            Select-Object TaskName, State |
            Format-Table -AutoSize
    }
}
catch {
    if (-not $Silent) { Write-Host ("register trigger automation error: " + $_.Exception.Message) -ForegroundColor Yellow }
}
finally {
    try { [Environment]::Exit(0) } catch { exit 0 }
}