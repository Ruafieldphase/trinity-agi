#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Merge multiple augmented ledger files into a unified ledger
.DESCRIPTION
    Consolidates YouTube, RPA, and other augmented ledger sources into
    a single canonical augmented ledger with deduplication and sorting.
#>

param(
    # Unified output JSONL path
    [Alias('OutFile')]
    [string]$OutputPath = "$PSScriptRoot\..\fdo_agi_repo\memory\resonance_ledger_augmented.jsonl",

    # Optional override for summary JSON path
    [string]$SummaryPath = "$PSScriptRoot\..\outputs\augmented_ledger_merge_summary.json",

    # Input paths (defaults to youtube+rpa augmented ledgers)
    [string[]]$InputPaths = @(
        "$PSScriptRoot\..\fdo_agi_repo\outputs\resonance_ledger_youtube_augmented.jsonl",
        "$PSScriptRoot\..\fdo_agi_repo\outputs\resonance_ledger_rpa_augmented.jsonl"
    ),

    # Dry-run prints what would happen without writing files
    [switch]$DryRun,

    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "WARN" { "Yellow" }
        "SUCCESS" { "Green" }
        default { "Cyan" }
    }
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
}

function Resolve-Timestamp {
    param([object]$Evt)
    # Try common fields: ts, timestamp, time
    $raw = $null
    if ($Evt.PSObject.Properties.Name -contains 'ts') { $raw = $Evt.ts }
    elseif ($Evt.PSObject.Properties.Name -contains 'timestamp') { $raw = $Evt.timestamp }
    elseif ($Evt.PSObject.Properties.Name -contains 'time') { $raw = $Evt.time }

    if ($null -eq $raw -or [string]::IsNullOrWhiteSpace([string]$raw)) {
        return [datetime]'1970-01-01T00:00:00Z'
    }

    # If numeric, assume Unix epoch seconds or ms
    if ($raw -is [int] -or $raw -is [long] -or $raw -is [double]) {
        $num = [double]$raw
        if ($num -gt 9999999999) {
            # milliseconds
            return [datetime]([DateTimeOffset]::FromUnixTimeMilliseconds([int64]$num).UtcDateTime)
        }
        else {
            return [datetime]([DateTimeOffset]::FromUnixTimeSeconds([int64]$num).UtcDateTime)
        }
    }

    # Fallback try parse
    try { return [datetime]$raw } catch { return [datetime]'1970-01-01T00:00:00Z' }
}

# Source files to merge
$sources = $InputPaths

Write-Log "Starting augmented ledger merge..." "INFO"

# Collect all events
$allEvents = @()
$stats = @{
    youtube    = 0
    rpa        = 0
    duplicates = 0
    total      = 0
}

foreach ($source in $sources) {
    if (-not (Test-Path $source)) {
        Write-Log "Source not found: $source (skipping)" "WARN"
        continue
    }
    
    $sourceType = if ($source -like "*youtube*") { "youtube" } elseif ($source -like "*rpa*") { "rpa" } else { "other" }
    if (-not $stats.ContainsKey($sourceType)) { $stats[$sourceType] = 0 }
    Write-Log "Reading $sourceType events from: $source" "INFO"
    
    $lines = Get-Content $source -ErrorAction SilentlyContinue
    foreach ($line in $lines) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        
        try {
            $evt = $line | ConvertFrom-Json
            if ($null -ne $evt) {
                $allEvents += $evt
                $stats[$sourceType]++
            }
            else {
                Write-Log "Parsed null event, skipping: $line" "WARN"
            }
        }
        catch {
            Write-Log "Failed to parse line (skipped)" "WARN"
        }
    }
}

$stats.total = $allEvents.Count
Write-Log "Collected $($stats.total) total events (YouTube: $($stats.youtube), RPA: $($stats.rpa))" "INFO"

if ($stats.total -eq 0) {
    Write-Log "No events to merge. Exiting." "WARN"
    exit 0
}

# Deduplicate by timestamp + event + source (robust field fallback)
$seen = @{}
$unique = @()

foreach ($evt in $allEvents) {
    $tsField = if ($evt.PSObject.Properties.Name -contains 'ts') { $evt.ts } elseif ($evt.PSObject.Properties.Name -contains 'timestamp') { $evt.timestamp } elseif ($evt.PSObject.Properties.Name -contains 'time') { $evt.time } else { '' }
    $eventField = if ($evt.PSObject.Properties.Name -contains 'event') { $evt.event } elseif ($evt.PSObject.Properties.Name -contains 'event_type') { $evt.event_type } elseif ($evt.PSObject.Properties.Name -contains 'type') { $evt.type } else { '' }
    $sourceField = if ($evt.PSObject.Properties.Name -contains 'source') { $evt.source } elseif ($evt.PSObject.Properties.Name -contains 'src') { $evt.src } else { '' }
    $rawKey = "${tsField}_${eventField}_${sourceField}"
    if ([string]::IsNullOrWhiteSpace($rawKey)) {
        # Fallback to hashing full JSON
        $rawKey = [System.BitConverter]::ToString((New-Object -TypeName System.Security.Cryptography.SHA1Managed).ComputeHash([System.Text.Encoding]::UTF8.GetBytes(($evt | ConvertTo-Json -Compress -Depth 10))))
    }
    $key = $rawKey
    if (-not $seen.ContainsKey($key)) {
        $seen[$key] = $true
        $unique += $evt
    }
    else {
        $stats.duplicates++
    }
}

Write-Log "Removed $($stats.duplicates) duplicate events" "INFO"

# Sort by resolved timestamp
$sorted = $unique | Sort-Object { Resolve-Timestamp $_ }
Write-Log "Sorted $($sorted.Count) unique events by timestamp" "INFO"

# Ensure output directory exists
$outDir = Split-Path $OutputPath -Parent
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

if ($DryRun) {
    Write-Log "DRY RUN: Would write unified ledger to: $OutputPath" "WARN"
}
else {
    # Write unified ledger
    $sorted | ForEach-Object { 
        $_ | ConvertTo-Json -Compress -Depth 10
    } | Set-Content $OutputPath -Encoding UTF8
}

if ($DryRun) {
    Write-Log "DRY RUN: Skipped writing unified ledger" "SUCCESS"
}
else {
    Write-Log "Merged ledger written to: $OutputPath" "SUCCESS"
}
Write-Log "Final stats: $($sorted.Count) events ($($stats.youtube) YouTube, $($stats.rpa) RPA, $($stats.duplicates) removed)" "SUCCESS"

# Create summary JSON
$summary = @{
    merged_at          = (Get-Date -Format "o")
    total_events       = $sorted.Count
    sources            = @{
        youtube = $stats.youtube
        rpa     = $stats.rpa
    }
    duplicates_removed = $stats.duplicates
    output_path        = $OutputPath
}

if ($DryRun) {
    Write-Log "DRY RUN: Would write summary to: $SummaryPath" "WARN"
}
else {
    # Ensure summary directory exists
    $sumDir = Split-Path $SummaryPath -Parent
    if (-not (Test-Path $sumDir)) { New-Item -ItemType Directory -Path $sumDir -Force | Out-Null }
    $summary | ConvertTo-Json -Depth 5 | Set-Content $SummaryPath -Encoding UTF8
    Write-Log "Summary saved to: $SummaryPath" "INFO"
}

exit 0
