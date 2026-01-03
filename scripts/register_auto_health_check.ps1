# 자동 시스템 건강 체크 스케줄러 등록
# 매 시간마다 실행하여 시스템을 자동으로 관리합니다.


. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot
$TaskName = "AGI_Auto_Health_Check"
$Description = "자동 시스템 건강 체크 및 복구 - 매 시간마다 실행"
$Python = "python"
$Script = "$WorkspaceRoot\scripts\auto_system_health_check.py"

# 기존 작업 제거
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

# 트리거: 매 시간마다 (1년간)
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 365)

# 액션: Python 스크립트 실행
$Action = New-ScheduledTaskAction -Execute $Python -Argument $Script -WorkingDirectory $WorkspaceRoot

# 설정: 숨김 모드, 백그라운드 실행
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -Hidden

# 현재 사용자로 실행
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Highest

# 작업 등록
Register-ScheduledTask -TaskName $TaskName -Trigger $Trigger -Action $Action -Settings $Settings -Principal $Principal -Description $Description -Force

Write-Host "✅ $TaskName 등록 완료" -ForegroundColor Green
Write-Host "   - 실행 간격: 매 1시간" -ForegroundColor Cyan
Write-Host "   - 다음 실행: $(Get-Date -Format 'yyyy-MM-dd HH:00:00')" -ForegroundColor Cyan

# 즉시 실행 테스트
Write-Host "`n🚀 테스트 실행 중..." -ForegroundColor Yellow
Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 3
$Task = Get-ScheduledTask -TaskName $TaskName
Write-Host "   상태: $($Task.State)" -ForegroundColor Green