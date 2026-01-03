#Requires -Version 5.1
<#
.SYNOPSIS
    Auto-Upgrade Detector - Git pull 후 자동으로 환경을 업데이트
.DESCRIPTION
    Git pull로 새 스크립트나 의존성이 추가되면 자동으로:
    - requirements.txt 변경 감지 → pip install
    - package.json 변경 감지 → npm install
    - 새 스크립트 감지 → 권한 설정
    - 프로세스 재시작 필요 여부 판단 → 자동 재시작
#>

param(
    [string]$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } ) = "$PSScriptRoot\..",
    [switch]$DryRun,
    [switch]$Force
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Continue"
$logFile = "$WorkspaceRoot\outputs\auto_upgrade_log.jsonl"

function Write-UpgradeLog {
    param([string]$Action, [string]$Target, [string]$Status, [string]$Details = "")
    $entry = @{
        timestamp = (Get-Date).ToString("o")
        action    = $Action
        target    = $Target
        status    = $Status
        details   = $Details
    } | ConvertTo-Json -Compress
    Add-Content -Path $logFile -Value $entry -Encoding UTF8
}

function Get-LastCommitHash {
    param([string]$RepoPath)
    try {
        Push-Location $RepoPath
        $hash = git rev-parse HEAD 2>$null
        Pop-Location
        return $hash
    }
    catch {
        Pop-Location
        return $null
    }
}

function Get-ChangedFiles {
    param([string]$RepoPath, [string]$OldHash, [string]$NewHash)
    try {
        Push-Location $RepoPath
        $files = git diff --name-only "$OldHash" "$NewHash" 2>$null
        Pop-Location
        return $files
    }
    catch {
        Pop-Location
        return @()
    }
}

Write-Host "`n=== Auto-Upgrade Detector ===" -ForegroundColor Cyan

# Read last known commit
$stateFile = "$WorkspaceRoot\outputs\last_known_commit.txt"
$oldHash = if (Test-Path $stateFile) { Get-Content $stateFile -Raw | ForEach-Object { $_.Trim() } } else { $null }
$newHash = Get-LastCommitHash -RepoPath $WorkspaceRoot

if (-not $newHash) {
    Write-Host "✗ Not a git repository or git not available" -ForegroundColor Red
    exit 1
}

if ($oldHash -eq $newHash -and -not $Force) {
    Write-Host "✓ No changes detected (same commit: $newHash)" -ForegroundColor Green
    exit 0
}

Write-Host "Commit changed: $oldHash → $newHash" -ForegroundColor Yellow

# Get changed files
$changedFiles = Get-ChangedFiles -RepoPath $WorkspaceRoot -OldHash $oldHash -NewHash $newHash
if (-not $changedFiles) {
    Write-Host "  No file changes detected" -ForegroundColor Gray
    $changedFiles = @()
}

Write-Host "`nChanged files: $($changedFiles.Count)" -ForegroundColor Cyan

# Check for requirements.txt changes
$reqChanged = $changedFiles | Where-Object { $_ -like "*requirements.txt" }
if ($reqChanged) {
    Write-Host "`n[1] Python requirements changed" -ForegroundColor Yellow
    if (-not $DryRun) {
        foreach ($req in $reqChanged) {
            $reqPath = Join-Path $WorkspaceRoot $req
            $venvDir = Split-Path -Parent $reqPath
            $venvPython = Join-Path $venvDir ".venv\Scripts\python.exe"
            
            if (Test-Path $venvPython) {
                Write-Host "  Installing: $req" -ForegroundColor Cyan
                & $venvPython -m pip install -r $reqPath --quiet --disable-pip-version-check
                Write-UpgradeLog -Action "upgrade" -Target $req -Status "success"
            }
        }
    }
    else {
        Write-Host "  [DRY-RUN] Would install Python packages" -ForegroundColor Gray
    }
}

# Check for package.json changes
$pkgChanged = $changedFiles | Where-Object { $_ -like "*package.json" }
if ($pkgChanged) {
    Write-Host "`n[2] Node.js packages changed" -ForegroundColor Yellow
    if (-not $DryRun) {
        foreach ($pkg in $pkgChanged) {
            $pkgDir = Split-Path -Parent (Join-Path $WorkspaceRoot $pkg)
            Write-Host "  Installing: $pkg" -ForegroundColor Cyan
            Push-Location $pkgDir
            npm install --silent
            Pop-Location
            Write-UpgradeLog -Action "upgrade" -Target $pkg -Status "success"
        }
    }
    else {
        Write-Host "  [DRY-RUN] Would run npm install" -ForegroundColor Gray
    }
}

# Check for new .ps1 scripts
$newScripts = $changedFiles | Where-Object { $_ -like "*.ps1" -and $_ -like "scripts/*" }
if ($newScripts) {
    Write-Host "`n[3] New PowerShell scripts detected: $($newScripts.Count)" -ForegroundColor Yellow
    foreach ($script in $newScripts) {
        Write-Host "  New: $script" -ForegroundColor Cyan
    }
    Write-UpgradeLog -Action "detect" -Target "new_scripts" -Status "found" -Details "$($newScripts.Count) scripts"
}

# Decide if restart needed
$restartNeeded = $reqChanged -or $pkgChanged
if ($restartNeeded) {
    Write-Host "`n[4] Process restart recommended" -ForegroundColor Yellow
    if (-not $DryRun) {
        Write-Host "  Restarting Master Orchestrator..." -ForegroundColor Cyan
        & "$WorkspaceRoot\scripts\master_orchestrator.ps1" -Force
        Write-UpgradeLog -Action "restart" -Target "master_orchestrator" -Status "success"
    }
    else {
        Write-Host "  [DRY-RUN] Would restart processes" -ForegroundColor Gray
    }
}

# Update state file
if (-not $DryRun) {
    Set-Content -Path $stateFile -Value $newHash -Encoding UTF8
    Write-Host "`n✓ State updated: $newHash" -ForegroundColor Green
}

Write-Host "`n=== Auto-Upgrade Complete ===`n" -ForegroundColor Cyan
exit 0