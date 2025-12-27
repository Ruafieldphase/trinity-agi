# Register Rhythm Guardian as Windows Startup Task
# 부팅 시 자동으로 Guardian 시작

$ErrorActionPreference = "SilentlyContinue"

$TaskName = "RhythmGuardian"
$ProjectRoot = "C:\workspace\agi"
$Python = "$ProjectRoot\.venv\Scripts\pythonw.exe"  # pythonw = no console window
$Script = "$ProjectRoot\scripts\rhythm_guardian.py"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Rhythm Guardian Startup Registration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Python 확인
if (-not (Test-Path $Python)) {
    $Python = "pythonw"
    Write-Host "[WARN] Using system pythonw" -ForegroundColor Yellow
}

# 기존 작업 제거
$existing = schtasks /Query /TN $TaskName 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[INFO] Removing existing task..." -ForegroundColor Yellow
    schtasks /Delete /TN $TaskName /F | Out-Null
}

# 새 작업 등록 (로그온 시 실행)
Write-Host "[INFO] Registering startup task..." -ForegroundColor Cyan

$Action = New-ScheduledTaskAction -Execute $Python -Argument "`"$Script`" --interval 30" -WorkingDirectory $ProjectRoot
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force | Out-Null

if ($?) {
    Write-Host ""
    Write-Host "[OK] Guardian registered for startup!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Task Name: $TaskName" -ForegroundColor White
    Write-Host "  Trigger:   At logon" -ForegroundColor White
    Write-Host "  Interval:  30 seconds" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "[ERROR] Registration failed" -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
