# AGI 시스템 조용히 중지
# 모든 AGI 관련 Python 프로세스를 종료합니다

$ErrorActionPreference = "SilentlyContinue"

Write-Host "🛑 AGI 시스템을 중지합니다..." -ForegroundColor Red

# AGI 관련 Python 프로세스 찾기
$agiProcesses = Get-Process python* -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*workspace*agi*" -or
    $_.CommandLine -like "*rhythm_guardian*" -or
    $_.CommandLine -like "*heartbeat*" -or
    $_.CommandLine -like "*aura_controller*" -or
    $_.CommandLine -like "*background_self*" -or
    $_.CommandLine -like "*autonomous_goal*"
}

if ($agiProcesses) {
    $count = ($agiProcesses | Measure-Object).Count
    Write-Host "   발견된 프로세스: $count 개" -ForegroundColor Yellow

    foreach ($proc in $agiProcesses) {
        try {
            Write-Host "   종료 중: PID $($proc.Id)" -ForegroundColor Gray
            Stop-Process -Id $proc.Id -Force
        } catch {
            Write-Host "   ⚠️  PID $($proc.Id) 종료 실패" -ForegroundColor DarkYellow
        }
    }

    Start-Sleep -Seconds 2
    Write-Host "✅ AGI 시스템 중지 완료" -ForegroundColor Green
} else {
    Write-Host "   실행 중인 AGI 프로세스가 없습니다." -ForegroundColor Gray
}

# Guardian PID 파일 삭제
$pidFile = "C:\workspace\agi\logs\rhythm_guardian.pid"
if (Test-Path $pidFile) {
    Remove-Item $pidFile -Force
    Write-Host "   Guardian PID 파일 삭제됨" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🔇 모든 프로세스가 조용히 종료되었습니다." -ForegroundColor Cyan
