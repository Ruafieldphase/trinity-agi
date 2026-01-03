#Requires -Version 5.1
param(
    [switch]$Enable,
    [switch]$Disable,
    [switch]$Status
)

<#
.SYNOPSIS
  Toggle Focus Mode to minimize CPU/RAM spikes during intense sessions (LLM + Copilot).

.DESCRIPTION
  -Enable: Enters Rhythm Safe Mode, enforces single worker, and applies low-load VS Code settings
           (disables Copilot inline suggestions and limits diagnostics to open files only).
           Backs up .vscode/settings.json to settings.focus_backup.json once.
  -Disable: Restores settings from backup (if present) and exits Safe Mode.
  -Status:  Prints current relevant settings and Safe Mode hints.

.NOTES
  Idempotent and workspace-local. Does not require admin.
#>

$ErrorActionPreference = 'Continue'

function Write-Info($msg) { Write-Host "[Focus] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "[OK]    $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[ERR]   $msg" -ForegroundColor Red }

if (-not $Enable -and -not $Disable -and -not $Status) { $Enable = $true }
if (($Enable -and $Disable) -or ($Enable -and $Status) -or ($Disable -and $Status)) {
    Write-Err "Use only one of -Enable, -Disable, or -Status."
    exit 1
}

$root = Split-Path -Parent $PSScriptRoot
$scripts = Join-Path $root 'scripts'
$vscodeDir = Join-Path $root '.vscode'
$settingsPath = Join-Path $vscodeDir 'settings.json'
$backupPath = Join-Path $vscodeDir 'settings.focus_backup.json'

function Read-Settings {
    if (-not (Test-Path -LiteralPath $settingsPath)) {
        New-Item -ItemType Directory -Path $vscodeDir -ErrorAction SilentlyContinue | Out-Null
        '{}' | Out-File -FilePath $settingsPath -Encoding utf8 -Force
    }
    try {
        $raw = Get-Content -LiteralPath $settingsPath -Raw -Encoding UTF8
        if ([string]::IsNullOrWhiteSpace($raw)) { $raw = '{}' }
        return $raw | ConvertFrom-Json
    }
    catch {
        Write-Warn "settings.json is not valid JSON; creating a minimal replacement. Backup will be created as-is."
        if (-not (Test-Path -LiteralPath $backupPath)) {
            Copy-Item -LiteralPath $settingsPath -Destination $backupPath -Force -ErrorAction SilentlyContinue
        }
        '{}' | Out-File -FilePath $settingsPath -Encoding utf8 -Force
        return '{}' | ConvertFrom-Json
    }
}

function Save-Settings($obj) {
    try {
        $json = $obj | ConvertTo-Json -Depth 20
        $json | Out-File -FilePath $settingsPath -Encoding utf8 -Force
        return $true
    }
    catch {
        Write-Err "Failed to save settings.json: $($_.Exception.Message)"
        return $false
    }
}

function Ensure-Backup {
    if (-not (Test-Path -LiteralPath $backupPath)) {
        try {
            Copy-Item -LiteralPath $settingsPath -Destination $backupPath -Force
            Write-Ok "Created backup: .vscode/settings.focus_backup.json"
        }
        catch { Write-Warn "Could not create backup: $($_.Exception.Message)" }
    }
}

function Restore-Backup {
    if (Test-Path -LiteralPath $backupPath) {
        try {
            Copy-Item -LiteralPath $backupPath -Destination $settingsPath -Force
            Write-Ok "Restored VS Code settings from backup"
        }
        catch { Write-Warn "Failed to restore backup: $($_.Exception.Message)" }
    }
    else {
        Write-Warn "Backup not found; leaving current settings as-is"
    }
}

function Apply-LowLoadSettings {
    $s = Read-Settings
    # GitHub Copilot: disable for code languages, allow in markdown/git-commit/plaintext only
    $copEn = [pscustomobject]@{
        '*'         = $false
        markdown    = $true
        'git-commit'= $true
        plaintext   = $true
    }
    $s | Add-Member -NotePropertyName 'github.copilot.enable' -NotePropertyValue $copEn -Force
    $s | Add-Member -NotePropertyName 'github.copilot.inlineSuggest.enable' -NotePropertyValue $false -Force
    $s | Add-Member -NotePropertyName 'editor.inlineSuggest.enabled' -NotePropertyValue $false -Force

    # Pylance diagnostics only for open files to reduce background analysis
    $s | Add-Member -NotePropertyName 'python.analysis.diagnosticMode' -NotePropertyValue 'openFilesOnly' -Force

    # Limit editors per group to avoid too many open buffers
    $s | Add-Member -NotePropertyName 'workbench.editor.limit.enabled' -NotePropertyValue $true -Force
    $s | Add-Member -NotePropertyName 'workbench.editor.limit.perEditorGroup' -NotePropertyValue 6 -Force

    # Ensure watcher excludes (idempotent; many already present in repo)
    if (-not $s.'files.watcherExclude') { $s | Add-Member -NotePropertyName 'files.watcherExclude' -NotePropertyValue (@{}) -Force }
    $w = $s.'files.watcherExclude'
    $w.'**/.venv/**' = $true
    $w.'**/node_modules/**' = $true
    $w.'outputs/**' = $true
    $w.'**/*.jsonl' = $true
    $w.'**/__pycache__/**' = $true

    if (Save-Settings $s) { Write-Ok "Applied low-load VS Code settings" }
}

function Enter-SafeMode {
    $safe = Join-Path $scripts 'rhythm_safe_mode.ps1'
    if (Test-Path -LiteralPath $safe) {
        try { & $safe -Enable | Out-Null; Write-Ok "Rhythm Safe Mode enabled" } catch { Write-Warn $_ }
    }
    else {
        Write-Warn "rhythm_safe_mode.ps1 not found"
    }

    # Enforce single worker if available (safe)
    $ensureWorker = Join-Path $scripts 'ensure_rpa_worker.ps1'
    if (Test-Path -LiteralPath $ensureWorker) {
        try { & $ensureWorker -EnforceSingle -MaxWorkers 1 | Out-Null; Write-Ok "Queue worker limited to 1" } catch { Write-Warn $_ }
    }
}

function Exit-SafeMode {
    $safe = Join-Path $scripts 'rhythm_safe_mode.ps1'
    if (Test-Path -LiteralPath $safe) {
        try { & $safe -Disable | Out-Null; Write-Ok "Safe Mode exit requested" } catch { Write-Warn $_ }
    }
}

function Show-Status {
    Write-Info "Reading VS Code settings..."
    $s = Read-Settings
    $cop = $s.PSObject.Properties['github.copilot.enable']
    $inline = $s.PSObject.Properties['github.copilot.inlineSuggest.enable']
    $diag = $s.PSObject.Properties['python.analysis.diagnosticMode']
    $limEn = $s.PSObject.Properties['workbench.editor.limit.enabled']
    $limPer = $s.PSObject.Properties['workbench.editor.limit.perEditorGroup']

    $status = [ordered]@{
        settings_path = $settingsPath
        backup_exists = (Test-Path -LiteralPath $backupPath)
        copilot_enable = if ($cop) { $cop.Value } else { $null }
        copilot_inlineSuggest = if ($inline) { $inline.Value } else { $null }
        pylance_diagnosticMode = if ($diag) { $diag.Value } else { $null }
        editor_limit_enabled = if ($limEn) { $limEn.Value } else { $null }
        editor_limit_perGroup = if ($limPer) { $limPer.Value } else { $null }
        hints = @(
            "Run scripts/pre_reboot_safety_check.ps1 before heavy work",
            "Use scripts/autonomous_goal_executor.py --dry-run to stage work",
            "Prefer one assistant active at a time during focus"
        )
    }
    $status | ConvertTo-Json -Depth 6 | Write-Output
}

if ($Enable) {
    Write-Info "Enabling Focus Mode..."
    Ensure-Backup
    Apply-LowLoadSettings
    Enter-SafeMode
    Show-Status | Out-Null
    exit 0
}
elseif ($Disable) {
    Write-Info "Disabling Focus Mode..."
    Restore-Backup
    Exit-SafeMode
    Show-Status | Out-Null
    exit 0
}
elseif ($Status) {
    Show-Status
    exit 0
}
