#Requires -Version 5.1
<#
.SYNOPSIS
    시스템 점검 - 재부팅/재실행 후 모든 변경사항이 잘 적용되었는지 확인
.DESCRIPTION
    1. 이전 세션 컨텍스트 로드
    2. Git 상태 확인
    3. 의존성 설치 상태 확인
    4. 프로세스 상태 확인
    5. 자동 시작 설정 확인
    6. 최근 출력물 확인
    7. 다음 작업 제안
#>

param(
    [string]$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } ) = "$PSScriptRoot\..",
    [switch]$AutoFix,
    [switch]$Verbose
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Continue"

Write-Host "`n╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   시스템 점검 - 재부팅/재실행 후 상태 확인    ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

Push-Location $WorkspaceRoot

$allChecks = @()
$warningCount = 0
$errorCount = 0

# 1. 이전 세션 컨텍스트 확인
Write-Host "📋 [1/8] 이전 세션 컨텍스트 확인 중..." -ForegroundColor Yellow

$contextFile = "$WorkspaceRoot\outputs\next_session_context.json"
$lastContext = $null
if (Test-Path $contextFile) {
    $lastContext = Get-Content $contextFile -Raw | ConvertFrom-Json
    Write-Host "  ✓ 이전 세션: $($lastContext.savedAt)" -ForegroundColor Green
    if ($lastContext.note) {
        Write-Host "    노트: $($lastContext.note)" -ForegroundColor Gray
    }
    $allChecks += @{name = "이전 세션 컨텍스트"; status = "✓"; color = "Green" }
}
else {
    Write-Host "  ⊘ 이전 세션 컨텍스트 없음 (첫 실행)" -ForegroundColor Gray
    $allChecks += @{name = "이전 세션 컨텍스트"; status = "⊘"; color = "Gray" }
}

# 2. Git 상태 확인
Write-Host "`n🔀 [2/8] Git 상태 확인 중..." -ForegroundColor Yellow

$currentCommit = git rev-parse HEAD 2>$null
$gitStatus = git status --porcelain 2>$null

if ($lastContext -and $lastContext.lastCommit -eq $currentCommit) {
    Write-Host "  ✓ Git 커밋 일치: $(($currentCommit).Substring(0,7))" -ForegroundColor Green
    $allChecks += @{name = "Git 커밋"; status = "✓"; color = "Green" }
}
elseif ($lastContext) {
    Write-Host "  ⚠ Git 커밋 변경됨:" -ForegroundColor Yellow
    Write-Host "    이전: $(($lastContext.lastCommit).Substring(0,7))" -ForegroundColor Gray
    Write-Host "    현재: $(($currentCommit).Substring(0,7))" -ForegroundColor Gray
    $warningCount++
    $allChecks += @{name = "Git 커밋"; status = "⚠"; color = "Yellow" }
}
else {
    Write-Host "  ✓ 현재 커밋: $(($currentCommit).Substring(0,7))" -ForegroundColor Green
    $allChecks += @{name = "Git 커밋"; status = "✓"; color = "Green" }
}

if ($gitStatus) {
    $changedCount = ($gitStatus | Measure-Object).Count
    Write-Host "  ⚠ 미커밋 변경: $changedCount 개 파일" -ForegroundColor Yellow
    $warningCount++
}
else {
    Write-Host "  ✓ 워킹 디렉토리 깨끗함" -ForegroundColor Green
}

# 3. Python 가상환경 확인
Write-Host "`n🐍 [3/8] Python 가상환경 확인 중..." -ForegroundColor Yellow

$pyExe = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
if (Test-Path $pyExe) {
    $pyVersion = (& $pyExe --version 2>&1) -replace "Python ", ""
    Write-Host "  ✓ Python 가상환경: $pyVersion" -ForegroundColor Green
    
    # pip 패키지 확인
    $reqFile = "$WorkspaceRoot\fdo_agi_repo\requirements.txt"
    if (Test-Path $reqFile) {
        Write-Host "  ✓ requirements.txt 존재" -ForegroundColor Green
    }
    $allChecks += @{name = "Python 가상환경"; status = "✓"; color = "Green" }
}
else {
    Write-Host "  ✗ Python 가상환경 없음" -ForegroundColor Red
    $errorCount++
    $allChecks += @{name = "Python 가상환경"; status = "✗"; color = "Red" }
    
    if ($AutoFix) {
        Write-Host "  🔧 자동 수정 시도..." -ForegroundColor Cyan
        # TODO: 가상환경 자동 생성
    }
}

