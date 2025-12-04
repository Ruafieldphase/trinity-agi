# Nightly Consolidation - Scheduled Task Registration
# Hippocampus consolidation을 매일 자동 실행하도록 등록

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [string]$Time = "03:00"  # 기본: 새벽 3시
)

$TaskName = "AGI_Nightly_Consolidation"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$ScriptPath = Join-Path $WorkspaceRoot "scripts\nightly_consolidation.py"
$PythonExe = Join-Path $WorkspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"

# Python 실행 파일 확인
if (!(Test-Path -LiteralPath $PythonExe)) {
    $PythonExe = "python"
}

function Register-ConsolidationTask {
    Write-Host "🌙 Nightly Consolidation Task 등록 중..." -ForegroundColor Cyan
    
    # 기존 Task 제거
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "   기존 Task 제거 중..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # Task Action
    $action = New-ScheduledTaskAction `
        -Execute $PythonExe `
        -Argument "`"$ScriptPath`"" `
        -WorkingDirectory $WorkspaceRoot
    
    # Task Trigger (매일 지정된 시간)
    $trigger = New-ScheduledTaskTrigger -Daily -At $Time
    
    # Task Settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false
    
    # Task Principal (현재 사용자)
    $principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -LogonType Interactive `
        -RunLevel Highest
    
    # Task 등록
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "AGI Hippocampus Nightly Consolidation - 단기 기억을 장기 기억으로 변환" | Out-Null
    
    Write-Host "✅ Nightly Consolidation Task 등록 완료!" -ForegroundColor Green
    Write-Host "   Task 이름: $TaskName" -ForegroundColor White
    Write-Host "   실행 시간: 매일 $Time" -ForegroundColor White
    Write-Host "   스크립트: $ScriptPath" -ForegroundColor Gray
}

function Unregister-ConsolidationTask {
    Write-Host "🗑️  Nightly Consolidation Task 제거 중..." -ForegroundColor Yellow
    
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✅ Task 제거 완료" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  등록된 Task가 없습니다." -ForegroundColor Yellow
    }
}

function Show-TaskStatus {
    Write-Host "📊 Nightly Consolidation Task 상태" -ForegroundColor Cyan
    Write-Host ""
    
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    
    if ($task) {
        Write-Host "✅ Task 등록됨" -ForegroundColor Green
        Write-Host "   상태: $($task.State)" -ForegroundColor White
        Write-Host "   마지막 실행: $($task.LastRunTime)" -ForegroundColor Gray
        Write-Host "   다음 실행: $($task.NextRunTime)" -ForegroundColor Cyan
        
        # 최근 결과 확인
        $resultFile = Join-Path $WorkspaceRoot "outputs\consolidation_result_latest.json"
        if (Test-Path -LiteralPath $resultFile) {
            $result = Get-Content $resultFile -Raw | ConvertFrom-Json
            Write-Host ""
            Write-Host "📁 최근 실행 결과:" -ForegroundColor White
            Write-Host "   Timestamp: $($result.timestamp)" -ForegroundColor Gray
            Write-Host "   Total: $($result.consolidation_result.total)" -ForegroundColor Yellow
            Write-Host "   Episodic: $($result.consolidation_result.episodic)" -ForegroundColor Magenta
            Write-Host "   Semantic: $($result.consolidation_result.semantic)" -ForegroundColor Cyan
            Write-Host "   Procedural: $($result.consolidation_result.procedural)" -ForegroundColor Blue
        }
    }
    else {
        Write-Host "❌ Task가 등록되지 않았습니다." -ForegroundColor Red
        Write-Host "   등록 명령: .\register_nightly_consolidation.ps1 -Register" -ForegroundColor Yellow
    }
}

# Main
if ($Register) {
    Register-ConsolidationTask
    Write-Host ""
    Show-TaskStatus
}
elseif ($Unregister) {
    Unregister-ConsolidationTask
}
elseif ($Status) {
    Show-TaskStatus
}
else {
    # 기본: 상태 확인
    Show-TaskStatus
    Write-Host ""
    Write-Host "사용법:" -ForegroundColor White
    Write-Host "  등록:   .\register_nightly_consolidation.ps1 -Register" -ForegroundColor Gray
    Write-Host "  제거:   .\register_nightly_consolidation.ps1 -Unregister" -ForegroundColor Gray
    Write-Host "  상태:   .\register_nightly_consolidation.ps1 -Status" -ForegroundColor Gray
    Write-Host "  시간변경: .\register_nightly_consolidation.ps1 -Register -Time '04:00'" -ForegroundColor Gray
}
