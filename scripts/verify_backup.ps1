#!/usr/bin/env pwsh
<##
.SYNOPSIS
    Verify backup integrity and produce a report.
#>

param(
    [string]$BackupRoot = "C:\workspace\agi\backups",
    [string]$OutReport = "C:\workspace\agi\outputs\backup_verification_report_latest.md",
    [string]$HashAlgorithm = "MD5",
    [int]$MaxEntries = 5,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::UTF8 } catch {}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
}

Write-Log "=== Backup Verification ==="
Write-Log "Backup root : $BackupRoot"
Write-Log "Report path : $OutReport"
Write-Log "Algorithm   : $HashAlgorithm"
Write-Log "Dry run     : $DryRun"

if (-not (Test-Path -LiteralPath $BackupRoot)) {
    Write-Log "Backup root not found" "ERROR"
    exit 1
}

$buildReport = @()
$buildReport += "# Backup Verification Report"
$buildReport += ""
$buildReport += "**Generated**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$buildReport += "**Backup Root**: $BackupRoot"
$buildReport += "**Dry Run**: $DryRun"
$buildReport += ""

$backupDirs = Get-ChildItem -LiteralPath $BackupRoot -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First $MaxEntries
if (-not $backupDirs) {
    Write-Log "No backup directories found" "WARN"
    $buildReport += "No backups found."
}
else {
    foreach ($dir in $backupDirs) {
        Write-Log "Verifying backup: $($dir.FullName)" "INFO"
        $buildReport += "## Backup: $($dir.Name)"
        $buildReport += "- Path: $($dir.FullName)"
        $buildReport += "- Last Modified: $($dir.LastWriteTime)"

        $hashFile = Join-Path $dir.FullName "hashes.json"
        if (Test-Path -LiteralPath $hashFile) {
            try {
                $hashes = Get-Content -LiteralPath $hashFile -Raw | ConvertFrom-Json
            }
            catch {
                Write-Log "Failed to parse hashes.json" "ERROR"
                $buildReport += "- Result: Failed to parse hashes.json"
                continue
            }
        }
        else {
            Write-Log "hashes.json missing" "WARN"
            $buildReport += "- Result: hashes.json missing"
            continue
        }

        $results = @()
        foreach ($entry in $hashes) {
            $relative = $entry.relative_path
            $expected = $entry.hash
            $filePath = Join-Path $dir.FullName $relative
            if (-not (Test-Path -LiteralPath $filePath)) {
                Write-Log "Missing file: $relative" "ERROR"
                $results += "  - ❌ Missing file: $relative"
                continue
            }
            if ($DryRun) {
                $results += "  - (DryRun) Skipped hash check: $relative"
                continue
            }
            try {
                $actualHash = Get-FileHash -Path $filePath -Algorithm $HashAlgorithm
                if ($actualHash.Hash -eq $expected) {
                    $results += "  - ✅ $relative"
                }
                else {
                    $results += "  - ❌ Hash mismatch: $relative"
                }
            }
            catch {
                $results += "  - ❌ Hash error: $relative ($_ )"
            }
        }

        if (-not $results) {
            $results += "  - (No entries in hashes.json)"
        }

        $buildReport += "- Verification:"
        $buildReport += $results
        $buildReport += ""
    }
}

try {
    $reportDir = Split-Path -Parent $OutReport
    if ($reportDir -and -not (Test-Path -LiteralPath $reportDir)) {
        New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
    }
    [System.IO.File]::WriteAllLines($OutReport, $buildReport)
    Write-Log "Report written to $OutReport"
}
catch {
    Write-Log "Failed to write report: $($_.Exception.Message)" "ERROR"
    exit 1
}

Write-Log "Backup verification complete" "INFO"
