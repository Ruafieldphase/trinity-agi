<#
.SYNOPSIS
    VS Code에서 터미널 방해 없이 작업하는 설정

.DESCRIPTION
    현재 실행 중인 PowerShell Job을 정리하고
    백그라운드 실행으로 전환

.EXAMPLE
    .\cleanup_terminal_jobs.ps1
#>

[CmdletBinding()]
param()
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'

Write-Host "`n╔═══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  터미널 정리 및 백그라운드 전환          ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════╝`n" -ForegroundColor Cyan

# 1. 현재 실행 중인 Job 확인
Write-Host "📊 현재 실행 중인 Jobs:" -ForegroundColor Cyan
$jobs = Get-Job | Where-Object { $_.Name -like 'AGI_*' }

if ($jobs.Count -eq 0) {
    Write-Host "   ✅ 실행 중인 Job 없음" -ForegroundColor Green
}
else {
    Write-Host "   발견: $($jobs.Count)개`n" -ForegroundColor Yellow
    
    foreach ($job in $jobs) {
        Write-Host "   🔹 $($job.Name)" -ForegroundColor White
        Write-Host "      상태: $($job.State)" -ForegroundColor Gray
        Write-Host "      시작: $($job.PSBeginTime)" -ForegroundColor Gray
    }
    
    # 2. 상태 저장
    Write-Host "`n💾 현재 상태 저장 중..." -ForegroundColor Cyan
    $statusFile = Join-Path $WorkspaceRoot "outputs\job_state_before_cleanup.json"
    
    $state = @{
        timestamp = (Get-Date).ToString("o")
        jobs      = $jobs | ForEach-Object {
            @{
                name      = $_.Name
                state     = $_.State
                startTime = $_.PSBeginTime
                id        = $_.Id
            }
        }
    }
    
    $state | ConvertTo-Json -Depth 3 | Out-File -FilePath $statusFile -Encoding UTF8
    Write-Host "   ✅ 저장 완료: job_state_before_cleanup.json" -ForegroundColor Green
    
    # 3. Job 정리
    Write-Host "`n🧹 Job 정리 중..." -ForegroundColor Cyan
    
    $runningJobs = $jobs | Where-Object { $_.State -eq 'Running' }
    $completedJobs = $jobs | Where-Object { $_.State -eq 'Completed' -or $_.State -eq 'Failed' }
    
    if ($runningJobs.Count -gt 0) {
        Write-Host "   중지: $($runningJobs.Count)개" -ForegroundColor Yellow
        $runningJobs | Stop-Job
        Start-Sleep -Seconds 1
    }
    
    Write-Host "   제거: $($jobs.Count)개" -ForegroundColor Yellow
    $jobs | Remove-Job -Force
    
    Write-Host "   ✅ 정리 완료" -ForegroundColor Green
}

# 4. 백그라운드 전환 제안
Write-Host "`n🚀 백그라운드 실행 옵션:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   [권장] Task Scheduler로 전환:" -ForegroundColor Green
Write-Host "   .\scripts\start_24h_silent.ps1" -ForegroundColor White
Write-Host ""
Write-Host "   또는 숨김 창으로 실행:" -ForegroundColor Yellow
Write-Host "   .\scripts\start_24h_silent.ps1 -Method hidden" -ForegroundColor White
Write-Host ""

# 5. VS Code 설정 제안
Write-Host "💡 VS Code 터미널 설정 개선:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   1. Ctrl+, (설정 열기)" -ForegroundColor Gray
Write-Host "   2. 검색: 'terminal.integrated.automationProfile.windows'" -ForegroundColor Gray
Write-Host "   3. 또는 settings.json에 추가:" -ForegroundColor Gray
Write-Host '      "terminal.integrated.hideOnStartup": "whenEmpty"' -ForegroundColor DarkGray
Write-Host '      "terminal.integrated.defaultProfile.windows": "PowerShell"' -ForegroundColor DarkGray
Write-Host ""

# 6. 현재 터미널 상태
Write-Host "📊 현재 터미널 상태:" -ForegroundColor Cyan
$currentJobs = Get-Job
if ($currentJobs.Count -eq 0) {
    Write-Host "   ✅ 깨끗함 (실행 중인 Job 없음)" -ForegroundColor Green
}
else {
    Write-Host "   ⚠️  $($currentJobs.Count)개 Job 남아있음" -ForegroundColor Yellow
}

Write-Host "`n✅ 정리 완료!" -ForegroundColor Green
Write-Host "   이제 터미널 방해 없이 작업할 수 있습니다." -ForegroundColor White
Write-Host ""