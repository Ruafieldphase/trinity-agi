#Requires -Version 5.1
<#
.SYNOPSIS
    AGI Dream Mode - Constraint-free pattern exploration during sleep.

.DESCRIPTION
    Implements information-theoretic sleep for AGI:
    - Load recent patterns from Ledger
    - Randomly recombine events (no validation)
    - Explore impossible combinations
    - Discover new connections
    - Save interesting dreams to dreams.jsonl

.PARAMETER Hours
    Hours of recent history to sample for dreams (default: 24).

.PARAMETER Iterations
    Number of dream iterations (default: 10).

.PARAMETER OutJsonl
    Path to dreams log (default: outputs/dreams.jsonl).
#>

param(
    [int]$Hours = 24,
    [int]$Iterations = 10,
    [string]$OutJsonl = "outputs\dreams.jsonl",
    [switch]$UseScarcity,
    [string]$ScarcityJson = "outputs\scarcity_drive_latest.json",
    [double]$Temperature = 1.0,
    [double]$Recombination = 1.0
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$LedgerPath = Join-Path $WorkspaceRoot "fdo_agi_repo\memory\resonance_ledger.jsonl"
$OutPath = Join-Path $WorkspaceRoot $OutJsonl
if ($UseScarcity) {
    $ScarcityPath = Join-Path $WorkspaceRoot $ScarcityJson
    if (Test-Path $ScarcityPath) {
        try {
            $scarcity = Get-Content $ScarcityPath -Raw | ConvertFrom-Json
            if ($scarcity.recommended) {
                if (-not $PSBoundParameters.ContainsKey('Temperature')) {
                    $Temperature = [double]$scarcity.recommended.exploration_temp
                }
                if (-not $PSBoundParameters.ContainsKey('Recombination')) {
                    $Recombination = [double]$scarcity.recommended.recombination
                }
            }
        }
        catch {
            Write-Host "[WARN] Failed to parse scarcity JSON: $ScarcityPath" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "[WARN] Scarcity JSON not found: $ScarcityPath" -ForegroundColor Yellow
    }
}

Write-Host "[DREAM MODE] Starting..." -ForegroundColor Magenta
Write-Host "  Time Window: Last $Hours hours" -ForegroundColor Gray
Write-Host "  Iterations: $Iterations" -ForegroundColor Gray
Write-Host "  Output: $OutPath" -ForegroundColor Gray
if ($UseScarcity) {
    Write-Host "  Scarcity Applied → Temp=$([math]::Round($Temperature,2)), Recomb=$([math]::Round($Recombination,2))" -ForegroundColor DarkCyan
}
else {
    Write-Host "  Params → Temp=$([math]::Round($Temperature,2)), Recomb=$([math]::Round($Recombination,2))" -ForegroundColor DarkGray
}

# Ensure output directory
$outDir = Split-Path $OutPath
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

# Load recent Ledger events
if (-not (Test-Path $LedgerPath)) {
    Write-Host "[WARN] Ledger not found: $LedgerPath" -ForegroundColor Yellow
    Write-Host "       Generating synthetic dream..." -ForegroundColor Yellow
    $events = @()
}
else {
    $cutoff = (Get-Date).AddHours(-$Hours)
    $events = Get-Content $LedgerPath | ForEach-Object {
        try {
            $obj = $_ | ConvertFrom-Json
            if ([datetime]$obj.timestamp -gt $cutoff) {
                $obj
            }
        }
        catch { }
    }
    Write-Host "[OK] Loaded $($events.Count) recent events" -ForegroundColor Green
}

# Dream iteration
for ($i = 0; $i -lt $Iterations; $i++) {
    Write-Host "`n[DREAM $($i+1)/$Iterations]" -ForegroundColor Cyan
    
    # 1. Sample random events (no constraints) — scale with Recombination
    $baseSample = [Math]::Min(5, $events.Count)
    $extra = [Math]::Floor([Math]::Max(0, ($Recombination - 1.0) * 2))
    $sampleSize = [Math]::Min($events.Count, [Math]::Max(1, $baseSample + $extra))
    if ($sampleSize -eq 0) {
        # Synthetic dream if no data
        $sample = @(
            @{ event = "synthetic_pattern_1"; delta = 0.5 },
            @{ event = "synthetic_pattern_2"; delta = 0.3 }
        )
    }
    else {
        $sample = $events | Get-Random -Count $sampleSize
    }
    
    # 2. Extract patterns (event types, deltas, contexts)
    $patterns = $sample | ForEach-Object {
        $deltaValue = if ($_.delta) { [double]$_.delta } else { Get-Random }
        @{
            event   = if ($_.event) { $_.event } else { "unknown_event" }
            delta   = $deltaValue
            context = if ($_.context) { $_.context } else { "unknown" }
        }
    }
    
    # 3. Random recombination (impossible combinations allowed)
    $recombinations = @()
    $recombCount = [Math]::Max(1, [int][Math]::Round(3 * $Recombination))
    for ($j = 0; $j -lt $recombCount; $j++) {
        $p1 = $patterns | Get-Random
        $p2 = $patterns | Get-Random
        $recombinations += "$($p1.event) + $($p2.event)"
    }
    
    # 4. Generate "narrative" (story from patterns)
    $narrative = "In this dream, " + ($recombinations -join ", then ")
    
    # 5. Assess "interestingness" (random + delta-based) — scale threshold with Temperature
    $deltaSum = 0
    $patterns | ForEach-Object { $deltaSum += $_.delta }
    $avgDelta = if ($patterns.Count -gt 0) { $deltaSum / $patterns.Count } else { 0 }
    $threshold = if ($Temperature -ge 1.2) { 0.25 } elseif ($Temperature -le 0.9) { 0.35 } else { 0.3 }
    $rngGate = if ($Temperature -ge 1.2) { 0.6 } else { 0.7 }
    $interesting = ($avgDelta -gt $threshold) -or ((Get-Random) -gt $rngGate)
    
    # 6. Dream log entry
    $dream = @{
        dream_id       = "dream_$(Get-Date -Format 'yyyyMMdd_HHmmss')_$i"
        timestamp      = (Get-Date -Format "o")
        patterns       = $patterns | ForEach-Object { "$($_.event) (delta=$($_.delta))" }
        recombinations = $recombinations
        narrative      = $narrative
        interesting    = $interesting
        avg_delta      = [math]::Round($avgDelta, 3)
        params         = @{ temperature = [math]::Round($Temperature, 2); recombination = [math]::Round($Recombination, 2) }
    }
    
    # Display
    Write-Host "  Patterns: $($dream.patterns -join ', ')" -ForegroundColor Gray
    Write-Host "  Narrative: $narrative" -ForegroundColor White
    Write-Host "  Interesting: $interesting (delta=$([math]::Round($avgDelta,3)))" -ForegroundColor $(if ($interesting) { "Yellow" } else { "Gray" })
    
    # 7. Save if interesting
    if ($interesting) {
        $dream | ConvertTo-Json -Depth 10 -Compress | Out-File -Append -Encoding UTF8 -FilePath $OutPath
        Write-Host "  [SAVED] to dreams.jsonl" -ForegroundColor Green
    }
    
    Start-Sleep -Milliseconds 500
}

Write-Host "`n[DREAM MODE] Complete" -ForegroundColor Magenta
Write-Host "  Dreams logged: $OutPath" -ForegroundColor Gray

# Summary
if (Test-Path $OutPath) {
    $dreamCount = (Get-Content $OutPath | Measure-Object -Line).Lines
    Write-Host "`n[SUMMARY] Total dreams saved: $dreamCount" -ForegroundColor Cyan
}
