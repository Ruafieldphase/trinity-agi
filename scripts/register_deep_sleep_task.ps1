# Deep Sleep Consolidation - Scheduled Task Registration (compat)
# docs/AGENT_HANDOFF.md의 `scripts/register_deep_sleep_task.ps1` 참조를 충족시키는 래퍼.
# 실제 실행은 `scripts/deep_sleep_consolidation.py`를 호출한다.

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [string]$Time = "03:00"
)

$TaskName = "AGI_Deep_Sleep_Consolidation"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$ScriptPath = Join-Path $WorkspaceRoot "scripts\\deep_sleep_consolidation.py"

# pythonw 우선(콘솔 팝업 최소화)
$PythonExe = "C:\\Python313\\pythonw.exe"
if (!(Test-Path -LiteralPath $PythonExe)) {
    $PythonExe = "pythonw"
}
if ($PythonExe -eq "pythonw") {
    # fallback: venv python.exe 또는 시스템 python
    $venvPy = Join-Path $WorkspaceRoot "fdo_agi_repo\\.venv\\Scripts\\python.exe"
    if (Test-Path -LiteralPath $venvPy) {
        $PythonExe = $venvPy
    } else {
        $PythonExe = "python"
    }
}

function Register-DeepSleepTask {
    Write-Host "🌙 Deep Sleep Consolidation Task 등록 중..." -ForegroundColor Cyan

    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }

    $action = New-ScheduledTaskAction `
        -Execute $PythonExe `
        -Argument "`"$ScriptPath`"" `
        -WorkingDirectory $WorkspaceRoot

    $trigger = New-ScheduledTaskTrigger -Daily -At $Time

    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false

    $principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -LogonType Interactive `
        -RunLevel Highest

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "AGI Deep Sleep Consolidation - Dream/Glymphatic/Memory pipeline wrapper" | Out-Null

    Write-Host "✅ Deep Sleep Task 등록 완료: $TaskName (매일 $Time)" -ForegroundColor Green
    Write-Host "   Script: $ScriptPath" -ForegroundColor Gray
    Write-Host "   Python: $PythonExe" -ForegroundColor Gray
}

function Unregister-DeepSleepTask {
    Write-Host "🗑️  Deep Sleep Task 제거 중..." -ForegroundColor Yellow
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✅ Task 제거 완료" -ForegroundColor Green
    } else {
        Write-Host "⚠️  등록된 Task가 없습니다." -ForegroundColor Yellow
    }
}

function Show-DeepSleepTaskStatus {
    Write-Host "📊 Deep Sleep Task 상태" -ForegroundColor Cyan
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "✅ Task 등록됨" -ForegroundColor Green
        Write-Host "   상태: $($task.State)" -ForegroundColor White
        Write-Host "   마지막 실행: $($task.LastRunTime)" -ForegroundColor Gray
        Write-Host "   다음 실행: $($task.NextRunTime)" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Task가 등록되지 않았습니다." -ForegroundColor Red
    }

    $resultJson = Join-Path $WorkspaceRoot "outputs\\deep_sleep_consolidation_latest.json"
    if (Test-Path -LiteralPath $resultJson) {
        try {
            $r = Get-Content $resultJson -Raw | ConvertFrom-Json
            Write-Host ""
            Write-Host "📁 최근 결과:" -ForegroundColor White
            Write-Host "   ok: $($r.ok)" -ForegroundColor White
            Write-Host "   timestamp: $($r.timestamp)" -ForegroundColor Gray
            Write-Host "   duration_sec: $($r.duration_sec)" -ForegroundColor Gray
        } catch {
            Write-Host "⚠️ 결과 파일 파싱 실패: $resultJson" -ForegroundColor Yellow
        }
    }
}

if ($Register) {
    Register-DeepSleepTask
    Show-DeepSleepTaskStatus
} elseif ($Unregister) {
    Unregister-DeepSleepTask
} elseif ($Status) {
    Show-DeepSleepTaskStatus
} else {
    Show-DeepSleepTaskStatus
    Write-Host ""
    Write-Host "사용법:" -ForegroundColor White
    Write-Host "  등록:   .\\scripts\\register_deep_sleep_task.ps1 -Register" -ForegroundColor Gray
    Write-Host "  제거:   .\\scripts\\register_deep_sleep_task.ps1 -Unregister" -ForegroundColor Gray
    Write-Host "  상태:   .\\scripts\\register_deep_sleep_task.ps1 -Status" -ForegroundColor Gray
    Write-Host "  시간변경: .\\scripts\\register_deep_sleep_task.ps1 -Register -Time '04:00'" -ForegroundColor Gray
}

