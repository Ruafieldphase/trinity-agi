param(
    [int]$IntervalSeconds = 30,
    [int]$DurationMinutes = 10,
    [int]$WarnMs = 1200,
    [int]$AlertMs = 3500,
    [switch]$SlackOnFailure,
    [switch]$FailOnDegraded,
    [int]$KeepDays = 1,
    [string]$OutDir = "${PSScriptRoot}\..\outputs"
)

# ASCII-safe console lines for PS 5.1
function Write-Line {
    param([string]$Text)
    Write-Host $Text
}

$ErrorActionPreference = 'Stop'

# Resolve paths
$script:DashboardPath = Join-Path $PSScriptRoot 'lumen_dashboard.ps1'
if (-not (Test-Path $script:DashboardPath)) {
    Write-Line "ERROR: lumen_dashboard.ps1 not found at $script:DashboardPath"
    exit 1
}

if (-not (Test-Path $OutDir)) {
    New-Item -Path $OutDir -ItemType Directory -Force | Out-Null
}

# Timing
$start = Get-Date
$deadline = $start.AddMinutes($DurationMinutes)

Write-Line "Starting dashboard snapshot loop..."
Write-Line ("IntervalSeconds={0} DurationMinutes={1} WarnMs={2} AlertMs={3} KeepDays={4} OutDir={5}" -f $IntervalSeconds, $DurationMinutes, $WarnMs, $AlertMs, $KeepDays, (Resolve-Path $OutDir))

if ($DurationMinutes -le 0) {
    # Single-shot mode when duration is zero or negative
    $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
    $outFile = Join-Path $OutDir ("lumen_dashboard_{0}.json" -f $ts)

    # Build named parameter splat for reliability on PS 5.1
    $paramSplat = @{ WarnMs = $WarnMs; AlertMs = $AlertMs; OutJson = $outFile }
    if ($SlackOnFailure) { $paramSplat.SlackOnFailure = $true }
    if ($FailOnDegraded) { $paramSplat.FailOnDegraded = $true }

    $exitCode = 0
    try {
        # Invoke the dashboard script in-process with named splatting
        & $script:DashboardPath @paramSplat
        $exitCode = $LASTEXITCODE
    }
    catch {
        $exitCode = 1
        Write-Line ("ERROR: Dashboard run failed: {0}" -f $_.Exception.Message)
    }

    if (Test-Path $outFile) {
        Write-Line ("Saved snapshot: {0} (exit={1})" -f $outFile, $exitCode)
    }
    else {
        Write-Line ("WARN: Snapshot not created (exit={0})" -f $exitCode)
    }

}
else {
    while ([DateTime]::UtcNow -lt $deadline.ToUniversalTime()) {
        $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
        $outFile = Join-Path $OutDir ("lumen_dashboard_{0}.json" -f $ts)

        # Build named parameter splat for reliability on PS 5.1
        $paramSplat = @{ WarnMs = $WarnMs; AlertMs = $AlertMs; OutJson = $outFile }
        if ($SlackOnFailure) { $paramSplat.SlackOnFailure = $true }
        if ($FailOnDegraded) { $paramSplat.FailOnDegraded = $true }

        $exitCode = 0
        try {
            & $script:DashboardPath @paramSplat
            $exitCode = $LASTEXITCODE
        }
        catch {
            $exitCode = 1
            Write-Line ("ERROR: Dashboard run failed: {0}" -f $_.Exception.Message)
        }

        if (Test-Path $outFile) {
            Write-Line ("Saved snapshot: {0} (exit={1})" -f $outFile, $exitCode)
        }
        else {
            Write-Line ("WARN: Snapshot not created (exit={0})" -f $exitCode)
        }

        Start-Sleep -Seconds $IntervalSeconds
    }
}

# Retention: delete old snapshots older than KeepDays
try {
    $cutoff = (Get-Date).AddDays(-$KeepDays)
    Get-ChildItem -Path $OutDir -Filter 'lumen_dashboard_*.json' -File -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt $cutoff } |
    ForEach-Object {
        Write-Line ("Prune old snapshot: {0}" -f $_.FullName)
        Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue
    }
}
catch {
    Write-Line ("WARN: Retention cleanup failed: {0}" -f $_.Exception.Message)
}

Write-Line "Completed snapshot loop."
