# ?동 백업 ?크립트
# 중요 ?로?트??기?으?백업?니??
param(
    [string]$BackupRoot = "D:\backup\AutoBackup",
    [switch]$DryRun,
    [switch]$Verbose
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = "SilentlyContinue"
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'

# 백업 ????의
$backupTargets = @(
    @{
        Name     = "LLM_Unified"
        Source   = "$WorkspaceRoot\LLM_Unified"
        Exclude  = @("__pycache__", ".venv", "*.pyc", "*.log", ".pytest_cache", "outputs\*.json")
        Critical = $true
    },
    @{
        Name     = "Ion_Mentoring"
        Source   = "$WorkspaceRoot\LLM_Unified\ion-mentoring"
        Exclude  = @("__pycache__", "outputs", "*.log")
        Critical = $true
    },
    @{
        Name     = "Gitko_Extension"
        Source   = "$WorkspaceRoot\gitko-agent-extension"
        Exclude  = @("node_modules", "out", "*.vsix")
        Critical = $true
    },
    @{
        Name     = "Scripts"
        Source   = "$WorkspaceRoot\scripts"
        Exclude  = @()
        Critical = $true
    },
    @{
        Name     = "Obsidian_Vault"
        Source   = "D:\obsidian-vault"
        Exclude  = @(".obsidian\workspace*", ".trash")
        Critical = $true
    }
)

Write-Host "=== ?동 백업 ?작 ===" -ForegroundColor Cyan
Write-Host "??스?프: $timestamp" -ForegroundColor Yellow
Write-Host "백업 경로: $BackupRoot" -ForegroundColor Yellow
if ($DryRun) {
    Write-Host "모드: DRY RUN (?제 복사?? ?음)" -ForegroundColor Magenta
}
Write-Host ""

# 백업 루트 ?렉?리 ?성
if (-not $DryRun) {
    if (-not (Test-Path $BackupRoot)) {
        New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
    }
}

# 백업 로그 초기??$logPath = Join-Path $BackupRoot "backup_log_$timestamp.txt"
$summaryLog = @()

foreach ($target in $backupTargets) {
    Write-Host "[$($target.Name)]" -ForegroundColor Green
    
    if (-not (Test-Path $target.Source)) {
        Write-Host "  경고: ?스 ?더가 존재?? ?습?다: $($target.Source)" -ForegroundColor Red
        $summaryLog += "[ERROR] $($target.Name): ?스 ?더 ?음"
        continue
    }
    
    # 백업 ???경로
    $destination = Join-Path $BackupRoot "$($target.Name)_$timestamp"
    
    # ?외 ?턴 구성
    $excludeParams = @()
    foreach ($exclude in $target.Exclude) {
        $excludeParams += "/XF"
        $excludeParams += $exclude
        $excludeParams += "/XD"
        $excludeParams += $exclude
    }
    
    Write-Host "  ?스: $($target.Source)" -ForegroundColor Gray
    Write-Host "  ??? $destination" -ForegroundColor Gray
    
    if ($DryRun) {
        Write-Host "  [DRY RUN] 복사?? ?음" -ForegroundColor Magenta
        $summaryLog += "[SEARCH] $($target.Name): Dry Run ?료"
    }
    else {
        # Robocopy??용??백업
        $robocopyArgs = @(
            $target.Source,
            $destination,
            "/MIR",           # 미러?(?본??일?게)
            "/R:3",           # ?시??3??            "/W:5",           # ??5?            "/MT:8",          # 멀?스?드 8?            "/NP",            # 진행??시 ????(로그 간소??
            "/NFL",           # ?일 목록 ????            "/NDL"            # ?렉?리 목록 ????        ) + $excludeParams
        
        if ($Verbose) {
            $robocopyArgs += "/V"  # ?세 출력
        }
        
        $logFile = Join-Path $BackupRoot "$($target.Name)_$timestamp.log"
        $robocopyArgs += "/LOG:$logFile"
        
        Write-Host "  백업 ?.." -ForegroundColor Yellow
        & robocopy @robocopyArgs | Out-Null
        
        # Robocopy 종료 코드 ?석
        # 0-1: ?공, 2-7: 부??공/경고, 8+: ?류
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -le 1) {
            Write-Host "  ??백업 ?료" -ForegroundColor Green
            $summaryLog += "[OK] $($target.Name): 백업 ?공"
        }
        elseif ($exitCode -le 7) {
            Write-Host "  [WARN] 백업 ?료 (경고 ?음, 코드: $exitCode)" -ForegroundColor Yellow
            $summaryLog += "[WARN] $($target.Name): 백업 ?료 (경고)"
        }
        else {
            Write-Host "  ??백업 ?패 (코드: $exitCode)" -ForegroundColor Red
            $summaryLog += "[ERROR] $($target.Name): 백업 ?패"
        }
        
        # 백업 ?기 ?인
        if (Test-Path $destination) {
            $size = (Get-ChildItem $destination -Recurse -File | Measure-Object -Property Length -Sum).Sum
            $sizeMB = [math]::Round($size / 1MB, 2)
            Write-Host "  ?기: $sizeMB MB" -ForegroundColor Cyan
        }
    }
    
    Write-Host ""
}

# ?약 보고??Write-Host "=== 백업 ?약 ===" -ForegroundColor Cyan
foreach ($log in $summaryLog) {
    Write-Host $log
}
Write-Host ""

# 백업 로그 ???if (-not $DryRun) {
    $report = @"
?동 백업 보고???성 ?간: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
백업 경로: $BackupRoot

=== 백업 ???===
$($backupTargets | ForEach-Object { "- $($_.Name): $($_.Source)" } | Out-String)

=== 백업 결과 ===
$($summaryLog | Out-String)

=== ?음 ?계 ===
1. 백업 무결???인: 주요 ?일???바르게 복사?었?? 검?2. ?라?드 ?기?? 중요 백업??Google Drive ?는 OneDrive???로??3. ?기 백업 ??? Windows ?업 ??줄러??동???정
4. ?래??백업 ?리: 30???상 ??백업? 검??????

=== 복원 방법 ===
?백업 ?더??래 ?치?복사?면 ?니??
?? robocopy "$BackupRoot\LLM_Unified_$timestamp" "$WorkspaceRoot\LLM_Unified" /MIR

"@
    
    $report | Out-File -FilePath $logPath -Encoding UTF8
    Write-Host "백업 로그 ??? $logPath" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== 백업 ?료 ===" -ForegroundColor Green

# ?래??백업 ?리 (?택 ?항)
if (-not $DryRun) {
    Write-Host ""
    Write-Host "?래??백업 ?리 ????인?고 ?으?면 -CleanOld ?위치? 추??세??" -ForegroundColor Gray
}