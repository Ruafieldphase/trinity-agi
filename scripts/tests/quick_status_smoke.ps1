<#
Quick Status Smoke Test

Purpose
    - Validate that `outputs/quick_status_latest.json` exists and has a sane minimal shape.
    - Optionally enforce strict SLO profiles and trend stability checks.
    - With -ExplainStrict, emit a one-line JSON summary of thresholds, current latencies, online flags, and trend directions when strict checks pass.

Behavior
    - If the JSON is missing, empty, stale (> -StaleMinutes), or -Regenerate is provided, it will invoke `scripts/quick_status.ps1 -OutJson` to generate it.
    - Exit codes: 0 (PASS), 2 (FAIL). Non-zero from quick_status.ps1 also results in 2.

Key Parameters
    - -Profile <ops-normal|latency-first|ops-tight>
            Applies preset SLO thresholds and requires all channels online.
    - -Strict
            Enforce thresholds (Local/Cloud/Gateway) and, if requested, online checks.
    - -CheckTrendStability
            If trend direction is worsening and current latency is ≥ TrendWarnPercent% of threshold, fail early.
    - -TrendWarnPercent <50..99>
            Margin for early warning (default 85). Used with -CheckTrendStability.
    - -ExplainStrict
            When -Strict passes, prints a single JSON line with: profile, thresholds, warnAt, channels, online, trend.*Direction.

Notes
    - Local2Ms (optional channel) is validated leniently (allowed null); not part of SLO thresholds by default.
    - Online.* must be boolean when snapshot format is used.
    - Legacy format is tolerated with minimal key presence checks.
#>
param(
    [string]$JsonPath = '',
    [switch]$Regenerate,
    [int]$StaleMinutes = 30,
    [ValidateSet('ops-normal', 'latency-first', 'ops-tight')]
    [string]$Profile = '',
    [switch]$Strict,
    [switch]$ExplainStrict,
    [switch]$CheckTrendStability,
    [ValidateRange(50, 99)]
    [int]$TrendWarnPercent = 85,
    [int]$MaxLocalMs = 500,
    [int]$MaxCloudMs = 1500,
    [int]$MaxGatewayMs = 2000,
    [switch]$RequireAllOnline,
    [switch]$Verbose
)

$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot

# Find workspace root robustly (works whether this file is under scripts/tests or elsewhere)
function Find-RepoRoot([string]$startDir) {
    try {
        $dir = Get-Item -LiteralPath $startDir
    }
    catch { return (Split-Path -Parent (Split-Path -Parent $startDir)) }
    for ($i = 0; $i -lt 6; $i++) {
        $qs = Join-Path $dir.FullName 'scripts\quick_status.ps1'
        if (Test-Path -LiteralPath $qs) { return $dir.FullName }
        if (-not $dir.Parent) { break }
        $dir = $dir.Parent
    }
    return (Split-Path -Parent (Split-Path -Parent $startDir))
}

$root = Find-RepoRoot -startDir $here
$scriptsDir = Join-Path $root 'scripts'

