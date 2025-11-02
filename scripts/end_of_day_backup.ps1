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

Write-Host "\n===============================================" -ForegroundColor Cyan
Write-Host "|   End of Day Backup - Session Complete      |" -ForegroundColor Cyan
Write-Host "===============================================\n" -ForegroundColor Cyan

Push-Location $WorkspaceRoot

# 1. 세션 저장 먼저 실행
Write-Host "[1/6] Saving session..." -ForegroundColor Yellow

$saveSessionScript = "$WorkspaceRoot\scripts\save_session_with_changes.ps1"
if (Test-Path $saveSessionScript) {
    & $saveSessionScript -SessionNote $Note
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Session saved." -ForegroundColor Green
    }
    else {
        Write-Host "  Warning: Session save warning (continuing)" -ForegroundColor Yellow
    }
}
else {
    Write-Host "  Warning: Session save script not found (skipped)" -ForegroundColor Yellow
}

# 2. 백업 디렉토리 준비
Write-Host "\n[2/6] Preparing backup directory..." -ForegroundColor Yellow

$backupRoot = "$WorkspaceRoot\backups"
$todayBackup = "$backupRoot\$dateStamp"

if (-not (Test-Path $backupRoot)) {
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
}
if (-not (Test-Path $todayBackup)) {
    New-Item -ItemType Directory -Path $todayBackup -Force | Out-Null
}

Write-Host "  Backup location: $todayBackup" -ForegroundColor Green

# 3. 설정 파일 백업
Write-Host "\n[3/6] Backing up config files..." -ForegroundColor Yellow

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

Write-Host "  Config files: $configCount backed up" -ForegroundColor Green

# 4. 최근 출력물 백업 (24시간)
Write-Host "\n[4/6] Backing up recent outputs..." -ForegroundColor Yellow

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

Write-Host "  Outputs: $outputCount backed up" -ForegroundColor Green

# 5. 시스템 상태 스냅샷
Write-Host "\n[5/6] Saving system status snapshot..." -ForegroundColor Yellow

$statusSnapshot = @{
    timestamp        = $timestamp
    note             = $Note
    gitCommit        = (git rev-parse HEAD 2>$null)
    gitBranch        = (git branch --show-current 2>$null)
    taskQueueServer  = (Test-NetConnection -ComputerName localhost -Port 8091 -WarningAction SilentlyContinue).TcpTestSucceeded
    pythonEnv        = (Test-Path "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe")
    nodeModules      = (Test-Path "$WorkspaceRoot\LLM_Unified\ion-mentoring\node_modules")
    autoStartEnabled = ($null -ne (Get-ScheduledTask -TaskName "AGI_MasterOrchestrator" -ErrorAction SilentlyContinue))
    backupLocation   = $todayBackup
}

$snapshotFile = "$todayBackup\end_of_day_snapshot.json"
$statusSnapshot | ConvertTo-Json -Depth 5 | Out-File -FilePath $snapshotFile -Encoding UTF8
Write-Host "  Snapshot saved: $snapshotFile" -ForegroundColor Green

# 6. 백업 아카이브 생성 (선택)
Write-Host "\n[6/6] Creating backup archive..." -ForegroundColor Yellow

if (-not $SkipArchive) {
    $archiveFile = "$backupRoot\backup_$dateStamp.zip"
    
    try {
        Compress-Archive -Path $todayBackup -DestinationPath $archiveFile -Force -ErrorAction Stop
        
        $archiveSize = [math]::Round((Get-Item $archiveFile).Length / 1MB, 2)
        Write-Host ("  Archive created: {0} ({1} MB)" -f $archiveFile, $archiveSize) -ForegroundColor Green
    }
    catch {
        Write-Host "  Warning: Archive creation failed (original files kept)" -ForegroundColor Yellow
    }
}
else {
    Write-Host "  Archive skipped (-SkipArchive)" -ForegroundColor Gray
}

# 오래된 백업 정리 (14일 이상)
Write-Host "\n[Cleanup] Old backups cleanup..." -ForegroundColor Yellow

$oldBackups = Get-ChildItem -Path $backupRoot -Directory -ErrorAction SilentlyContinue |
Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-14) }

if ($oldBackups) {
    $oldCount = ($oldBackups | Measure-Object).Count
    foreach ($old in $oldBackups) {
        Remove-Item -Path $old.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }
    Write-Host "  Old backups cleaned: $oldCount" -ForegroundColor Green
}
else {
    Write-Host "  No old backups to clean" -ForegroundColor Green
}

Pop-Location

# 최종 요약
Write-Host "\n===============================================" -ForegroundColor Green
Write-Host "|   End of Day Backup Complete                |" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

Write-Host "\n[Summary] Backup details:" -ForegroundColor Cyan
Write-Host "  - Location: $todayBackup" -ForegroundColor Gray
Write-Host "  - Config files: $configCount" -ForegroundColor Gray
Write-Host "  - Outputs: $outputCount" -ForegroundColor Gray
Write-Host "  - Git commit: $(($statusSnapshot.gitCommit).Substring(0,7))" -ForegroundColor Gray
if (-not $SkipArchive) {
    Write-Host "  - Archive: backup_$dateStamp.zip" -ForegroundColor Gray
}

if ($Note) {
    Write-Host "\n[Note] $Note" -ForegroundColor Cyan
}

Write-Host "\n[Next steps for tomorrow]:" -ForegroundColor Yellow
Write-Host "  1. Launch VS Code" -ForegroundColor Gray
Write-Host "  2. Run 'system check'" -ForegroundColor Gray
Write-Host "  3. Resume work" -ForegroundColor Gray
Write-Host "  4. Morning kickoff: scripts/morning_kickoff.ps1 -Hours 1 -OpenHtml" -ForegroundColor Gray

Write-Host "\nGood night! See you tomorrow!" -ForegroundColor Cyan
Write-Host ""

exit 0
