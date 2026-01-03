param(
    [int]$MinResonance = -1,
    [int]$MaxFear = 10,
    [string]$Tag,
    [string]$StateLabel,
    [switch]$LongTermOnly,
    [int]$Top = 20
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$MemoryRoot = Join-Path $WorkspaceRoot "outputs\memory"
$Dirs = @()
if ($LongTermOnly) { $Dirs += (Join-Path $MemoryRoot 'long_term') } else { $Dirs += (Join-Path $MemoryRoot 'short_term'); $Dirs += (Join-Path $MemoryRoot 'long_term') }

$files = @()
foreach ($d in $Dirs) {
    if (Test-Path $d) {
        $files += Get-ChildItem -Path $d -Filter 'snapshot_*.json' -File -ErrorAction SilentlyContinue
    }
}

if (-not $files -or $files.Count -eq 0) {
    Write-Host "No snapshot files found under $Dirs" -ForegroundColor Yellow
    exit 0
}

$results = @()
foreach ($f in $files) {
    try {
        $js = Get-Content -LiteralPath $f.FullName -Raw | ConvertFrom-Json
        $ms = $js.mental_state
        if ($null -eq $ms) { continue }

        $ok = $true
        if ($MinResonance -ge 0 -and [int]$ms.resonance_level -lt $MinResonance) { $ok = $false }
        if ($MaxFear -ge 0 -and [int]$ms.fear_noise_level -gt $MaxFear) { $ok = $false }
        if ($Tag) {
            $tags = @()
            if ($null -ne $ms.tags) { $tags = @($ms.tags) }
            if (-not ($tags -contains $Tag)) { $ok = $false }
        }
        if ($StateLabel -and ($ms.state_label -ne $StateLabel)) { $ok = $false }
        if (-not $ok) { continue }

        $results += [pscustomobject]@{
            Timestamp   = [datetime]$js.timestamp
            Importance  = $js.importance
            Resonance   = [int]$ms.resonance_level
            FearNoise   = [int]$ms.fear_noise_level
            NonSemantic = [bool]$ms.non_semantic_mode
            State       = $ms.state_label
            Reason      = $js.reason
            File        = $f.FullName
        }
    }
    catch {
        Write-Host "Skip invalid json: $($f.FullName)" -ForegroundColor DarkYellow
    }
}

$sorted = $results | Sort-Object Timestamp -Descending | Select-Object -First $Top
if ($sorted.Count -eq 0) {
    Write-Host "No results matched filters." -ForegroundColor Yellow
    exit 0
}

$sorted | Format-Table Timestamp, Importance, Resonance, FearNoise, NonSemantic, State, Reason -AutoSize

$cnt = ($sorted | Measure-Object).Count
Write-Host "\nTop $cnt files:" -ForegroundColor Cyan
$sorted | ForEach-Object { Write-Host $_.File -ForegroundColor Gray }