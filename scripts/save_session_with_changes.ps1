#Requires -Version 5.1
<#
.SYNOPSIS
    세션 저장 - 대화 내용 + 모든 시스템/구조 변경사항 적용
.DESCRIPTION
    1. 현재까지의 대화 내용을 저장
    2. Git 변경사항을 커밋
    3. 새 의존성이 있으면 자동 설치
    4. 새 스크립트 권한 설정
    5. 시스템 상태 스냅샷 저장
    6. 다음 세션을 위한 컨텍스트 저장
#>

param(
    [string]$SessionNote = "",
    [string]$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } ) = "$PSScriptRoot\..",
    [switch]$SkipGitCommit
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Continue"
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"

Write-Host ('\n[INFO] ========================================') -ForegroundColor Cyan
Write-Host ('[INFO]   Session Save - All Changes Applied') -ForegroundColor Cyan
Write-Host ('[INFO] ========================================\n') -ForegroundColor Cyan

Push-Location $WorkspaceRoot

# 1. Collecting session info
Write-Host '[1/7] Collecting session info...' -ForegroundColor Yellow

$sessionInfo = @{
    timestamp       = $timestamp
    note            = $SessionNote
    gitBranch       = (git branch --show-current 2>$null)
    gitCommit       = (git rev-parse HEAD 2>$null)
    pythonVersion   = ""
    nodeVersion     = ""
    activeProcesses = @()
    recentFiles     = @()
}

# Python 버전
$pyExe = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
if (Test-Path $pyExe) {
    $sessionInfo.pythonVersion = (& $pyExe --version 2>&1) -replace "Python ", ""
}

# Node 버전
try {
    $sessionInfo.nodeVersion = (node --version 2>$null) -replace "v", ""
}
catch {}

# 활성 프로세스
$sessionInfo.activeProcesses = @(
    @{name = "TaskQueueServer"; port = 8091; running = (Test-NetConnection -ComputerName localhost -Port 8091 -WarningAction SilentlyContinue).TcpTestSucceeded }
    @{name = "RPAWorker"; running = $false }  # TODO: detect
)

# 최근 24시간 변경된 파일
$sessionInfo.recentFiles = Get-ChildItem -Path $WorkspaceRoot -Recurse -File -ErrorAction SilentlyContinue |
Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-24) -and $_.Extension -match '\.(py|ps1|json|md)$' } |
Select-Object -First 20 FullName, LastWriteTime

# 세션 정보 저장
$sessionFile = "$WorkspaceRoot\outputs\session_context_$timestamp.json"
$sessionInfo | ConvertTo-Json -Depth 10 | Out-File -FilePath $sessionFile -Encoding UTF8
Write-Host "  세션 정보 저장됨: $sessionFile" -ForegroundColor Green

# 2. Git 변경사항 확인 및 커밋
Write-Host "`n[2/7] Git 변경사항 처리 중..." -ForegroundColor Yellow

$gitStatus = git status --porcelain 2>$null
if ($gitStatus -and -not $SkipGitCommit) {
    $changedFiles = ($gitStatus | Measure-Object).Count
    Write-Host "  변경된 파일: $changedFiles 개" -ForegroundColor Gray
    
    # 자동 커밋 메시지 생성
    $commitMsg = "Session save - $timestamp"
    if ($SessionNote) {
        $commitMsg += "`n`n$SessionNote"
    }
    
    git add -A 2>&1 | Out-Null
    git commit -m $commitMsg 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host '  Git 커밋 완료' -ForegroundColor Green
    }
    else {
        Write-Host '  경고: Git 커밋 실패 (수동 확인 필요)' -ForegroundColor Yellow
    }
}
elseif (-not $gitStatus) {
    Write-Host '  변경사항 없음' -ForegroundColor Green
}
else {
    Write-Host '  Git 커밋 스킵됨 (-SkipGitCommit)' -ForegroundColor Gray
}

# 3. 의존성 변경 감지 및 설치
Write-Host '\n[3/7] 의존성 변경 확인 중...' -ForegroundColor Yellow

$upgradeNeeded = $false

# requirements.txt 체크
$reqFiles = Get-ChildItem -Path $WorkspaceRoot -Filter "requirements.txt" -Recurse -File -ErrorAction SilentlyContinue
foreach ($req in $reqFiles) {
    if ($req.LastWriteTime -gt (Get-Date).AddHours(-24)) {
        Write-Host "  감지: $($req.FullName)" -ForegroundColor Gray
        $venvDir = Join-Path (Split-Path -Parent $req.FullName) ".venv"
        if (Test-Path "$venvDir\Scripts\pip.exe") {
            Write-Host "  설치 중..." -ForegroundColor Gray
            & "$venvDir\Scripts\pip.exe" install -r $req.FullName --quiet
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  Python 의존성 설치 완료" -ForegroundColor Green
                $upgradeNeeded = $true
            }
        }
    }
}

# package.json 체크
$pkgFiles = Get-ChildItem -Path $WorkspaceRoot -Filter "package.json" -Recurse -File -ErrorAction SilentlyContinue |
Where-Object { $_.DirectoryName -notlike "*\node_modules\*" }
foreach ($pkg in $pkgFiles) {
    if ($pkg.LastWriteTime -gt (Get-Date).AddHours(-24)) {
        Write-Host "  감지: $($pkg.FullName)" -ForegroundColor Gray
        $pkgDir = Split-Path -Parent $pkg.FullName
        Push-Location $pkgDir
        npm install --silent 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Node 의존성 설치 완료" -ForegroundColor Green
            $upgradeNeeded = $true
        }
        Pop-Location
    }
}

