#Requires -RunAsAdministrator

# 관리자 권한으로 모든 AGI 프로세스 강제 종료

Write-Host "`n🚨 긴급 전체 프로세스 강제 종료 (관리자 권한)" -ForegroundColor Red
Write-Host "=" * 80

# 1. cmd.exe 프로세스 중지
Write-Host "`n[1/3] cmd.exe 프로세스 중지..." -ForegroundColor Yellow
$cmdProcesses = Get-Process cmd -ErrorAction SilentlyContinue
if ($cmdProcesses) {
    foreach ($proc in $cmdProcesses) {
        try {
            Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            Write-Host "  ✅ cmd.exe PID $($proc.Id) 중지" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ cmd.exe PID $($proc.Id) 실패" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  ℹ️  cmd.exe 프로세스 없음" -ForegroundColor Gray
}

# 2. python.exe 프로세스 중지
Write-Host "`n[2/3] python.exe 프로세스 중지..." -ForegroundColor Yellow
$pythonProcesses = Get-Process python* -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    foreach ($proc in $pythonProcesses) {
        try {
            Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            Write-Host "  ✅ python.exe PID $($proc.Id) 중지" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ python.exe PID $($proc.Id) 실패" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  ℹ️  python.exe 프로세스 없음" -ForegroundColor Gray
}

# 3. PowerShell 프로세스 중지 (현재 제외)
Write-Host "`n[3/3] PowerShell 프로세스 중지..." -ForegroundColor Yellow
$psProcesses = Get-Process powershell* -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne $PID }
if ($psProcesses) {
    foreach ($proc in $psProcesses) {
        try {
            Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            Write-Host "  ✅ powershell.exe PID $($proc.Id) 중지" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ powershell.exe PID $($proc.Id) 실패" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  ℹ️  PowerShell 프로세스 없음" -ForegroundColor Gray
}

# 검증
Write-Host "`n" + "=" * 80
Write-Host "🔍 검증 중..." -ForegroundColor Cyan
Start-Sleep -Seconds 2

$remainingCmd = (Get-Process cmd -ErrorAction SilentlyContinue).Count
$remainingPython = (Get-Process python* -ErrorAction SilentlyContinue).Count
$remainingPS = (Get-Process powershell* -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne $PID }).Count

Write-Host "`n남은 프로세스:" -ForegroundColor Yellow
Write-Host "  cmd.exe: $remainingCmd" -ForegroundColor White
Write-Host "  python.exe: $remainingPython" -ForegroundColor White
Write-Host "  powershell.exe: $remainingPS" -ForegroundColor White

if ($remainingCmd -eq 0 -and $remainingPython -eq 0 -and $remainingPS -eq 0) {
    Write-Host "`n✅ 모든 프로세스가 중지되었습니다!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  일부 프로세스가 남아있습니다. 재부팅을 권장합니다." -ForegroundColor Yellow
}

Write-Host "`n" + "=" * 80
Write-Host ""