function Write-Info([string]$m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Ok([string]$m) { Write-Host "[ OK ] $m" -ForegroundColor Green }
function Write-Warn([string]$m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err([string]$m) { Write-Host "[ERR ] $m" -ForegroundColor Red }

# Trend direction helper (centralized)
function Test-IsWorsening([string]$d) {
    if ([string]::IsNullOrWhiteSpace($d)) { return $false }
    $s = $d.ToUpperInvariant()
    if ($s -like '*++*' -or $s -like '*+*') { return $true }
    if ($s -like '*WORSEN*' -or $s -like '*DEGRAD*' -or $s -like '*INCREAS*' -or $s -like '*UP*' -or $s -like '*SLOW*' -or $s -like '*REGRESS*') { return $true }
    return $false
}

if (-not $JsonPath -or $JsonPath.Trim().Length -eq 0) { $JsonPath = Join-Path $root 'outputs/quick_status_latest.json' }
$quickStatusPs1 = Join-Path $scriptsDir 'quick_status.ps1'

if (-not (Test-Path -LiteralPath $quickStatusPs1)) {
    Write-Err "quick_status.ps1 not found at: $quickStatusPs1"
    exit 2
}

$needGen = $Regenerate -or (-not (Test-Path -LiteralPath $JsonPath))
if (-not $needGen) {
    try {
        $fi = Get-Item -LiteralPath $JsonPath
        if ($fi.Length -eq 0) { $needGen = $true }
        elseif ((Get-Date) - $fi.LastWriteTime -gt [TimeSpan]::FromMinutes($StaleMinutes)) { $needGen = $true }
    }
    catch { $needGen = $true }
}

if ($needGen) {
    Write-Info "Generating quick status JSON -> $JsonPath"
    & $quickStatusPs1 -OutJson $JsonPath | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Err "quick_status.ps1 returned non-zero exit code: $LASTEXITCODE"; exit 2 }
}

if (-not (Test-Path -LiteralPath $JsonPath)) { Write-Err "Missing JSON: $JsonPath"; exit 2 }

# Load and validate
try {
    $raw = Get-Content -LiteralPath $JsonPath -Raw -Encoding UTF8
}
catch {
    $errMsg = $_.Exception.Message
    Write-Err "Failed to read ${JsonPath}: ${errMsg}"
    exit 2
}
if (-not $raw -or $raw.Trim().Length -eq 0) { Write-Err "Empty JSON: $JsonPath"; exit 2 }

try {
    # ConvertFrom-Json does not support -Depth (only ConvertTo-Json does); pipeline depth isn't limited here.
    $obj = $raw | ConvertFrom-Json
}
catch {
    $errMsg = $_.Exception.Message
    Write-Err "Invalid JSON: ${errMsg}"
    exit 2
}

if ($null -eq $obj -or ($obj | Get-Member -MemberType NoteProperty, Property, ScriptProperty).Count -eq 0) {
    Write-Err "JSON is not an object with properties"
    exit 2
}

# Support two formats:
# 1) Snapshot format (current): { Timestamp, Channels, Online, Trend, Issues, Warnings }
# 2) Legacy monitor format: keys among { summary, status, overall, metrics, services, components, checks, timestamp }

$isSnapshot = ($null -ne $obj.Timestamp -or $null -ne $obj.Channels -or $null -ne $obj.Online -or $null -ne $obj.Trend)

# Apply profile presets (only affects strict checks)
if ([string]::IsNullOrWhiteSpace($Profile) -eq $false) {
    switch ($Profile) {
        'ops-normal' {
            $MaxLocalMs = 100
            $MaxCloudMs = 1000
            $MaxGatewayMs = 1200
            $RequireAllOnline = $true
        }
        'latency-first' {
            $MaxLocalMs = 50
            $MaxCloudMs = 500
            $MaxGatewayMs = 600
            $RequireAllOnline = $true
        }
        'ops-tight' {
            $MaxLocalMs = 70
            $MaxCloudMs = 700
            $MaxGatewayMs = 800
            $RequireAllOnline = $true
        }
    }
}

if ($isSnapshot) {
    # Basic required keys for snapshot format
    $snapKeys = @('Timestamp', 'Channels', 'Online')
    $missing = @()
    foreach ($k in $snapKeys) { if ($null -eq $obj.$k) { $missing += $k } }
    if ($missing.Count -gt 0) { Write-Err "Snapshot JSON missing required keys: $($missing -join ', ')"; exit 2 }

    # Timestamp sanity
    try {
        $ts = [DateTime]::Parse($obj.Timestamp, [Globalization.CultureInfo]::InvariantCulture)
    }
    catch { Write-Err "Timestamp not parseable: $($obj.Timestamp)"; exit 2 }

    # Online sanity
    foreach ($n in @('Local', 'Cloud', 'Gateway')) {
        if ($null -eq $obj.Online.$n) { Write-Err "Online.$n missing"; exit 2 }
        if (-not ($obj.Online.$n -is [bool])) { Write-Err "Online.$n must be boolean"; exit 2 }
    }

    # Channels sanity (allow null for Local2Ms)
    foreach ($n in @('LocalMs', 'CloudMs', 'GatewayMs')) {
        if ($null -eq $obj.Channels.$n) { Write-Err "Channels.$n missing"; exit 2 }
        if ($obj.Channels.$n -ne $null -and [int]$obj.Channels.$n -lt 0) { Write-Err "Channels.$n negative"; exit 2 }
    }
    if ($obj.Channels.Local2Ms -ne $null -and [int]$obj.Channels.Local2Ms -lt 0) { Write-Err "Channels.Local2Ms negative"; exit 2 }

    # Trend sanity (lenient)
    if ($null -ne $obj.Trend) {
        foreach ($ch in @('Local', 'Cloud', 'Gateway')) {
            $t = $obj.Trend.$ch
            if ($null -ne $t) {
                if ($null -ne $t.Count -and [int]$t.Count -lt 0) { Write-Err "Trend.$ch.Count < 0"; exit 2 }
                if ($null -ne $t.Direction -and [string]::IsNullOrWhiteSpace([string]$t.Direction)) { Write-Err "Trend.$ch.Direction empty"; exit 2 }
            }
        }
    }

    # Optional strict validation block
    if ($Strict) {
        $violations = @()
        $explain = [ordered]@{}
        # Require all online if requested
        if ($RequireAllOnline) {
            foreach ($n in @('Local', 'Cloud', 'Gateway')) {
                if (-not ($obj.Online.$n -eq $true)) { $violations += "Online.$n is not true" }
            }
        }

        # Latency thresholds (ignore nulls, only check > 0 values)
        $local = $obj.Channels.LocalMs
        $cloud = $obj.Channels.CloudMs
        $gateway = $obj.Channels.GatewayMs
        if ($null -ne $local -and [int]$local -gt 0 -and [int]$local -gt [int]$MaxLocalMs) { $violations += "LocalMs $local > $MaxLocalMs" }
        if ($null -ne $cloud -and [int]$cloud -gt 0 -and [int]$cloud -gt [int]$MaxCloudMs) { $violations += "CloudMs $cloud > $MaxCloudMs" }
        if ($null -ne $gateway -and [int]$gateway -gt 0 -and [int]$gateway -gt [int]$MaxGatewayMs) { $violations += "GatewayMs $gateway > $MaxGatewayMs" }

        # Trend stability checks (optional): if trend is worsening and current latency is near threshold, flag early
        if ($CheckTrendStability -and $null -ne $obj.Trend) {
            $margin = [double]$TrendWarnPercent / 100.0

            # Local
            $dLocal = $null; if ($null -ne $obj.Trend.Local) { $dLocal = [string]$obj.Trend.Local.Direction }
            if (Test-IsWorsening $dLocal) {
                if ($null -ne $local -and [int]$MaxLocalMs -gt 0) {
                    $thresholdLocal = [int]([double]$MaxLocalMs * $margin)
                    if ([int]$local -ge $thresholdLocal) { $violations += "Trend.Local worsening ($dLocal) with LocalMs $local >= ${TrendWarnPercent}% of $MaxLocalMs" }
                }
            }
            # Cloud
            $dCloud = $null; if ($null -ne $obj.Trend.Cloud) { $dCloud = [string]$obj.Trend.Cloud.Direction }
            if (Test-IsWorsening $dCloud) {
                if ($null -ne $cloud -and [int]$MaxCloudMs -gt 0) {
                    $thresholdCloud = [int]([double]$MaxCloudMs * $margin)
                    if ([int]$cloud -ge $thresholdCloud) { $violations += "Trend.Cloud worsening ($dCloud) with CloudMs $cloud >= ${TrendWarnPercent}% of $MaxCloudMs" }
                }
            }
            # Gateway
            $dGateway = $null; if ($null -ne $obj.Trend.Gateway) { $dGateway = [string]$obj.Trend.Gateway.Direction }
            if (Test-IsWorsening $dGateway) {
                if ($null -ne $gateway -and [int]$MaxGatewayMs -gt 0) {
                    $thresholdGateway = [int]([double]$MaxGatewayMs * $margin)
                    if ([int]$gateway -ge $thresholdGateway) { $violations += "Trend.Gateway worsening ($dGateway) with GatewayMs $gateway >= ${TrendWarnPercent}% of $MaxGatewayMs" }
                }
            }
            # For explanation payload
            $explain.trend = [ordered]@{
                localDirection   = $dLocal
                cloudDirection   = $dCloud
                gatewayDirection = $dGateway
            }
        }

        if ($violations.Count -gt 0) {
            $msg = $violations -join '; '
            Write-Err "Strict validation failed: $msg"
            exit 2
        }

        if ($ExplainStrict) {
            $margin = [double]$TrendWarnPercent / 100.0
            $explain.profile = if ([string]::IsNullOrWhiteSpace($Profile)) { '(custom)' } else { $Profile }
            $explain.requireAllOnline = [bool]$RequireAllOnline
            $explain.thresholds = [ordered]@{
                localMs          = [int]$MaxLocalMs
                cloudMs          = [int]$MaxCloudMs
                gatewayMs        = [int]$MaxGatewayMs
                warnAt           = [ordered]@{
                    localMs   = [int]([double]$MaxLocalMs * $margin)
                    cloudMs   = [int]([double]$MaxCloudMs * $margin)
                    gatewayMs = [int]([double]$MaxGatewayMs * $margin)
                }
                trendWarnPercent = [int]$TrendWarnPercent
            }
            $explain.channels = [ordered]@{
                localMs   = $obj.Channels.LocalMs
                local2Ms  = $obj.Channels.Local2Ms
                cloudMs   = $obj.Channels.CloudMs
                gatewayMs = $obj.Channels.GatewayMs
            }
            $explain.online = [ordered]@{
                local   = [bool]$obj.Online.Local
                cloud   = [bool]$obj.Online.Cloud
                gateway = [bool]$obj.Online.Gateway
            }
            # Emit one-line JSON for downstream parsing
            ($explain | ConvertTo-Json -Depth 6) | Write-Output
        }
    }

    Write-Ok "quick_status_latest.json looks sane (snapshot format) at ${JsonPath}."
    exit 0
}
else {
    # Legacy minimal shape checks (lenient to allow format evolution)
    $keys = @('summary', 'status', 'overall', 'metrics', 'services', 'components', 'checks', 'timestamp')
    $present = @()
    foreach ($k in $keys) { if ($null -ne $obj.$k) { $present += $k } }
    if ($present.Count -eq 0) {
        Write-Err "JSON missing any of required keys: $($keys -join ', ')"
        exit 2
    }
    if ($null -ne $obj.status -and ($obj.status -is [string])) {
        if ([string]::IsNullOrWhiteSpace($obj.status)) { Write-Err "status is empty string"; exit 2 }
    }
    Write-Ok "quick_status_latest.json looks sane (legacy format) at ${JsonPath}. Keys present: $($present -join ', ')"
    exit 0
}
