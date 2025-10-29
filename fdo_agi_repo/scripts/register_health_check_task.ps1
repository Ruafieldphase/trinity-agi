param(
    [Parameter(Mandatory = $false)]
    [ValidateSet('Hourly', 'Daily', 'Weekly')]
    [string]$Frequency = 'Daily',
    
    [Parameter(Mandatory = $false)]
    [string]$TaskName = 'AGI_HealthCheck_Alert',
    
    [switch]$WithReport,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

# 스크립트 경로
$RepoRoot = "D:\nas_backup\fdo_agi_repo"
$AlertScript = Join-Path $RepoRoot "scripts\alert_system.ps1"

if (-not (Test-Path $AlertScript)) {
    Write-Error "Alert script not found: $AlertScript"
    exit 1
}

# 기존 작업 확인
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask -and -not $Force) {
    Write-Host "작업 '$TaskName'이 이미 존재합니다." -ForegroundColor Yellow
    Write-Host "강제 재생성하려면 -Force 플래그를 사용하세요." -ForegroundColor Yellow
    exit 0
}

if ($ExistingTask -and $Force) {
    Write-Host "기존 작업 삭제 중..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# 트리거 설정
$Trigger = switch ($Frequency) {
    'Hourly' {
        $TriggerObj = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration ([TimeSpan]::MaxValue)
        Write-Host "트리거: 매 1시간마다" -ForegroundColor Cyan
        $TriggerObj
    }
    'Daily' {
        $TriggerObj = New-ScheduledTaskTrigger -Daily -At "09:00"
        Write-Host "트리거: 매일 오전 9시" -ForegroundColor Cyan
        $TriggerObj
    }
    'Weekly' {
        $TriggerObj = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "09:00"
        Write-Host "트리거: 매주 월요일 오전 9시" -ForegroundColor Cyan
        $TriggerObj
    }
}

# 액션 설정
$ActionCommand = "powershell.exe"
$ActionArguments = "-NoProfile -ExecutionPolicy Bypass -File `"$AlertScript`""

if ($WithReport) {
    # 리포트 생성도 함께 실행
    $DashboardScript = Join-Path $RepoRoot "scripts\ops_dashboard.ps1"
    $ReportOutputDir = Join-Path $RepoRoot "outputs\scheduled_reports"
    
    if (-not (Test-Path $ReportOutputDir)) {
        New-Item -ItemType Directory -Path $ReportOutputDir -Force | Out-Null
    }
    
    $ReportFile = Join-Path $ReportOutputDir "report_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    
    $ActionArguments = "-NoProfile -ExecutionPolicy Bypass -Command `"" +
    "& '$DashboardScript' -Json | Out-File -FilePath '$ReportFile' -Encoding UTF8; " +
    "& '$AlertScript'`""
    
    Write-Host "리포트 자동 생성: $ReportOutputDir" -ForegroundColor Cyan
}

$Action = New-ScheduledTaskAction -Execute $ActionCommand -Argument $ActionArguments

# 설정
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# 주체 (현재 사용자 권한으로 실행)
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive

# 작업 등록
$Task = Register-ScheduledTask `
    -TaskName $TaskName `
    -Trigger $Trigger `
    -Action $Action `
    -Settings $Settings `
    -Principal $Principal `
    -Description "AGI 헬스 체크 및 알림 자동 실행 ($Frequency)"

Write-Host "✅ 예약 작업 등록 완료!" -ForegroundColor Green
Write-Host ""
Write-Host "작업 이름: $TaskName" -ForegroundColor Cyan
Write-Host "빈도: $Frequency" -ForegroundColor Cyan
Write-Host "실행 스크립트: $AlertScript" -ForegroundColor Cyan
Write-Host ""
Write-Host "작업 관리:" -ForegroundColor Yellow
Write-Host "  • 상태 확인: Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "  • 즉시 실행: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "  • 비활성화: Disable-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "  • 삭제: Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor Gray
