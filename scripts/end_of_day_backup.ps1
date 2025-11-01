#Requires -Version 5.1
<#
.SYNOPSIS
    일과 종료 백업 - "오늘 여기까지" 명령 시 실행
.DESCRIPTION
    1. 세션 저장 (대화 내용 + 변경사항)
    2. Git 커밋
    3. 시스템 상태 백업
    4. 설정 파일 백업
    5. 최근 출력물 백업
    6. 백업 아카이브 생성
.EXAMPLE
    .\end_of_day_backup.ps1
    .\end_of_day_backup.ps1 -Note "Phase 6 완료"
#>

param(
    [string]$Note = "",
    [string]$WorkspaceRoot = "$PSScriptRoot\..",
    [switch]$SkipArchive
)

$ErrorActionPreference = "Continue"
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$dateStamp = Get-Date -Format "yyyy-MM-dd"

Write-Host "`n╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   일과 종료 백업 - 오늘 여기까지               ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

Push-Location $WorkspaceRoot

# 1. 세션 저장 먼저 실행
Write-Host "💾 [1/6] 세션 저장 실행 중..." -ForegroundColor Yellow

$saveSessionScript = "$WorkspaceRoot\scripts\save_session_with_changes.ps1"
if (Test-Path $saveSessionScript) {
    & $saveSessionScript -SessionNote $Note
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ 세션 저장 완료" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ 세션 저장 경고 (계속 진행)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠ 세션 저장 스크립트 없음 (스킵)" -ForegroundColor Yellow
}

# 2. 백업 디렉토리 준비
Write-Host "`n📁 [2/6] 백업 디렉토리 준비 중..." -ForegroundColor Yellow

$backupRoot = "$WorkspaceRoot\backups"
$todayBackup = "$backupRoot\$dateStamp"

if (-not (Test-Path $backupRoot)) {
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
}
if (-not (Test-Path $todayBackup)) {
    New-Item -ItemType Directory -Path $todayBackup -Force | Out-Null
}

Write-Host "  ✓ 백업 위치: $todayBackup" -ForegroundColor Green

# 3. 설정 파일 백업
Write-Host "`n⚙️  [3/6] 설정 파일 백업 중..." -ForegroundColor Yellow

$configFiles = @(
    ".vscode\tasks.json"
    ".vscode\settings.json"
    "fdo_agi_repo\.venv\pyvenv.cfg"
    "LLM_Unified\ion-mentoring\package.json"
    "fdo_agi_repo\requirements.txt"
    "pytest.ini"
)

$configBackupDir = "$todayBackup\configs"
if (-not (Test-Path $configBackupDir)) {
    New-Item -ItemType Directory -Path $configBackupDir -Force | Out-Null
}

$configCount = 0
foreach ($file in $configFiles) {
    $fullPath = Join-Path $WorkspaceRoot $file
    if (Test-Path $fullPath) {
        $destDir = Join-Path $configBackupDir (Split-Path -Parent $file)
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        Copy-Item -Path $fullPath -Destination (Join-Path $configBackupDir $file) -Force -ErrorAction SilentlyContinue
        $configCount++
    }
}

Write-Host "  ✓ 설정 파일: $configCount 개 백업됨" -ForegroundColor Green

# 4. 최근 출력물 백업 (24시간)
Write-Host "`n📄 [4/6] 최근 출력물 백업 중..." -ForegroundColor Yellow

$outputsBackupDir = "$todayBackup\outputs"
if (-not (Test-Path $outputsBackupDir)) {
    New-Item -ItemType Directory -Path $outputsBackupDir -Force | Out-Null
}

$recentOutputs = Get-ChildItem -Path "$WorkspaceRoot\outputs" -File -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-24) }

$outputCount = 0
if ($recentOutputs) {
    foreach ($file in $recentOutputs) {
        Copy-Item -Path $file.FullName -Destination $outputsBackupDir -Force -ErrorAction SilentlyContinue
        $outputCount++
    }
}

