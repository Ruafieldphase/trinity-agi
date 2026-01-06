Param(
    [ValidateSet("disabled","observe","enforce")]
    [string]$Mode = "observe",
    [string]$Policy,
    [int]$Hours = 1,
    [switch]$OpenMd,
    [switch]$Restore
)

$ErrorActionPreference = "Stop"

function Write-Info($msg) {
    Write-Host "[policy-smoke] $msg"
}

function Load-JsonFile([string]$path) {
    if (-not (Test-Path -LiteralPath $path)) { return $null }
    try {
        $raw = Get-Content -LiteralPath $path -Raw -Encoding UTF8
        if (-not $raw) { return $null }
        return $raw | ConvertFrom-Json
    } catch {
        return $null
    }
}

function Save-JsonFile([string]$path, $obj) {
    $json = $obj | ConvertTo-Json -Depth 16
    $dir = Split-Path -Parent $path
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
    Set-Content -LiteralPath $path -Value $json -Encoding UTF8
}

try {
    $primary = Join-Path (Resolve-Path ".").Path "configs/resonance_config.json"
    $example = Join-Path (Resolve-Path ".").Path "configs/resonance_config.example.json"
    $cfgPath = $null
    if (Test-Path -LiteralPath $primary) { $cfgPath = $primary }
    elseif (Test-Path -LiteralPath $example) { $cfgPath = $example }
    else {
        $cfgPath = $primary
        Write-Info "No config found; creating default at $cfgPath"
        $default = [ordered]@{
            active_mode = "observe";
            default_policy = "quality-first";
            active_policy = "quality-first";
            closed_loop_snapshot_period_sec = 300;
            policies = [ordered]@{
                "quality-first" = @{ min_quality = 0.8; require_evidence = $true; max_latency_ms = 8000 };
                "latency-first" = @{ min_quality = 0.5; require_evidence = $false; max_latency_ms = 1500 };
            }
        }
        Save-JsonFile -path $cfgPath -obj $default
    }

    if ($Restore) {
        $dir = Split-Path -Parent $cfgPath
        $name = Split-Path -Leaf $cfgPath
        $pattern = "$name.bak_*"
        $candidates = Get-ChildItem -LiteralPath $dir -Filter $pattern | Sort-Object LastWriteTime -Descending
        if ($candidates -and $candidates.Count -gt 0) {
            $latest = $candidates[0].FullName
            Copy-Item -LiteralPath $latest -Destination $cfgPath -Force
            Write-Info "Restored from backup: $latest -> $cfgPath"
        } else {
            Write-Warning "No backup files found to restore in $dir"
        }
    } else {
        $cfg = Load-JsonFile -path $cfgPath
        if ($null -eq $cfg) { throw "Failed to load resonance config at $cfgPath" }

        $backup = "$cfgPath.bak_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Copy-Item -LiteralPath $cfgPath -Destination $backup -Force
        Write-Info "Backup saved: $backup"

        # Apply requested toggles
        $cfg.active_mode = $Mode
        if ($Policy) { $cfg.active_policy = $Policy }
        Save-JsonFile -path $cfgPath -obj $cfg
        Write-Info "Updated $cfgPath (mode=$Mode, policy=$($cfg.active_policy))"
    }

    # Regenerate monitoring report (core)
    $reportScript = "scripts/generate_monitoring_report.ps1"
    if (-not (Test-Path -LiteralPath $reportScript)) { throw "Missing $reportScript" }

    Write-Info "Generating monitoring report for last $Hours hour(s)…"
    & $reportScript -Hours $Hours | Out-Host

    $latest = "outputs/monitoring_report_latest.md"
    if ($OpenMd -and (Test-Path -LiteralPath $latest)) {
        Write-Info "Opening $latest"
        Invoke-Item -LiteralPath $latest
    }

    if (-not $Restore) {
        Write-Info "Done. Mode=$Mode Policy=$($cfg.active_policy). Report refreshed."
    } else {
        Write-Info "Done. Restored last config and refreshed report."
    }
} catch {
    Write-Error $_
    exit 1
}