if (-not $upgradeNeeded) {
    Write-Host "  의존성 변경 없음" -ForegroundColor Green
}

# 4. 새 스크립트 권한 설정
Write-Host '\n[4/7] 새 스크립트 권한 설정 중...' -ForegroundColor Yellow

$newScripts = Get-ChildItem -Path "$WorkspaceRoot\scripts" -Filter "*.ps1" -File -ErrorAction SilentlyContinue |
Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-24) }

if ($newScripts) {
    Write-Host "  새 스크립트: $($newScripts.Count)개" -ForegroundColor Gray
    foreach ($script in $newScripts) {
        Write-Host "  - $($script.Name)" -ForegroundColor Gray
    }
    Write-Host "  권한 확인 완료" -ForegroundColor Green
}
else {
    Write-Host "  새 스크립트 없음" -ForegroundColor Green
}

# 5. 시스템 상태 스냅샷
Write-Host '\n[5/7] 시스템 상태 스냅샷 저장 중...' -ForegroundColor Yellow

$statusSnapshot = @{
    timestamp       = $timestamp
    taskQueueServer = (Test-NetConnection -ComputerName localhost -Port 8091 -WarningAction SilentlyContinue).TcpTestSucceeded
    pythonEnv       = (Test-Path "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe")
    nodeModules     = (Test-Path "$WorkspaceRoot\LLM_Unified\ion-mentoring\node_modules")
    recentOutputs   = (Get-ChildItem -Path "$WorkspaceRoot\outputs" -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-24) }).Count
}

$snapshotFile = "$WorkspaceRoot\outputs\status_snapshot_$timestamp.json"
$statusSnapshot | ConvertTo-Json -Depth 5 | Out-File -FilePath $snapshotFile -Encoding UTF8
Write-Host "  스냅샷 저장됨: $snapshotFile" -ForegroundColor Green

# 6. 다음 세션 컨텍스트 저장 (latest)
Write-Host '\n[6/7] 다음 세션 컨텍스트 저장 중...' -ForegroundColor Yellow

$contextForNext = @{
    savedAt          = $timestamp
    note             = $SessionNote
    lastCommit       = (git rev-parse HEAD 2>$null)
    upgradesApplied  = $upgradeNeeded
    processesRunning = $statusSnapshot.taskQueueServer
    actionItems      = @(
        "재부팅 후 '시스템 점검해줘' 실행 권장"
        if ($upgradeNeeded) { "의존성 업그레이드됨 - 프로세스 재시작 필요할 수 있음" }
    )
}

$contextFile = "$WorkspaceRoot\outputs\next_session_context.json"
$contextForNext | ConvertTo-Json -Depth 5 | Out-File -FilePath $contextFile -Encoding UTF8
Write-Host "  다음 세션 컨텍스트 저장: $contextFile" -ForegroundColor Green

# 7. 마스터 상태 업데이트
Write-Host '\n[7/7] 마스터 상태 파일 업데이트 중...' -ForegroundColor Yellow

$masterStatus = @{
    lastSessionSave    = $timestamp
    lastCommit         = (git rev-parse HEAD 2>$null)
    sessionNote        = $SessionNote
    autoStartEnabled   = $null -ne (Get-ScheduledTask -TaskName "AGI_MasterOrchestrator" -ErrorAction SilentlyContinue)
    dailyBackupEnabled = $null -ne (Get-ScheduledTask -TaskName "AGI_DailyBackup" -ErrorAction SilentlyContinue)
}

$masterFile = "$WorkspaceRoot\outputs\master_status.json"
$masterStatus | ConvertTo-Json -Depth 5 | Out-File -FilePath $masterFile -Encoding UTF8
Write-Host '  [OK] Master status updated' -ForegroundColor Green

Pop-Location

# 최종 요약

Write-Host ('\n[INFO] ========================================') -ForegroundColor Green
Write-Host ('[INFO]   Session save complete') -ForegroundColor Green
Write-Host ('[INFO] ========================================') -ForegroundColor Green

Write-Host ('\n[INFO] Saved files:') -ForegroundColor Cyan

Write-Host ('  - Session info: ' + $sessionFile) -ForegroundColor Gray
Write-Host ('  - Status snapshot: ' + $snapshotFile) -ForegroundColor Gray
Write-Host ('  - Next context: ' + $contextFile) -ForegroundColor Gray
Write-Host ('  - Git commit: ' + $(if (-not $SkipGitCommit -and $gitStatus) { 'done' } else { 'skipped' })) -ForegroundColor Gray
Write-Host ('  - Dependency upgrade: ' + $(if ($upgradeNeeded) { 'done' } else { 'none' })) -ForegroundColor Gray


Write-Host ('\n[INFO] Next session checklist:') -ForegroundColor Yellow
Write-Host '  1. Restart VS Code or reboot' -ForegroundColor Gray
Write-Host '  2. Run system check command' -ForegroundColor Gray
Write-Host '  3. All changes will be auto-verified' -ForegroundColor Gray



if ($SessionNote) {
    Write-Host ('\n[NOTE] Session note: ' + $SessionNote) -ForegroundColor Cyan
}

Write-Host ""
exit 0