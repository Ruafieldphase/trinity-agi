param(
    [string]$FilePath = "C:\workspace\agi\outputs\status_snapshots.jsonl",
    [int]$MaxLines = 50000,
    [int]$MaxSizeMB = 50,
    [string]$ArchiveDir = "C:\workspace\agi\outputs\archive",
    [int]$RetentionDays = 30,
    [switch]$Zip,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO] $msg" }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

if (-not (Test-Path $FilePath)) {
    Write-Info "Snapshot file not found: $FilePath (nothing to rotate)"
    # Cleanup can still run even if current file is missing
}

# Compute current size if file exists
$sizeMB = 0
if (Test-Path $FilePath) {
    $fi = Get-Item -LiteralPath $FilePath
    $sizeMB = [math]::Round($fi.Length / 1MB, 2)
}

# Efficient line count
$lineCount = 0
if (Test-Path $FilePath) {
    try {
        $lineCount = [System.IO.File]::ReadLines($FilePath).Count
    }
    catch {
        Write-Warn "Failed to count lines via ReadLines(); falling back to Measure-Object (may use more memory)"
        $lineCount = (Get-Content -LiteralPath $FilePath -ReadCount 0 | Measure-Object -Line).Lines
    }
}

if (Test-Path $FilePath) {
    Write-Info "Current: $lineCount lines, $sizeMB MB"
}

$needsRotate = $false
if (Test-Path $FilePath) {
    if ($lineCount -gt $MaxLines) { $needsRotate = $true }
    if ($sizeMB -gt $MaxSizeMB) { $needsRotate = $true }
}

$baseName = [System.IO.Path]::GetFileNameWithoutExtension($FilePath)

if (-not $needsRotate) {
    Write-Info "No rotation needed (thresholds: MaxLines=$MaxLines, MaxSizeMB=$MaxSizeMB)"
    # Cleanup old archives if configured
    if ($RetentionDays -gt 0 -and (Test-Path $ArchiveDir)) {
        $cutoff = (Get-Date).AddDays(-$RetentionDays)
        $pattern1 = "$baseName-*.jsonl"
        $pattern2 = "$baseName-*.jsonl.zip"
        $candidates = @()
        $candidates += Get-ChildItem -Path $ArchiveDir -Filter $pattern1 -ErrorAction SilentlyContinue
        $candidates += Get-ChildItem -Path $ArchiveDir -Filter $pattern2 -ErrorAction SilentlyContinue
        $toDelete = $candidates | Where-Object { $_.LastWriteTime -lt $cutoff }
        if ($toDelete -and $toDelete.Count -gt 0) {
            Write-Info ("Cleaning {0} archived file(s) older than {1} days" -f $toDelete.Count, $RetentionDays)
            foreach ($f in $toDelete) {
                if ($DryRun) {
                    Write-Info "[DryRun] Would remove: $($f.FullName)"
                }
                else {
                    Remove-Item -LiteralPath $f.FullName -Force -ErrorAction SilentlyContinue
                }
            }
        }
    }
    exit 0
}

if (-not (Test-Path $ArchiveDir)) {
    New-Item -Path $ArchiveDir -ItemType Directory -Force | Out-Null
}

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$archivedPath = Join-Path $ArchiveDir "$baseName-$timestamp.jsonl"

Write-Info "Rotating: moving '$FilePath' -> '$archivedPath'"

if ($DryRun) {
    Write-Info "[DryRun] Would move and optionally zip, then create new empty file"
    exit 0
}

# Move current file
Move-Item -LiteralPath $FilePath -Destination $archivedPath -Force

if ($Zip) {
    $zipPath = "$archivedPath.zip"
    Write-Info "Compressing to: $zipPath"
    Compress-Archive -Path $archivedPath -DestinationPath $zipPath -Force
    Remove-Item -LiteralPath $archivedPath -Force
}

# Create new empty file
New-Item -Path $FilePath -ItemType File -Force | Out-Null
Write-Info "Rotation complete. New file created: $FilePath"

# Cleanup old archives by retention
if ($RetentionDays -gt 0) {
    $cutoff = (Get-Date).AddDays(-$RetentionDays)
    $pattern1 = "$baseName-*.jsonl"
    $pattern2 = "$baseName-*.jsonl.zip"
    $candidates = @()
    $candidates += Get-ChildItem -Path $ArchiveDir -Filter $pattern1 -ErrorAction SilentlyContinue
    $candidates += Get-ChildItem -Path $ArchiveDir -Filter $pattern2 -ErrorAction SilentlyContinue
    $toDelete = $candidates | Where-Object { $_.LastWriteTime -lt $cutoff }
    if ($toDelete -and $toDelete.Count -gt 0) {
        Write-Info ("Cleaning {0} archived file(s) older than {1} days" -f $toDelete.Count, $RetentionDays)
        foreach ($f in $toDelete) {
            if ($DryRun) {
                Write-Info "[DryRun] Would remove: $($f.FullName)"
            }
            else {
                Remove-Item -LiteralPath $f.FullName -Force -ErrorAction SilentlyContinue
            }
        }
    }
}
