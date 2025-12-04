#!/usr/bin/env pwsh
#Requires -Version 5.1
<#!
.SYNOPSIS
    Verify feedback loop heartbeat by checking unified augmented ledger freshness
.DESCRIPTION
    Reads the unified augmented ledger (JSONL) and verifies the newest event timestamp
    is within an acceptable freshness threshold. Optionally derives the threshold
    from the adaptive scheduler recommendation (2x the interval) for flexibility.
#>

param(
    # Max allowed staleness in minutes when not using adaptive recommendation
    [int]$MaxStaleMinutes = 15,

    # Path to unified augmented ledger (JSONL)
    [string]$LedgerPath = "$PSScriptRoot\..\fdo_agi_repo\memory\resonance_ledger_augmented.jsonl",

    # Optional: adaptive recommendation (JSON)
    [string]$RecommendPath = "$PSScriptRoot\..\fdo_agi_repo\outputs\adaptive_feedback_interval.json",

    # Use adaptive recommendation (2x interval) as threshold
    [switch]$UseAdaptive,

    # Also check scheduled task state
    [switch]$CheckTask,

    # Scheduled task name
    [string]$TaskName = "AGI_FeedbackLoop",

    # Optional: write result summary to JSON file
    [string]$OutJson,

    # Optional: suppress logs and print JSON only to stdout
    [switch]$JsonOnly
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    if ($JsonOnly) { return }
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
    $raw = $null
    if ($Evt.PSObject.Properties.Name -contains 'ts') { $raw = $Evt.ts }
    elseif ($Evt.PSObject.Properties.Name -contains 'timestamp') { $raw = $Evt.timestamp }
    elseif ($Evt.PSObject.Properties.Name -contains 'time') { $raw = $Evt.time }

    if ($null -eq $raw -or [string]::IsNullOrWhiteSpace([string]$raw)) {
        return $null
    }

    if ($raw -is [int] -or $raw -is [long] -or $raw -is [double]) {
        $num = [double]$raw
        if ($num -gt 9999999999) { return [datetime]([DateTimeOffset]::FromUnixTimeMilliseconds([int64]$num).UtcDateTime) }
        else { return [datetime]([DateTimeOffset]::FromUnixTimeSeconds([int64]$num).UtcDateTime) }
    }

    try { return [datetime]$raw } catch { return $null }
}

# Determine freshness threshold
$thresholdMin = $MaxStaleMinutes
$mode = "fixed"
if ($UseAdaptive -and (Test-Path -LiteralPath $RecommendPath)) {
    try {
        $rec = Get-Content -LiteralPath $RecommendPath -ErrorAction Stop | ConvertFrom-Json
        if ($rec -and $rec.interval_minutes) {
            $thresholdMin = [int]([math]::Max($MaxStaleMinutes, ($rec.interval_minutes * 2)))
            $mode = "adaptive"
            Write-Log "Adaptive threshold enabled: $thresholdMin min (2x recommended $($rec.interval_minutes))" "INFO"
        }
    }
    catch {
        Write-Log "Failed to read recommendation: $($_.Exception.Message) — using default $MaxStaleMinutes min" "WARN"
    }
}

# Check ledger existence
if (-not (Test-Path -LiteralPath $LedgerPath)) {
    Write-Log "Unified ledger not found: $LedgerPath" "ERROR"
    $result = [ordered]@{
        ok            = $false
        code          = 2
        message       = "Unified ledger not found"
        ledger_path   = $LedgerPath
        mode          = $mode
        threshold_min = $thresholdMin
    }
    $json = ($result | ConvertTo-Json -Depth 5 -Compress)
    if ($OutJson) { try { $dir = Split-Path -LiteralPath $OutJson -Parent; if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }; $json | Out-File -LiteralPath $OutJson -Encoding UTF8 -Force } catch { } }
    if ($JsonOnly) { Write-Output $json }
    exit 2
}

# Read tail and find latest valid timestamp
$lines = Get-Content -LiteralPath $LedgerPath -Tail 300 -ErrorAction SilentlyContinue
$latest = $null
foreach ($line in ($lines | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Last 300)) {
    try {
        $evt = $line | ConvertFrom-Json -ErrorAction Stop
        $t = Resolve-Timestamp $evt
        if ($t) { if (($null -eq $latest) -or ($t -gt $latest)) { $latest = $t } }
    }
    catch { }
}

if ($null -eq $latest) {
    Write-Log "Failed to find any valid timestamps in ledger tail." "ERROR"
    $result = [ordered]@{
        ok            = $false
        code          = 3
        message       = "No valid timestamps in ledger tail"
        ledger_path   = $LedgerPath
        mode          = $mode
        threshold_min = $thresholdMin
    }
    $json = ($result | ConvertTo-Json -Depth 5 -Compress)
    if ($OutJson) { try { $dir = Split-Path -LiteralPath $OutJson -Parent; if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }; $json | Out-File -LiteralPath $OutJson -Encoding UTF8 -Force } catch { } }
    if ($JsonOnly) { Write-Output $json }
    exit 3
}

$nowUtc = (Get-Date).ToUniversalTime()
$ageMin = [int]([math]::Round(($nowUtc - $latest.ToUniversalTime()).TotalMinutes))
Write-Log "Latest ledger event: $($latest.ToString('o')) (age: $ageMin min)" "INFO"

if ($ageMin -le $thresholdMin) {
    Write-Log "Heartbeat OK (<= $thresholdMin min)" "SUCCESS"
    $result = [ordered]@{
        ok            = $true
        code          = 0
        message       = "Heartbeat OK"
        age_min       = $ageMin
        threshold_min = $thresholdMin
        latest_iso    = $latest.ToString('o')
        ledger_path   = $LedgerPath
        mode          = $mode
    }
    $json = ($result | ConvertTo-Json -Depth 5 -Compress)
    if ($OutJson) { try { $dir = Split-Path -LiteralPath $OutJson -Parent; if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }; $json | Out-File -LiteralPath $OutJson -Encoding UTF8 -Force } catch { } }
    if ($JsonOnly) { Write-Output $json }
}
else {
    Write-Log "Heartbeat STALE: $ageMin min (> $thresholdMin min)" "ERROR"
    if ($CheckTask) {
        try {
            $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
            $info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction Stop
            Write-Log "Task '$TaskName' state: $($task.State), next: $($info.NextRunTime) last: $($info.LastRunTime) result: $($info.LastTaskResult)" "WARN"
        }
        catch {
            Write-Log "Task '$TaskName' not found or inaccessible." "WARN"
        }
    }
    $result = [ordered]@{
        ok            = $false
        code          = 4
        message       = "Heartbeat STALE"
        age_min       = $ageMin
        threshold_min = $thresholdMin
        latest_iso    = $latest.ToString('o')
        ledger_path   = $LedgerPath
        mode          = $mode
    }
    $json = ($result | ConvertTo-Json -Depth 5 -Compress)
    if ($OutJson) { try { $dir = Split-Path -LiteralPath $OutJson -Parent; if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }; $json | Out-File -LiteralPath $OutJson -Encoding UTF8 -Force } catch { } }
    if ($JsonOnly) { Write-Output $json }
    exit 4
}

exit 0
