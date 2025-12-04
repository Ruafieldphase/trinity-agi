#Requires -Version 5.1
<##
.SYNOPSIS
    Generate hashes.json for backup snapshot directories.

.DESCRIPTION
    Scans a backup directory (or latest backup under root) and computes file hashes
    for selected sections. Intended to run during backup creation prior to verification.

.PARAMETER BackupRoot
    Root folder containing dated backup directories.

.PARAMETER BackupName
    Specific backup directory to process. If omitted, the latest is used.

.PARAMETER Sections
    Sections (relative paths) to include. Default: config, fdo_agi_repo\memory, outputs.

.PARAMETER Algorithm
    Hash algorithm (MD5, SHA256, etc.). Default: MD5.

.PARAMETER Force
    Overwrite existing hashes.json when present.

.EXAMPLE
    .\scripts\generate_backup_hashes.ps1 -BackupName 2025-11-03_0300
#>

param(
    [string]$BackupRoot = "C:\workspace\agi\backups",
    [string]$BackupName,
    [string[]]$Sections = @("config", "fdo_agi_repo\memory", "outputs"),
    [string]$Algorithm = "MD5",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::UTF8 } catch {}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
}

if (-not (Test-Path -LiteralPath $BackupRoot)) {
    Write-Log "Backup root not found: $BackupRoot" "ERROR"
    exit 1
}

$backupDirs = Get-ChildItem -LiteralPath $BackupRoot -Directory | Sort-Object LastWriteTime -Descending
if (-not $backupDirs) {
    Write-Log "No backup directories under $BackupRoot" "ERROR"
    exit 1
}

$targetDir = $null
if ($BackupName) {
    $targetDir = $backupDirs | Where-Object { $_.Name -eq $BackupName } | Select-Object -First 1
    if (-not $targetDir) {
        Write-Log "Backup '$BackupName' not found." "ERROR"
        exit 1
    }
}
else {
    $targetDir = $backupDirs[0]
}

Write-Log "Selected backup: $($targetDir.FullName)" "INFO"
$hashFile = Join-Path $targetDir.FullName "hashes.json"
if (Test-Path -LiteralPath $hashFile -and -not $Force) {
    Write-Log "hashes.json already exists. Use -Force to overwrite." "WARN"
    exit 0
}

$entries = @()
foreach ($section in $Sections) {
    $sectionPath = Join-Path $targetDir.FullName $section
    if (-not (Test-Path -LiteralPath $sectionPath)) {
        Write-Log "Section missing: $section" "WARN"
        continue
    }
    $files = Get-ChildItem -LiteralPath $sectionPath -Recurse -File
    foreach ($file in $files) {
        $relative = Resolve-Path $file.FullName -Relative -RelativeBasePath $targetDir.FullName
        $entries += [PSCustomObject]@{
            relative_path = $relative
            hash = (Get-FileHash -Path $file.FullName -Algorithm $Algorithm).Hash
            algorithm = $Algorithm
        }
    }
}

$hashDir = Split-Path -Parent $hashFile
if ($hashDir -and -not (Test-Path -LiteralPath $hashDir)) {
    New-Item -ItemType Directory -Force -Path $hashDir | Out-Null
}

$entries | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $hashFile -Encoding UTF8

Write-Log "hashes.json generated: $hashFile" "SUCCESS"
