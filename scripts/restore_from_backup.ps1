#Requires -Version 5.1
<#
.SYNOPSIS
    Restore system state from a previously verified backup.

.DESCRIPTION
    Provides a guided restore process that copies configuration, data, and state
    directories from a backup location back into the workspace. By default the
    script runs in dry-run mode to preview the operations. Use -Execute to
    perform the actual restore.

.PARAMETER BackupRoot
    Root directory that contains backup snapshots (folders typically timestamped).

.PARAMETER BackupName
    Specific backup folder name to restore. When omitted, the latest backup is selected.

.PARAMETER Execute
    Perform the restore (copy files). Without this switch the script only logs planned actions.

.PARAMETER Sections
    Optional list of sections to restore. Supported values: Config, Data, State, Outputs.
    When omitted, all sections are restored.

.PARAMETER Force
    Overwrite files without confirmation (only relevant when -Execute is used).

.PARAMETER ReportPath
    Path to write a restore summary report (Markdown).

.EXAMPLE
    .\scripts\restore_from_backup.ps1 -BackupName "2025-11-02_0300" -Execute

.EXAMPLE
    .\scripts\restore_from_backup.ps1 -Sections Config,Data
#>

param(
    [string]$BackupRoot = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\backups",
    [string]$BackupName,
    [switch]$Execute,
    [string[]]$Sections,
    [switch]$Force,
    [string]$ReportPath = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\restore_from_backup_report_latest.md"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::UTF8 } catch {}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
}

# ---------------------------------------------------------------------------
# Resolve backup directory
# ---------------------------------------------------------------------------
if (-not (Test-Path -LiteralPath $BackupRoot)) {
    Write-Log "Backup root not found: $BackupRoot" "ERROR"
    exit 1
}

$candidateDirs = Get-ChildItem -LiteralPath $BackupRoot -Directory | Sort-Object LastWriteTime -Descending
if (-not $candidateDirs) {
    Write-Log "No backups available in $BackupRoot" "ERROR"
    exit 1
}

$backupDir = $null
if ($BackupName) {
    $backupDir = $candidateDirs | Where-Object { $_.Name -eq $BackupName } | Select-Object -First 1
    if (-not $backupDir) {
        Write-Log "Specified backup '$BackupName' not found under $BackupRoot" "ERROR"
        exit 1
    }
}
else {
    $backupDir = $candidateDirs[0]
}

Write-Log "Selected backup: $($backupDir.Name)" "INFO"
Write-Log "Execute mode : $Execute" "INFO"

# ---------------------------------------------------------------------------
# Determine sections and mapping
# ---------------------------------------------------------------------------
$validSections = @("Config","Data","State","Outputs")
$selectedSections = if ($Sections -and $Sections.Count -gt 0) { $Sections } else { $validSections }
$selectedSections = $selectedSections | ForEach-Object { $_.Trim() } | Where-Object { $_ -in $validSections }
if (-not $selectedSections) {
    Write-Log "No valid sections selected. Supported: $($validSections -join ', ')" "ERROR"
    exit 1
}

$workspaceRoot = Split-Path -Parent $PSScriptRoot
$restorePlan = @(
    @{ Section="Config"; RelativeSource="config"; Target=Join-Path $workspaceRoot "config" },
    @{ Section="Data"; RelativeSource="fdo_agi_repo\memory"; Target=Join-Path $workspaceRoot "fdo_agi_repo\memory" },
    @{ Section="State"; RelativeSource="outputs\health_gate_state.json"; Target=Join-Path $workspaceRoot "outputs\health_gate_state.json" },
    @{ Section="Outputs"; RelativeSource="outputs"; Target=Join-Path $workspaceRoot "outputs" }
)

$actions = @()
foreach ($item in $restorePlan) {
    if ($selectedSections -contains $item.Section) {
        $sourcePath = Join-Path $backupDir.FullName $item.RelativeSource
        $targetPath = $item.Target
        $actions += [PSCustomObject]@{
            Section = $item.Section
            Source  = $sourcePath
            Target  = $targetPath
        }
    }
}

if (-not $actions) {
    Write-Log "No restore actions determined (check section mapping)." "ERROR"
    exit 1
}

# ---------------------------------------------------------------------------
# Execute or preview actions
# ---------------------------------------------------------------------------
foreach ($action in $actions) {
    Write-Log "Section: $($action.Section)" "INFO"
    Write-Log "  Source: $($action.Source)" "INFO"
    Write-Log "  Target: $($action.Target)" "INFO"

    if (-not (Test-Path -LiteralPath $action.Source)) {
        Write-Log "  Skipped: source missing." "WARN"
        continue
    }

    if (-not $Execute) {
        Write-Log "  (Dry-Run) No changes applied." "INFO"
        continue
    }

    try {
        if (Test-Path -LiteralPath $action.Target) {
            if ($Force -or (Read-Host "  Target exists. Overwrite? (y/N)") -eq "y") {
                Write-Log "  Removing existing target..." "INFO"
                Remove-Item -LiteralPath $action.Target -Recurse -Force
            }
            else {
                Write-Log "  Skipped by user." "WARN"
                continue
            }
        }
        $targetParent = Split-Path -Parent $action.Target
        if ($targetParent -and -not (Test-Path -LiteralPath $targetParent)) {
            New-Item -ItemType Directory -Force -Path $targetParent | Out-Null
        }
        if ((Get-Item -LiteralPath $action.Source).PSIsContainer) {
            Copy-Item -LiteralPath $action.Source -Destination $action.Target -Recurse -Force
        }
        else {
            Copy-Item -LiteralPath $action.Source -Destination $action.Target -Force
        }
        Write-Log "  Restored successfully." "SUCCESS"
    }
    catch {
        Write-Log "  Restore failed: $($_.Exception.Message)" "ERROR"
    }
}

# ---------------------------------------------------------------------------
# Write summary report
# ---------------------------------------------------------------------------
$report = @()
$report += "# Backup Restore Summary"
$report += ""
$report += "**Generated**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$report += "**Backup Root**: $BackupRoot"
$report += "**Backup Name**: $($backupDir.Name)"
$report += "**Executed**: $Execute"
$report += "**Sections**: $($selectedSections -join ', ')"
$report += ""
$report += "## Actions"
foreach ($action in $actions) {
    $report += "- $($action.Section): `$(source=$($action.Source))` → `$(target=$($action.Target))`"
}

try {
    $reportDir = Split-Path -Parent $ReportPath
    if ($reportDir -and -not (Test-Path -LiteralPath $reportDir)) {
        New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
    }
    [System.IO.File]::WriteAllLines($ReportPath, $report)
    Write-Log "Report written to $ReportPath" "INFO"
}
catch {
    Write-Log "Failed to write report: $($_.Exception.Message)" "ERROR"
}

Write-Log "Restore process complete." "INFO"