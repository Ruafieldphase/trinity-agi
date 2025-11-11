# Lumen 24h Production - 새 터미널 창에서 실행
# 안정적이고 출력도 직접 확인 가능

Write-Host "`n╔═══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Lumen 24h Production 시작                    ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$pythonExe = "C:\workspace\agi\fdo_agi_repo\.venv\Scripts\python.exe"
$scriptPath = "C:\workspace\agi\fdo_agi_repo\scripts\lumen_production_24h_stable.py"

Write-Host "실행 정보:" -ForegroundColor Yellow
Write-Host "   Python: $pythonExe" -ForegroundColor Gray
Write-Host "   Script: $scriptPath" -ForegroundColor Gray
Write-Host "   시작: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor White
Write-Host "   종료 예정: $((Get-Date).AddHours(24).ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor White

Write-Host "`n새 PowerShell 창을 열어 실행합니다..." -ForegroundColor Green
Write-Host "   (창을 닫지 마세요 - 24시간 실행됩니다)`n" -ForegroundColor Yellow

# 새 PowerShell 창에서 실행 (백그라운드가 아닌 별도 창)
$command = "cd C:\workspace\agi\fdo_agi_repo; & '$pythonExe' '$scriptPath'; Read-Host 'Press Enter to close'"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $command

Write-Host "✅ 새 터미널 창에서 실행 시작!" -ForegroundColor Green
Write-Host "`n모니터링 방법:" -ForegroundColor Cyan
Write-Host "   1. 새로 열린 PowerShell 창에서 직접 확인" -ForegroundColor White
Write-Host "   2. 로그 파일: fdo_agi_repo\outputs\lumen_production_24h_stable.jsonl" -ForegroundColor White
Write-Host "   3. 모니터링 스크립트: .\scripts\monitor_lumen_24h_simple.ps1" -ForegroundColor White

Write-Host "`n✨ 완료!`n" -ForegroundColor Green
