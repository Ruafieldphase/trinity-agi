Param(
    [switch]$ShowLedger
)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::UTF8; $OutputEncoding = [System.Text.UTF8Encoding]::UTF8 } catch {}

function Get-JsonFile([string]$path) {
    if (-not (Test-Path -LiteralPath $path)) { return $null }
    try {
        $raw = Get-Content -LiteralPath $path -Raw -Encoding UTF8
        if (-not $raw) { return $null }
        return $raw | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

function Get-ResonanceConfigPath {
    $base = Join-Path (Resolve-Path ".").Path "configs"
    $primary = Join-Path $base "resonance_config.json"
    $example = Join-Path $base "resonance_config.example.json"
    if (Test-Path -LiteralPath $primary) { return $primary }
    if (Test-Path -LiteralPath $example) { return $example }
    return $primary # default target if we want to create later
}

Write-Host "[resonance-status] Gathering current configuration …" -ForegroundColor Cyan

$cfgPath = Get-ResonanceConfigPath
$cfg = Get-JsonFile -path $cfgPath
if ($null -eq $cfg) {
    Write-Warning "Config not found at $cfgPath"
}

$activeMode = if ($cfg.active_mode) { [string]$cfg.active_mode } else { 'observe' }
$activePol = if ($cfg.active_policy) { [string]$cfg.active_policy } elseif ($cfg.default_policy) { [string]$cfg.default_policy } else { 'quality-first' }
$periodSec = if ($cfg.closed_loop_snapshot_period_sec) { [int]$cfg.closed_loop_snapshot_period_sec } else { 300 }

$evalMinQ = $null
try {
    $pyCmd = "import json; from fdo_agi_repo.orchestrator.config import get_evaluation_config as g; print(json.dumps(g()))"
    $pyOut = & python -c $pyCmd 2>$null
    if ($LASTEXITCODE -eq 0 -and $pyOut) {
        try { $ev = $pyOut | ConvertFrom-Json -ErrorAction Stop; if ($null -ne $ev.min_quality) { $evalMinQ = [double]$ev.min_quality } } catch {}
    }
}
catch {}

Write-Host ("  Configured Mode     : {0}" -f $activeMode)
Write-Host ("  Configured Policy   : {0}" -f $activePol)
Write-Host ("  ClosedLoop Period   : {0}s" -f $periodSec)
if ($null -ne $evalMinQ) { Write-Host ("  Eval min_quality    : {0}" -f $evalMinQ) }

if ($ShowLedger) {
    try {
        $basePath = (Resolve-Path ".").Path
        $ledger = Join-Path $basePath "fdo_agi_repo\memory\resonance_ledger.jsonl"
        if (-not (Test-Path -LiteralPath $ledger)) { throw "Ledger not found: $ledger" }
        $lastPolicy = $null
        Get-Content -LiteralPath $ledger | ForEach-Object {
            if ([string]::IsNullOrWhiteSpace($_)) { return }
            try {
                $o = $_ | ConvertFrom-Json
                if ($o.event -eq 'resonance_policy') { $lastPolicy = $o }
            }
            catch {}
        }
        if ($null -ne $lastPolicy) {
            $unixEpoch = [datetime]::new(1970, 1, 1, 0, 0, 0, 0, [System.DateTimeKind]::Utc)
            $iso = $null
            try { $iso = $unixEpoch.AddSeconds([double]$lastPolicy.ts).ToString('s') } catch {}
            Write-Host "  Last Observed Policy: mode=$($lastPolicy.mode) policy=$($lastPolicy.policy) time=$iso"
            if ($lastPolicy.reasons) { Write-Host "  Last Reasons        : $($lastPolicy.reasons -join ', ')" }
        }
        else {
            Write-Host "  No policy events found in ledger (window)."
        }
    }
    catch {
        Write-Warning $_
    }
}

Write-Host "[resonance-status] Done." -ForegroundColor Green
