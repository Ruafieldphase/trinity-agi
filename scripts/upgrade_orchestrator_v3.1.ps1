# 오케스트레이터를 v3.1로 업그레이드 (Self-Healing 내장)

$TaskName = 'AGI_Integrated_Rhythm_Orchestrator'
$ScriptPathNew = 'C:\workspace\agi\scripts\integrated_rhythm_system_v3.1.ps1'

Write-Host "`n" -NoNewline
Write-Host ("=" * 90) -ForegroundColor Magenta
Write-Host "  🎵 ORCHESTRATOR v3.1 업그레이드 (Self-Healing 내장)" -ForegroundColor Yellow
Write-Host ("=" * 90) -ForegroundColor Magenta
Write-Host ""

# 기존 작업 제거
Write-Host "기존 오케스트레이터 작업을 업그레이드 중..." -ForegroundColor Yellow
try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
    Start-Sleep -Seconds 1
} catch {
    # 무시
}

# 새 작업 액션 생성
$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File '$ScriptPathNew'"

# 트리거 생성 (5분마다)
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration (New-TimeSpan -Days 999)

# 설정 생성
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false `
    -MultipleInstances IgnoreNew

# 새 작업 등록
Register-ScheduledTask -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "AGI Integrated Rhythm System v3.1 - Phase 1,2,3 + Self-Healing Level 1" `
    -Force | Out-Null

Write-Host "✅ 오케스트레이터 v3.1로 업그레이드 완료!" -ForegroundColor Green

# 즉시 시작
Start-ScheduledTask -TaskName $TaskName
Write-Host "✅ 업그레이드된 오케스트레이터 시작됨" -ForegroundColor Green

# 상태 확인
Start-Sleep -Seconds 2
$task = Get-ScheduledTask -TaskName $TaskName

Write-Host "`n" -NoNewline
Write-Host ("=" * 90) -ForegroundColor Magenta
Write-Host "  📊 업그레이드 완료" -ForegroundColor Green
Write-Host ("=" * 90) -ForegroundColor Magenta
Write-Host ""

Write-Host "작업명:      $TaskName" -ForegroundColor Cyan
Write-Host "스크립트:    v3.1 (Self-Healing 내장)" -ForegroundColor Cyan
Write-Host "상태:        $($task.State)" -ForegroundColor Green
Write-Host ""

Write-Host "🎵 이제 완전한 지능형 자동화 시스템이 배포되었습니다:" -ForegroundColor Magenta
Write-Host ""
Write-Host "   🔴 Phase 1: 마스터 스케줄러     (정적 리듬 - 메트로놈)" -ForegroundColor Red
Write-Host "   🔵 Phase 2: 적응형 스케줄러     (동적 리듬 - 호흡)" -ForegroundColor Cyan
Write-Host "   🟡 Phase 3: 이벤트 감지기       (지능형 리듬 - 감지)" -ForegroundColor Yellow
Write-Host "   🟢 Health: 자가 치유 Level 1   (자동 복구 - 생명)" -ForegroundColor Green
Write-Host ""

Write-Host "🔄 운영 흐름:" -ForegroundColor Magenta
Write-Host "   1. 감지 (Detection):     이벤트 감지기가 이상 패턴 감지" -ForegroundColor Gray
Write-Host "   2. 진단 (Diagnosis):     건강도 점수로 문제 분류" -ForegroundColor Gray
Write-Host "   3. 치유 (Healing):       자동 복구 액션 실행" -ForegroundColor Gray
Write-Host "   4. 모니터링 (Monitor):   결과 기록 및 지속 추적" -ForegroundColor Gray
Write-Host ""
