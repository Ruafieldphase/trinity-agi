param(
    [string]$ArchiveDir = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\archive",
    [int]$KeepDays = 14,
    [switch]$DryRun
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO] $msg" }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

if (-not (Test-Path $ArchiveDir)) {
    Write-Info "Archive dir not found: $ArchiveDir (nothing to cleanup)"
    exit 0
}

$cutoff = (Get-Date).AddDays(-$KeepDays)
Write-Info "Cleaning files older than $KeepDays days (before $($cutoff.ToString('yyyy-MM-dd HH:mm:ss'))) in: $ArchiveDir"

$files = Get-ChildItem -LiteralPath $ArchiveDir -File -ErrorAction Stop | Where-Object { $_.LastWriteTime -lt $cutoff }

if (-not $files) {
    Write-Info "No files eligible for deletion."
    exit 0
}

foreach ($f in $files) {
    if ($DryRun) {
        Write-Info "[DryRun] Would remove: $($f.FullName) (LastWriteTime=$($f.LastWriteTime))"
    }
    else {
        try {
            Remove-Item -LiteralPath $f.FullName -Force
            Write-Info "Removed: $($f.FullName)"
        }
        catch {
            Write-Warn "Failed to remove: $($f.FullName) - $($_.Exception.Message)"
        }
    }
}