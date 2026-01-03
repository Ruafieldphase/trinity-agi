# AGI 시스템 자동 시작 복원 스크립트
# ===============================================
# 백업된 자동 시작 설정을 복원합니다.

param(
    [Parameter(Mandatory=$false)]
    [string]$BackupFile,
    [switch]$Force
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



Write-Host "`n🔄 AGI 시스템 자동 시작 복원" -ForegroundColor Cyan
Write-Host "=" * 80

# 백업 파일 찾기
if (-not $BackupFile) {
    $backupDir = "$WorkspaceRoot\outputs\sena\backups"

    if (Test-Path $backupDir) {
        $backups = Get-ChildItem -Path $backupDir -Filter "autostart_backup_*.json" | Sort-Object LastWriteTime -Descending

        if ($backups.Count -eq 0) {
            Write-Host "`n❌ 백업 파일을 찾을 수 없습니다." -ForegroundColor Red
            Write-Host "   위치: $backupDir" -ForegroundColor Gray
            exit 1
        }

        Write-Host "`n📋 사용 가능한 백업 파일:" -ForegroundColor Yellow
        for ($i = 0; $i -lt [Math]::Min(5, $backups.Count); $i++) {
            $backup = $backups[$i]
            Write-Host "  [$($i+1)] $($backup.Name) - $($backup.LastWriteTime)" -ForegroundColor White
        }

        $selection = Read-Host "`n복원할 백업 번호를 선택하세요 (1-$([Math]::Min(5, $backups.Count)))"
        $selectedIndex = [int]$selection - 1

        if ($selectedIndex -ge 0 -and $selectedIndex -lt $backups.Count) {
            $BackupFile = $backups[$selectedIndex].FullName
        } else {
            Write-Host "`n❌ 잘못된 선택입니다." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "`n❌ 백업 디렉토리가 없습니다: $backupDir" -ForegroundColor Red
        exit 1
    }
}

# 백업 파일 읽기
if (-not (Test-Path $BackupFile)) {
    Write-Host "`n❌ 백업 파일이 없습니다: $BackupFile" -ForegroundColor Red
    exit 1
}

Write-Host "`n📂 백업 파일: $BackupFile" -ForegroundColor Cyan

try {
    $backup = Get-Content -Path $BackupFile -Raw | ConvertFrom-Json
    Write-Host "  ✅ 백업 파일 로드 완료 (생성일: $($backup.timestamp))" -ForegroundColor Green
} catch {
    Write-Host "`n❌ 백업 파일 읽기 실패: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 확인
if (-not $Force) {
    Write-Host "`n⚠️  다음 항목들이 복원됩니다:" -ForegroundColor Yellow

    if ($backup.registry.existed) {
        Write-Host "  • 레지스트리: AGI_Master_Orchestrator" -ForegroundColor White
    }

    foreach ($task in $backup.tasks) {
        if ($task.state -eq "Ready") {
            Write-Host "  • Task: $($task.name) (활성화)" -ForegroundColor White
        }
    }

    Write-Host ""
    $confirm = Read-Host "계속하시겠습니까? (Y/N)"
    if ($confirm -ne 'Y' -and $confirm -ne 'y') {
        Write-Host "`n취소되었습니다." -ForegroundColor Gray
        exit 0
    }
}

# 복원 시작
Write-Host "`n🔄 복원 중..." -ForegroundColor Cyan

# 1. 레지스트리 복원
Write-Host "`n[1/2] 레지스트리 복원..." -ForegroundColor Cyan
if ($backup.registry.existed -and $backup.registry.value) {
    try {
        Set-ItemProperty -Path $backup.registry.path `
                        -Name $backup.registry.name `
                        -Value $backup.registry.value `
                        -ErrorAction Stop
        Write-Host "  ✅ 레지스트리 복원 완료" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ 레지스트리 복원 실패: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "  ℹ️  레지스트리 항목이 백업에 없습니다" -ForegroundColor Gray
}

# 2. Task Scheduler 복원
Write-Host "`n[2/2] Task Scheduler 복원..." -ForegroundColor Cyan
foreach ($taskBackup in $backup.tasks) {
    try {
        $task = Get-ScheduledTask -TaskName $taskBackup.name -ErrorAction SilentlyContinue

        if (-not $task) {
            Write-Host "  ⚠️  작업이 존재하지 않습니다: $($taskBackup.name)" -ForegroundColor Yellow
            continue
        }

        if ($taskBackup.state -eq "Ready" -and $task.State -eq "Disabled") {
            Enable-ScheduledTask -TaskName $taskBackup.name -ErrorAction Stop | Out-Null
            Write-Host "  ✅ 활성화 완료: $($taskBackup.name)" -ForegroundColor Green
        } elseif ($taskBackup.state -eq "Disabled" -and $task.State -eq "Ready") {
            Disable-ScheduledTask -TaskName $taskBackup.name -ErrorAction Stop | Out-Null
            Write-Host "  ✅ 비활성화 완료: $($taskBackup.name)" -ForegroundColor Green
        } else {
            Write-Host "  ℹ️  변경 없음: $($taskBackup.name) (현재: $($task.State))" -ForegroundColor Gray
        }
    } catch {
        Write-Host "  ❌ 복원 실패: $($taskBackup.name) - $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 요약
Write-Host "`n" + "=" * 80
Write-Host "✅ 복원 완료!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 복원된 설정:" -ForegroundColor Cyan
Write-Host "   백업 날짜: $($backup.timestamp)" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  주의: 다음 로그인 시 또는 스케줄된 시간에 자동 시작됩니다." -ForegroundColor Yellow
Write-Host ""