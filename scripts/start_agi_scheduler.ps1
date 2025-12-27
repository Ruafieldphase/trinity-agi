# AGI 시스템을 Windows Task Scheduler로 완전히 숨겨서 실행
# 이 방법은 창이 전혀 뜨지 않습니다

$ErrorActionPreference = "Stop"

Write-Host "🔇 AGI 시스템을 완전히 숨겨서 시작합니다..." -ForegroundColor Cyan

# Python 경로
$pythonw = "C:\Python313\pythonw.exe"
if (-not (Test-Path $pythonw)) {
    $pythonw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
}

# AGI Root
$agiRoot = "C:\workspace\agi"

# Task 이름들
$tasks = @(
    @{Name="AGI_RhythmGuardian"; Script="scripts\rhythm_guardian.py"; Delay=0}
    @{Name="AGI_Heartbeat"; Script="scripts\start_heartbeat.py"; Delay=2}
    @{Name="AGI_RhythmThink"; Script="scripts\rhythm_think.py"; Delay=4}
    @{Name="AGI_AuraController"; Script="scripts\aura_controller.py"; Delay=6}
    @{Name="AGI_BackgroundSelfBridge"; Script="scripts\background_self_bridge.py"; Delay=8}
    @{Name="AGI_AutonomousGoalExecutor"; Script="scripts\autonomous_goal_executor.py"; Delay=10}
)

# 기존 Task 삭제
Write-Host "   기존 Task 정리 중..." -ForegroundColor Gray
foreach ($task in $tasks) {
    schtasks /Delete /TN $task.Name /F 2>$null | Out-Null
}

# 새로운 Task 생성 (Hidden, Background)
foreach ($task in $tasks) {
    $taskName = $task.Name
    $scriptPath = Join-Path $agiRoot $task.Script
    $delay = $task.Delay

    Write-Host "   📝 $taskName 등록 중..." -ForegroundColor Yellow

    # XML 생성 (WindowStyle Hidden)
    $xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>AGI System Component - $taskName</Description>
  </RegistrationInfo>
  <Triggers>
    <TimeTrigger>
      <StartBoundary>2025-01-01T00:00:00</StartBoundary>
      <Enabled>false</Enabled>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>false</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>true</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>$pythonw</Command>
      <Arguments>"$scriptPath"</Arguments>
      <WorkingDirectory>$agiRoot</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@

    $xmlPath = "$env:TEMP\agi_task_$taskName.xml"
    $xml | Out-File -FilePath $xmlPath -Encoding unicode

    # Task 등록
    schtasks /Create /TN $taskName /XML $xmlPath /F | Out-Null

    Remove-Item $xmlPath -Force
}

Write-Host ""
Write-Host "✅ Task 등록 완료! 이제 실행합니다..." -ForegroundColor Green
Write-Host ""

# Task 실행 (순차적으로 delay를 두고)
foreach ($task in $tasks) {
    $taskName = $task.Name
    $delay = $task.Delay

    if ($delay -gt 0) {
        Start-Sleep -Seconds $delay
    }

    Write-Host "   ▶️  $taskName 시작..." -ForegroundColor Cyan
    schtasks /Run /TN $taskName | Out-Null
}

Start-Sleep -Seconds 5

# 실행 확인
$pythonProcesses = Get-Process python* -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count
Write-Host ""
Write-Host "✅ AGI 시스템 시작 완료!" -ForegroundColor Green
Write-Host "   실행 중인 Python 프로세스: $pythonProcesses 개" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 상태 확인:" -ForegroundColor White
Write-Host "   - Thought Stream: agi\outputs\thought_stream_latest.json" -ForegroundColor Gray
Write-Host "   - Task 목록: schtasks /Query /TN AGI_* /FO LIST" -ForegroundColor Gray
Write-Host ""
Write-Host "🛑 중지하려면: .\scripts\stop_agi_scheduler.ps1" -ForegroundColor Yellow