Write-Host "  ✓ 출력물: $outputCount 개 백업됨" -ForegroundColor Green

# 5. 시스템 상태 스냅샷
Write-Host "`n📸 [5/6] 시스템 상태 스냅샷 저장 중..." -ForegroundColor Yellow

$statusSnapshot = @{
    timestamp = $timestamp
    note = $Note
    gitCommit = (git rev-parse HEAD 2>$null)
    gitBranch = (git branch --show-current 2>$null)
    taskQueueServer = (Test-NetConnection -ComputerName localhost -Port 8091 -WarningAction SilentlyContinue).TcpTestSucceeded
    pythonEnv = (Test-Path "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe")
    nodeModules = (Test-Path "$WorkspaceRoot\LLM_Unified\ion-mentoring\node_modules")
    autoStartEnabled = ($null -ne (Get-ScheduledTask -TaskName "AGI_MasterOrchestrator" -ErrorAction SilentlyContinue))
    backupLocation = $todayBackup
}

$snapshotFile = "$todayBackup\end_of_day_snapshot.json"
$statusSnapshot | ConvertTo-Json -Depth 5 | Out-File -FilePath $snapshotFile -Encoding UTF8
Write-Host "  ✓ 스냅샷 저장됨: $snapshotFile" -ForegroundColor Green

# 6. 백업 아카이브 생성 (선택)
Write-Host "`n📦 [6/6] 백업 아카이브 생성 중..." -ForegroundColor Yellow

if (-not $SkipArchive) {
    $archiveFile = "$backupRoot\backup_$dateStamp.zip"
    
    try {
        Compress-Archive -Path $todayBackup -DestinationPath $archiveFile -Force -ErrorAction Stop
        
        $archiveSize = [math]::Round((Get-Item $archiveFile).Length / 1MB, 2)
        Write-Host "  ✓ 아카이브 생성: $archiveFile ($archiveSize MB)" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠ 아카이브 생성 실패 (원본은 유지됨)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⊘ 아카이브 스킵됨 (-SkipArchive)" -ForegroundColor Gray
}

# 오래된 백업 정리 (14일 이상)
Write-Host "`n🗑️  오래된 백업 정리 중..." -ForegroundColor Yellow

$oldBackups = Get-ChildItem -Path $backupRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-14) }

if ($oldBackups) {
    $oldCount = ($oldBackups | Measure-Object).Count
    foreach ($old in $oldBackups) {
        Remove-Item -Path $old.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }
    Write-Host "  ✓ 오래된 백업 $oldCount 개 정리됨" -ForegroundColor Green
} else {
    Write-Host "  ✓ 정리할 오래된 백업 없음" -ForegroundColor Green
}

Pop-Location

# 최종 요약
Write-Host "`n╔════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   ✅ 일과 종료 백업 완료                       ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Green

Write-Host "`n📌 백업된 내용:" -ForegroundColor Cyan
Write-Host "  • 위치: $todayBackup" -ForegroundColor Gray
Write-Host "  • 설정 파일: $configCount 개" -ForegroundColor Gray
Write-Host "  • 출력물: $outputCount 개" -ForegroundColor Gray
Write-Host "  • Git 커밋: $(($statusSnapshot.gitCommit).Substring(0,7))" -ForegroundColor Gray
if (-not $SkipArchive) {
    Write-Host "  • 아카이브: backup_$dateStamp.zip" -ForegroundColor Gray
}

if ($Note) {
    Write-Host "`n📝 일과 노트: $Note" -ForegroundColor Cyan
}

Write-Host "`n💡 내일 시작 시:" -ForegroundColor Yellow
Write-Host "  1. VS Code 실행" -ForegroundColor Gray
Write-Host "  2. '시스템 점검해줘' 실행" -ForegroundColor Gray
Write-Host "  3. 이어서 작업 시작" -ForegroundColor Gray

Write-Host "`n🌙 Good night! 내일 봐요!" -ForegroundColor Cyan
Write-Host ""

exit 0
