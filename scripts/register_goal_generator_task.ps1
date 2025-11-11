[CmdletBinding()]
param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [string]$Time = "03:00"
)

$ErrorActionPreference = 'Stop'
$TaskName = "AGI_AutonomousGoalGenerator"
$WorkspaceRoot = "C:\workspace\agi"
$PythonPath = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
$ScriptPath = "$WorkspaceRoot\scripts\autonomous_goal_generator.py"
$LogDir = "$WorkspaceRoot\outputs\logs\goal_generator"
$BatchFile = "$WorkspaceRoot\scripts\run_goal_generator.bat"

# 로그 디렉토리 생성
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# 배치 파일 생성 (Goal Generator 실행용)
$batchContent = @"
@echo off
setlocal
cd /d "$WorkspaceRoot"
set PYTHONIOENCODING=utf-8
echo [%date% %time%] Starting autonomous goal generator...
"$PythonPath" "$ScriptPath" --hours 24 2>&1
echo [%date% %time%] Goal generator completed with exit code: %ERRORLEVEL%
exit /b %ERRORLEVEL%
"@

if ($Register -or $Unregister) {
    Set-Content -Path $BatchFile -Value $batchContent -Encoding ASCII
    Write-Host "✅ Created batch file: $BatchFile" -ForegroundColor Green
}

# 상태 확인
if (-not $Register -and -not $Unregister) {
    Write-Host "=== Autonomous Goal Generator Task Status ===" -ForegroundColor Cyan
    
    $task = schtasks /query /tn $TaskName /fo csv /v 2>$null | ConvertFrom-Csv
    
    if ($LASTEXITCODE -eq 0 -and $task) {
        Write-Host "✅ Task registered: $TaskName" -ForegroundColor Green
        Write-Host "   Next Run: $($task.'Next Run Time')" -ForegroundColor White
        Write-Host "   Status: $($task.Status)" -ForegroundColor White
        Write-Host "   Last Run: $($task.'Last Run Time')" -ForegroundColor White
        Write-Host "   Last Result: $($task.'Last Result')" -ForegroundColor White
    }
    else {
        Write-Host "⚠️  Task not registered: $TaskName" -ForegroundColor Yellow
        Write-Host "   Run with -Register to create the task" -ForegroundColor Gray
    }
    exit 0
}

# 등록 해제
if ($Unregister) {
    Write-Host "Unregistering task: $TaskName" -ForegroundColor Yellow
    
    $result = schtasks /delete /tn $TaskName /f 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Task unregistered successfully" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  Task was not registered or failed to unregister" -ForegroundColor Yellow
    }
    exit 0
}

# 등록
if ($Register) {
    Write-Host "Registering autonomous goal generator task..." -ForegroundColor Cyan
    Write-Host "  Task Name: $TaskName" -ForegroundColor Gray
    Write-Host "  Schedule: Daily at $Time" -ForegroundColor Gray
    Write-Host "  Batch File: $BatchFile" -ForegroundColor Gray
    
    # 기존 태스크 삭제 (있다면)
    try {
        $null = schtasks /delete /tn $TaskName /f 2>&1
    }
    catch {
        # Ignore if task doesn't exist
    }
    $LASTEXITCODE = 0  # Reset error code
    
    # 날짜 생성 (내일부터 시작)
    $tomorrow = (Get-Date).AddDays(1).ToString("yyyy-MM-dd")
    
    # 태스크 생성 (schtasks.exe 사용)
    # /RU SYSTEM 제거하고 현재 사용자로 실행
    $createArgs = @(
        "/create"
        "/tn", $TaskName
        "/tr", "`"$BatchFile`" > `"$LogDir\goal_gen_$(Get-Date -Format 'yyyyMMdd').log`" 2>&1"
        "/sc", "daily"
        "/st", $Time
        "/sd", $tomorrow
        "/f"
    )
    
    Write-Host "Creating task with schtasks..." -ForegroundColor Gray
    $output = & schtasks $createArgs 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Task registered successfully!" -ForegroundColor Green
        Write-Host "   Task Name: $TaskName" -ForegroundColor White
        Write-Host "   Daily Schedule: $Time" -ForegroundColor White
        Write-Host "   Next Run: $tomorrow $Time" -ForegroundColor White
        Write-Host "   Batch: $BatchFile" -ForegroundColor White
        Write-Host "   Logs: $LogDir" -ForegroundColor White
        Write-Host "`n💡 Run with -Status to check task status" -ForegroundColor Cyan
        Write-Host "💡 Run manually: schtasks /run /tn $TaskName" -ForegroundColor Cyan
    }
    else {
        Write-Host "`n❌ Failed to register task" -ForegroundColor Red
        Write-Host "Output: $output" -ForegroundColor Gray
        Write-Host "`n💡 May need administrator privileges" -ForegroundColor Yellow
        exit 1
    }
}
