param(
    [int]$ReportHours = 24,
    [int]$ArchiveKeepDays = 14,
    [switch]$NoZip,
    [switch]$Silent
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { if (-not $Silent) { Write-Host "[INFO] $msg" } }
function Write-Warn($msg) { if (-not $Silent) { Write-Host "[WARN] $msg" -ForegroundColor Yellow } }
function Write-Err($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

$root = "C:\workspace\agi"
$rotate = Join-Path $root 'scripts/rotate_status_snapshots.ps1'
$report = Join-Path $root 'scripts/generate_monitoring_report.ps1'
$cleanup = Join-Path $root 'scripts/cleanup_snapshot_archives.ps1'

# Ensure outputs and archive directories exist to avoid downstream errors
$outputs = Join-Path $root 'outputs'
$archiveDir = Join-Path $outputs 'archive'
if (-not (Test-Path $outputs)) { New-Item -ItemType Directory -Path $outputs -Force | Out-Null }
if (-not (Test-Path $archiveDir)) { New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null }

if (-not (Test-Path $rotate)) { Write-Err "Rotate script not found: $rotate"; exit 1 }
if (-not (Test-Path $report)) { Write-Err "Report script not found: $report"; exit 1 }
if (-not (Test-Path $cleanup)) { Write-Err "Cleanup script not found: $cleanup"; exit 1 }

# 1) Rotate (zip by default)
Write-Info "Step 1/3: Rotate snapshots"
$rotateArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $rotate)
if (-not $NoZip) { $rotateArgs += '-Zip' }
$rotateProc = Start-Process powershell -ArgumentList $rotateArgs -Wait -PassThru
if ($rotateProc.ExitCode -ne 0) { Write-Err "Rotate step failed with exit code $($rotateProc.ExitCode)"; exit $rotateProc.ExitCode }

# 2) Generate 24h report
Write-Info "Step 2/3: Generate report (${ReportHours}h)"
$reportArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $report, '-Hours', $ReportHours)
$reportProc = Start-Process powershell -ArgumentList $reportArgs -Wait -PassThru
if ($reportProc.ExitCode -ne 0) { Write-Err "Report step failed with exit code $($reportProc.ExitCode)"; exit $reportProc.ExitCode }

# 3) Cleanup archives
Write-Info "Step 3/3: Cleanup archives (keep $ArchiveKeepDays days)"
$cleanupArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $cleanup, '-KeepDays', $ArchiveKeepDays)
$cleanupProc = Start-Process powershell -ArgumentList $cleanupArgs -Wait -PassThru
if ($cleanupProc.ExitCode -ne 0) { Write-Err "Cleanup step failed with exit code $($cleanupProc.ExitCode)"; exit $cleanupProc.ExitCode }

Write-Info "Daily monitoring maintenance completed successfully."
