#Requires -Version 5.1
<#
.SYNOPSIS
    백그라운드 작업 모니터링 - PowerShell 창 팝업 감지
.DESCRIPTION
    5-10분간 백그라운드 작업을 모니터링하여
    PowerShell 창이 뜨는지, Hidden 설정이 제대로 작동하는지 확인합니다.
#>

param(
    [int]$DurationMinutes = 10,
    [int]$CheckIntervalSeconds = 30,
    [string]$OutFile = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\background_task_monitor_latest.json"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Continue"
$startTime = Get-Date
$endTime = $startTime.AddMinutes($DurationMinutes)
$events = @()

Write-Host "🔍 백그라운드 작업 모니터링 시작" -ForegroundColor Cyan
Write-Host "   시작: $($startTime.ToString('HH:mm:ss'))" -ForegroundColor Gray
Write-Host "   종료: $($endTime.ToString('HH:mm:ss'))" -ForegroundColor Gray
Write-Host "   체크 간격: ${CheckIntervalSeconds}초`n" -ForegroundColor Gray

$checkCount = 0
while ((Get-Date) -lt $endTime) {
    $checkCount++
    $now = Get-Date
    
    Write-Host "[$checkCount] $($now.ToString('HH:mm:ss')) - " -NoNewline -ForegroundColor Cyan
    
    # 1. PowerShell 프로세스 중 workspace\agi 관련된 것 찾기
    $agiProcesses = Get-Process -Name 'powershell', 'pwsh' -ErrorAction SilentlyContinue | Where-Object {
        $_.MainWindowTitle -ne '' -or # 창이 보이는 경우
        ($_.CommandLine -and $_.CommandLine -like '*workspace*agi*')
    }
    
    # 2. 창이 보이는 AGI 프로세스 (문제!)
    $visibleProcesses = $agiProcesses | Where-Object { $_.MainWindowTitle -ne '' }
    
    if ($visibleProcesses) {
        Write-Host "⚠️  창이 보임! ($($visibleProcesses.Count)개)" -ForegroundColor Yellow
        foreach ($proc in $visibleProcesses) {
            $event = @{
                timestamp    = $now.ToString('yyyy-MM-dd HH:mm:ss')
                type         = "visible_window"
                process_id   = $proc.Id
                process_name = $proc.ProcessName
                window_title = $proc.MainWindowTitle
                command_line = if ($proc.CommandLine) { $proc.CommandLine.Substring(0, [Math]::Min(200, $proc.CommandLine.Length)) } else { "N/A" }
            }
            $events += $event
            Write-Host "      PID $($proc.Id): $($proc.MainWindowTitle)" -ForegroundColor Red
        }
    }
    else {
        Write-Host "✓ 모든 작업 숨김 상태" -ForegroundColor Green
        
        # 백그라운드로 실행 중인 AGI 프로세스 수 기록
        $hiddenCount = $agiProcesses.Count
        $event = @{
            timestamp            = $now.ToString('yyyy-MM-dd HH:mm:ss')
            type                 = "all_hidden"
            hidden_process_count = $hiddenCount
        }
        $events += $event
        
        if ($hiddenCount -gt 0) {
            Write-Host "      ($hiddenCount개 백그라운드 실행 중)" -ForegroundColor Gray
        }
    }
    
    # 3. 작업 스케줄러에서 현재 Running 상태인 AGI 작업
    $runningTasks = Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object {
        $_.TaskName -like 'AGI*' -and $_.State -eq 'Running'
    }
    
    if ($runningTasks) {
        Write-Host "      실행 중인 작업: $($runningTasks.TaskName -join ', ')" -ForegroundColor Cyan
    }
    
    # 다음 체크까지 대기
    Start-Sleep -Seconds $CheckIntervalSeconds
}

# 최종 리포트
$totalChecks = $events.Count
$visibleEvents = $events | Where-Object { $_.type -eq 'visible_window' }
$hiddenEvents = $events | Where-Object { $_.type -eq 'all_hidden' }

Write-Host "`n=== 모니터링 완료 ===" -ForegroundColor Cyan
Write-Host "총 체크 횟수: $totalChecks" -ForegroundColor Gray
Write-Host "창 보임 이벤트: $($visibleEvents.Count) 회" -ForegroundColor $(if ($visibleEvents.Count -gt 0) { 'Red' } else { 'Green' })
Write-Host "정상 숨김: $($hiddenEvents.Count) 회" -ForegroundColor Green

if ($visibleEvents.Count -eq 0) {
    Write-Host "`n✅ 성공! 모든 백그라운드 작업이 숨김 상태로 실행됨" -ForegroundColor Green
}
else {
    Write-Host "`n⚠️  일부 작업이 창을 표시했습니다. 로그를 확인하세요." -ForegroundColor Yellow
}

# JSON 저장
$report = @{
    monitoring_period = @{
        start            = $startTime.ToString('yyyy-MM-dd HH:mm:ss')
        end              = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
        duration_minutes = $DurationMinutes
    }
    summary           = @{
        total_checks          = $totalChecks
        visible_window_events = $visibleEvents.Count
        hidden_ok_events      = $hiddenEvents.Count
        success               = ($visibleEvents.Count -eq 0)
    }
    events            = $events
}

$outDir = Split-Path -Parent $OutFile
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

$report | ConvertTo-Json -Depth 10 | Set-Content -Path $OutFile -Encoding UTF8
Write-Host "`n📊 리포트 저장: $OutFile" -ForegroundColor Cyan

exit 0