# 4. Node.js 의존성 확인
Write-Host "`n📦 [4/8] Node.js 의존성 확인 중..." -ForegroundColor Yellow

$nodeModules = "$WorkspaceRoot\LLM_Unified\ion-mentoring\node_modules"
if (Test-Path $nodeModules) {
    $pkgCount = (Get-ChildItem $nodeModules -Directory).Count
    Write-Host "  ✓ Node modules: $pkgCount 개 패키지" -ForegroundColor Green
    $allChecks += @{name = "Node.js 의존성"; status = "✓"; color = "Green" }
}
else {
    Write-Host "  ⚠ Node modules 없음" -ForegroundColor Yellow
    $warningCount++
    $allChecks += @{name = "Node.js 의존성"; status = "⚠"; color = "Yellow" }
    
    if ($AutoFix) {
        Write-Host "  🔧 자동 설치 시도..." -ForegroundColor Cyan
        $pkgDir = "$WorkspaceRoot\LLM_Unified\ion-mentoring"
        if (Test-Path "$pkgDir\package.json") {
            Push-Location $pkgDir
            npm install --silent 2>&1 | Out-Null
            Pop-Location
        }
    }
}

# 5. 핵심 프로세스 상태 확인
Write-Host "`n⚙️  [5/8] 핵심 프로세스 상태 확인 중..." -ForegroundColor Yellow

# Task Queue Server
$serverRunning = (Test-NetConnection -ComputerName localhost -Port 8091 -WarningAction SilentlyContinue).TcpTestSucceeded
if ($serverRunning) {
    Write-Host "  ✓ Task Queue Server (8091): Running" -ForegroundColor Green
    $allChecks += @{name = "Task Queue Server"; status = "✓"; color = "Green" }
}
else {
    Write-Host "  ✗ Task Queue Server (8091): Not Running" -ForegroundColor Red
    $errorCount++
    $allChecks += @{name = "Task Queue Server"; status = "✗"; color = "Red" }
    
    if ($AutoFix) {
        Write-Host "  🔧 자동 시작 시도..." -ForegroundColor Cyan
        & "$WorkspaceRoot\scripts\ensure_task_queue_server.ps1" -Port 8091
    }
}

# RPA Worker (프로세스 검색) - PS 5.1 호환: CommandLine 접근은 Win32_Process로 시도 후, 실패 시 단순 존재 체크로 폴백
$workerProc = $null
try {
    $workerProc = Get-CimInstance -ClassName Win32_Process -ErrorAction Stop |
        Where-Object { $_.Name -match '^python(\.exe)?$' -and ($_.CommandLine -like '*rpa_worker.py*') } |
        Select-Object -First 1
}
catch {
    # WinRM 비활성/권한 문제 등으로 CIM 쿼리 실패 시 Get-Process로 폴백 (정확도 낮음)
    $workerProc = Get-Process -Name python -ErrorAction SilentlyContinue |
        Select-Object -First 1
}

if ($workerProc) {
    $workerPid = if ($workerProc.PSObject.Properties['ProcessId']) { $workerProc.ProcessId } elseif ($workerProc.PSObject.Properties['Id']) { $workerProc.Id } else { $null }
    $msg = "  ✓ RPA Worker: Running"
    if ($workerPid) { $msg += " (PID: $workerPid)" }
    Write-Host $msg -ForegroundColor Green
    $allChecks += @{name = "RPA Worker"; status = "✓"; color = "Green" }
}
else {
    Write-Host "  ⚠ RPA Worker: Not Running" -ForegroundColor Yellow
    $warningCount++
    $allChecks += @{name = "RPA Worker"; status = "⚠"; color = "Yellow" }
    
    if ($AutoFix) {
        Write-Host "  🔧 자동 시작 시도..." -ForegroundColor Cyan
        & "$WorkspaceRoot\scripts\ensure_rpa_worker.ps1"
    }
}

# 6. 자동 시작 설정 확인
Write-Host "`n🚀 [6/8] 자동 시작 설정 확인 중..." -ForegroundColor Yellow

$masterTask = Get-ScheduledTask -TaskName "AGI_MasterOrchestrator" -ErrorAction SilentlyContinue
if ($null -ne $masterTask) {
    $taskState = $masterTask.State
    Write-Host "  ✓ Master Orchestrator: 등록됨 ($taskState)" -ForegroundColor Green
    $allChecks += @{name = "Master Orchestrator"; status = "✓"; color = "Green" }
}
else {
    Write-Host "  ⚠ Master Orchestrator: 미등록" -ForegroundColor Yellow
    $warningCount++
    $allChecks += @{name = "Master Orchestrator"; status = "⚠"; color = "Yellow" }
}

