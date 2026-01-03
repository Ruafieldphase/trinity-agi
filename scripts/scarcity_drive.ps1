#Requires -Version 5.1
<#!
.SYNOPSIS
  Compute a simple Scarcity (결핍) Drive and map it to recommended knobs for Dream/Unconscious.

.DESCRIPTION
  Aggregates a few signals (novelty, cognitive, material) into a unified drive score [0..1].
  Outputs JSON with the drive and recommended parameters:
    - exploration_temp   (for diversity / sampling temperature)
    - recombination      (for pattern recombination breadth)
    - collapse_gain      (for selection/collapse aggressiveness)
    - plasticity         (for momentary learning strength)

  If -ProbeOutputs is set, estimate novelty deficit by scanning recent dream logs.

.PARAMETER WindowHours
  Time window to probe for novelty signals (default: 24)

.PARAMETER Material
  Material (resource) deficit in [0..1]. If not provided, defaults to 0.0

.PARAMETER Cognitive
  Cognitive/attention deficit in [0..1]. If not provided, defaults to 0.0

.PARAMETER Novelty
  Novelty deficit in [0..1]. If set to -1, auto-probe from outputs (default: -1)

.PARAMETER ProbeOutputs
  If set, scan outputs to compute novelty deficit heuristically

.PARAMETER OutJson
  Output JSON path (default: outputs/scarcity_drive_latest.json)
#>

[CmdletBinding()]
param(
    [int]$WindowHours = 24,
    [double]$Material = 0.0,
    [double]$Cognitive = 0.0,
    [double]$Novelty = -1.0,
    [switch]$ProbeOutputs,
    [string]$OutJson = "outputs\\scarcity_drive_latest.json"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$OutPath = Join-Path $WorkspaceRoot $OutJson

# Ensure output directory
$outDir = Split-Path $OutPath
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

function Clamp([double]$x, [double]$lo, [double]$hi) {
    if ($x -lt $lo) { return $lo }
    if ($x -gt $hi) { return $hi }
    return $x
}

function Lerp([double]$a, [double]$b, [double]$t) {
    return $a + ($b - $a) * (Clamp $t 0 1)
}

function Get-NoveltyDeficitFromOutputs {
    param([int]$Hours)
    $dreamsPath = Join-Path $WorkspaceRoot "outputs\\dreams.jsonl"
    $unconsciousPath = Join-Path $WorkspaceRoot "outputs\\unconscious_log.jsonl"
    $cutoff = (Get-Date).AddHours(-$Hours)
    $saved = 0
    $diversitySet = New-Object System.Collections.Generic.HashSet[string]

    if (Test-Path $dreamsPath) {
        Get-Content $dreamsPath | ForEach-Object {
            try {
                $o = $_ | ConvertFrom-Json
                $ts = [datetime]$o.timestamp
                if ($ts -gt $cutoff) {
                    $saved++
                    if ($o.recombinations) { $o.recombinations | ForEach-Object { [void]$diversitySet.Add($_) } }
                }
            }
            catch {}
        }
    }
    if (Test-Path $unconsciousPath) {
        Get-Content $unconsciousPath | ForEach-Object {
            try {
                $o = $_ | ConvertFrom-Json
                $ts = [datetime]$o.timestamp
                if ($ts -gt $cutoff) {
                    $saved++
                    if ($o.events) { $o.events | ForEach-Object { [void]$diversitySet.Add($_) } }
                    if ($o.beyond_boundary) { [void]$diversitySet.Add($o.beyond_boundary) }
                }
            }
            catch {}
        }
    }

    # Heuristic target: 5 items in window, 10 unique tokens
    $targetSaved = 5.0
    $targetUnique = 10.0
    $savedScore = [Math]::Min(1.0, $saved / $targetSaved)
    $uniqueScore = [Math]::Min(1.0, ($diversitySet.Count) / $targetUnique)
    $noveltyAchieved = 0.6 * $uniqueScore + 0.4 * $savedScore
    $deficit = 1.0 - $noveltyAchieved
    return (Clamp $deficit 0.0 1.0)
}

if ($ProbeOutputs -and $Novelty -eq -1.0) {
    $Novelty = Get-NoveltyDeficitFromOutputs -Hours $WindowHours
}
if ($Novelty -eq -1.0) { $Novelty = 0.0 }

# Aggregate to a single drive score
$wNovelty = 0.5; $wCognitive = 0.3; $wMaterial = 0.2
$Drive = ($wNovelty * $Novelty) + ($wCognitive * $Cognitive) + ($wMaterial * $Material)
$Drive = Clamp $Drive 0.0 1.0

# Map to knobs
$recommended = @{
    exploration_temp = [math]::Round((Lerp 0.9 1.7 $Drive), 3)
    recombination    = [math]::Round((Lerp 1.0 2.5 $Drive), 3)
    collapse_gain    = [math]::Round((Lerp 1.0 2.0 $Drive), 3)
    plasticity       = [math]::Round((Lerp 0.1 0.8 $Drive), 3)
}

$result = @{
    timestamp    = (Get-Date -Format 'o')
    window_hours = $WindowHours
    inputs       = @{
        material      = [math]::Round($Material, 3)
        cognitive     = [math]::Round($Cognitive, 3)
        novelty       = [math]::Round($Novelty, 3)
        probe_outputs = [bool]$ProbeOutputs
    }
    drive        = [math]::Round($Drive, 3)
    recommended  = $recommended
}

$result | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutPath -Encoding UTF8 -Force

Write-Host "[SCARCITY] Drive computed -> $OutPath" -ForegroundColor Green
Write-Host (Get-Content $OutPath -Raw) -ForegroundColor DarkGray