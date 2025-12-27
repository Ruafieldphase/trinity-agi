Start-Sleep -Seconds 5
Write-Host "`n프로세스 확인 중..." -ForegroundColor Cyan
$ps = Get-Process powershell* -ErrorAction SilentlyContinue | Where-Object {$_.Id -ne $PID}
if ($ps) {
    Write-Host "⚠️  PowerShell 프로세스 발견:" -ForegroundColor Yellow
    $ps | Format-Table Id, StartTime
} else {
    Write-Host "✅ PowerShell 프로세스 없음 (문제 해결!)" -ForegroundColor Green
}