$backupTask = Get-ScheduledTask -TaskName "AGI_DailyBackup" -ErrorAction SilentlyContinue
if ($null -ne $backupTask) {
    $taskState = $backupTask.State
    Write-Host "  ✓ Daily Backup: 등록됨 ($taskState)" -ForegroundColor Green
    $allChecks += @{name = "Daily Backup"; status = "✓"; color = "Green" }
}
else {
    Write-Host "  ⊘ Daily Backup: 미등록 (선택사항)" -ForegroundColor Gray
    $allChecks += @{name = "Daily Backup"; status = "⊘"; color = "Gray" }
}

# 7. 최근 출력물 확인
Write-Host "`n📄 [7/8] 최근 출력물 확인 중..." -ForegroundColor Yellow

$recentOutputs = Get-ChildItem -Path "$WorkspaceRoot\outputs" -File -ErrorAction SilentlyContinue |
Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-24) }

if ($recentOutputs) {
    $outputCount = ($recentOutputs | Measure-Object).Count
    Write-Host "  ✓ 최근 24시간 출력물: $outputCount 개" -ForegroundColor Green
    if ($Verbose) {
        $recentOutputs | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | ForEach-Object {
            Write-Host "    - $($_.Name) ($(($_.LastWriteTime).ToString('HH:mm')))" -ForegroundColor Gray
        }
    }
    $allChecks += @{name = "최근 출력물"; status = "✓"; color = "Green" }
}
else {
    Write-Host "  ⊘ 최근 24시간 출력물 없음" -ForegroundColor Gray
    $allChecks += @{name = "최근 출력물"; status = "⊘"; color = "Gray" }
}

# 8. 전체 건강도 평가
Write-Host "`n🏥 [8/8] 전체 시스템 건강도 평가 중..." -ForegroundColor Yellow

$totalChecks = $allChecks.Count
$passedChecks = ($allChecks | Where-Object { $_.status -eq "✓" }).Count
$healthPercentage = [math]::Round(($passedChecks / $totalChecks) * 100)

Pop-Location

# 최종 요약
Write-Host "`n╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   시스템 점검 결과                             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

foreach ($check in $allChecks) {
    $status = $check.status
    $name = $check.name.PadRight(30)
    $color = $check.color
    Write-Host "  $status $name" -ForegroundColor $color
}

Write-Host "`n───────────────────────────────────────────────" -ForegroundColor Gray
Write-Host "  통과: $passedChecks / $totalChecks ($healthPercentage%)" -ForegroundColor Cyan
Write-Host "  경고: $warningCount" -ForegroundColor $(if ($warningCount -gt 0) { "Yellow" } else { "Gray" })
Write-Host "  오류: $errorCount" -ForegroundColor $(if ($errorCount -gt 0) { "Red" } else { "Gray" })
Write-Host "───────────────────────────────────────────────" -ForegroundColor Gray

# 상태 판정
if ($errorCount -eq 0 -and $warningCount -eq 0) {
    Write-Host "`n  🟢 시스템 상태: 완벽 (ALL SYSTEMS GO)" -ForegroundColor Green
    Write-Host "  💡 다음 작업을 이어갈 준비가 되었습니다." -ForegroundColor Cyan
}
elseif ($errorCount -eq 0) {
    Write-Host "`n  🟡 시스템 상태: 양호 (READY WITH WARNINGS)" -ForegroundColor Yellow
    Write-Host "  💡 작업 가능하나 일부 최적화 필요" -ForegroundColor Cyan
}
else {
    Write-Host "`n  🔴 시스템 상태: 주의 필요 (NEEDS ATTENTION)" -ForegroundColor Red
    Write-Host "  💡 일부 핵심 기능이 작동하지 않습니다." -ForegroundColor Cyan
    
    if (-not $AutoFix) {
        Write-Host "`n  🔧 자동 수정 시도: -AutoFix 옵션 사용" -ForegroundColor Yellow
    }
}

# 다음 작업 제안
if ($lastContext -and $lastContext.actionItems) {
    Write-Host "`n📌 이전 세션 액션 아이템:" -ForegroundColor Cyan
    foreach ($item in $lastContext.actionItems) {
        Write-Host "  • $item" -ForegroundColor Gray
    }
}

Write-Host ""
exit $(if ($errorCount -gt 0) { 1 } else { 0 })