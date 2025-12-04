# ?ë™ ë°±ì—… ?¤í¬ë¦½íŠ¸
# ì¤‘ìš” ?„ë¡œ?íŠ¸ë¥??•ê¸°?ìœ¼ë¡?ë°±ì—…?©ë‹ˆ??
param(
    [string]$BackupRoot = "D:\backup\AutoBackup",
    [switch]$DryRun,
    [switch]$Verbose
)

$ErrorActionPreference = "SilentlyContinue"
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'

# ë°±ì—… ?€???•ì˜
$backupTargets = @(
    @{
        Name     = "LLM_Unified"
        Source   = "C:\workspace\agi\LLM_Unified"
        Exclude  = @("__pycache__", ".venv", "*.pyc", "*.log", ".pytest_cache", "outputs\*.json")
        Critical = $true
    },
    @{
        Name     = "Ion_Mentoring"
        Source   = "C:\workspace\agi\LLM_Unified\ion-mentoring"
        Exclude  = @("__pycache__", "outputs", "*.log")
        Critical = $true
    },
    @{
        Name     = "Gitko_Extension"
        Source   = "C:\workspace\agi\gitko-agent-extension"
        Exclude  = @("node_modules", "out", "*.vsix")
        Critical = $true
    },
    @{
        Name     = "Scripts"
        Source   = "C:\workspace\agi\scripts"
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

Write-Host "=== ?ë™ ë°±ì—… ?œì‘ ===" -ForegroundColor Cyan
Write-Host "?€?„ìŠ¤?¬í”„: $timestamp" -ForegroundColor Yellow
Write-Host "ë°±ì—… ê²½ë¡œ: $BackupRoot" -ForegroundColor Yellow
if ($DryRun) {
    Write-Host "ëª¨ë“œ: DRY RUN (?¤ì œ ë³µì‚¬?˜ì? ?ŠìŒ)" -ForegroundColor Magenta
}
Write-Host ""

# ë°±ì—… ë£¨íŠ¸ ?”ë ‰? ë¦¬ ?ì„±
if (-not $DryRun) {
    if (-not (Test-Path $BackupRoot)) {
        New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
    }
}

# ë°±ì—… ë¡œê·¸ ì´ˆê¸°??$logPath = Join-Path $BackupRoot "backup_log_$timestamp.txt"
$summaryLog = @()

foreach ($target in $backupTargets) {
    Write-Host "[$($target.Name)]" -ForegroundColor Green
    
    if (-not (Test-Path $target.Source)) {
        Write-Host "  ê²½ê³ : ?ŒìŠ¤ ?´ë”ê°€ ì¡´ì¬?˜ì? ?ŠìŠµ?ˆë‹¤: $($target.Source)" -ForegroundColor Red
        $summaryLog += "[ERROR] $($target.Name): ?ŒìŠ¤ ?´ë” ?†ìŒ"
        continue
    }
    
    # ë°±ì—… ?€??ê²½ë¡œ
    $destination = Join-Path $BackupRoot "$($target.Name)_$timestamp"
    
    # ?œì™¸ ?¨í„´ êµ¬ì„±
    $excludeParams = @()
    foreach ($exclude in $target.Exclude) {
        $excludeParams += "/XF"
        $excludeParams += $exclude
        $excludeParams += "/XD"
        $excludeParams += $exclude
    }
    
    Write-Host "  ?ŒìŠ¤: $($target.Source)" -ForegroundColor Gray
    Write-Host "  ?€?? $destination" -ForegroundColor Gray
    
    if ($DryRun) {
        Write-Host "  [DRY RUN] ë³µì‚¬?˜ì? ?ŠìŒ" -ForegroundColor Magenta
        $summaryLog += "[SEARCH] $($target.Name): Dry Run ?„ë£Œ"
    }
    else {
        # Robocopyë¥??¬ìš©??ë°±ì—…
        $robocopyArgs = @(
            $target.Source,
            $destination,
            "/MIR",           # ë¯¸ëŸ¬ë§?(?ë³¸ê³??™ì¼?˜ê²Œ)
            "/R:3",           # ?¬ì‹œ??3??            "/W:5",           # ?€ê¸?5ì´?            "/MT:8",          # ë©€?°ìŠ¤?ˆë“œ 8ê°?            "/NP",            # ì§„í–‰ë¥??œì‹œ ????(ë¡œê·¸ ê°„ì†Œ??
            "/NFL",           # ?Œì¼ ëª©ë¡ ????            "/NDL"            # ?”ë ‰? ë¦¬ ëª©ë¡ ????        ) + $excludeParams
        
        if ($Verbose) {
            $robocopyArgs += "/V"  # ?ì„¸ ì¶œë ¥
        }
        
        $logFile = Join-Path $BackupRoot "$($target.Name)_$timestamp.log"
        $robocopyArgs += "/LOG:$logFile"
        
        Write-Host "  ë°±ì—… ì¤?.." -ForegroundColor Yellow
        & robocopy @robocopyArgs | Out-Null
        
        # Robocopy ì¢…ë£Œ ì½”ë“œ ?´ì„
        # 0-1: ?±ê³µ, 2-7: ë¶€ë¶??±ê³µ/ê²½ê³ , 8+: ?¤ë¥˜
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -le 1) {
            Write-Host "  ??ë°±ì—… ?„ë£Œ" -ForegroundColor Green
            $summaryLog += "[OK] $($target.Name): ë°±ì—… ?±ê³µ"
        }
        elseif ($exitCode -le 7) {
            Write-Host "  [WARN] ë°±ì—… ?„ë£Œ (ê²½ê³  ?ˆìŒ, ì½”ë“œ: $exitCode)" -ForegroundColor Yellow
            $summaryLog += "[WARN] $($target.Name): ë°±ì—… ?„ë£Œ (ê²½ê³ )"
        }
        else {
            Write-Host "  ??ë°±ì—… ?¤íŒ¨ (ì½”ë“œ: $exitCode)" -ForegroundColor Red
            $summaryLog += "[ERROR] $($target.Name): ë°±ì—… ?¤íŒ¨"
        }
        
        # ë°±ì—… ?¬ê¸° ?•ì¸
        if (Test-Path $destination) {
            $size = (Get-ChildItem $destination -Recurse -File | Measure-Object -Property Length -Sum).Sum
            $sizeMB = [math]::Round($size / 1MB, 2)
            Write-Host "  ?¬ê¸°: $sizeMB MB" -ForegroundColor Cyan
        }
    }
    
    Write-Host ""
}

# ?”ì•½ ë³´ê³ ??Write-Host "=== ë°±ì—… ?”ì•½ ===" -ForegroundColor Cyan
foreach ($log in $summaryLog) {
    Write-Host $log
}
Write-Host ""

# ë°±ì—… ë¡œê·¸ ?€??if (-not $DryRun) {
    $report = @"
?ë™ ë°±ì—… ë³´ê³ ???ì„± ?œê°„: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
ë°±ì—… ê²½ë¡œ: $BackupRoot

=== ë°±ì—… ?€??===
$($backupTargets | ForEach-Object { "- $($_.Name): $($_.Source)" } | Out-String)

=== ë°±ì—… ê²°ê³¼ ===
$($summaryLog | Out-String)

=== ?¤ìŒ ?¨ê³„ ===
1. ë°±ì—… ë¬´ê²°???•ì¸: ì£¼ìš” ?Œì¼???¬ë°”ë¥´ê²Œ ë³µì‚¬?˜ì—ˆ?”ì? ê²€ì¦?2. ?´ë¼?°ë“œ ?™ê¸°?? ì¤‘ìš” ë°±ì—…??Google Drive ?ëŠ” OneDrive???…ë¡œ??3. ?•ê¸° ë°±ì—… ?¤ì?ì¤? Windows ?‘ì—… ?¤ì?ì¤„ëŸ¬ë¡??ë™???¤ì •
4. ?¤ë˜??ë°±ì—… ?•ë¦¬: 30???´ìƒ ??ë°±ì—…?€ ê²€?????? œ

=== ë³µì› ë°©ë²• ===
ê°?ë°±ì—… ?´ë”ë¥??ë˜ ?„ì¹˜ë¡?ë³µì‚¬?˜ë©´ ?©ë‹ˆ??
?? robocopy "$BackupRoot\LLM_Unified_$timestamp" "C:\workspace\agi\LLM_Unified" /MIR

"@
    
    $report | Out-File -FilePath $logPath -Encoding UTF8
    Write-Host "ë°±ì—… ë¡œê·¸ ?€?? $logPath" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== ë°±ì—… ?„ë£Œ ===" -ForegroundColor Green

# ?¤ë˜??ë°±ì—… ?•ë¦¬ (? íƒ ?¬í•­)
if (-not $DryRun) {
    Write-Host ""
    Write-Host "?¤ë˜??ë°±ì—… ?•ë¦¬ ?¬ë?ë¥??•ì¸?˜ê³  ?¶ìœ¼?œë©´ -CleanOld ?¤ìœ„ì¹˜ë? ì¶”ê??˜ì„¸??" -ForegroundColor Gray
}
