param(
    [switch]$AlertOnDegraded,
    [string]$OutJson,
    [switch]$LogJsonl,
    [switch]$Perf,
    [string]$LogPath = "C:\workspace\agi\outputs\status_snapshots.jsonl",
    [int]$WarnLocalMs = 1800,
    [int]$AlertLocalMs = 2500,
    [int]$WarnCloudMs = 700,
    [int]$AlertCloudMs = 1200,
    [int]$WarnGatewayMs = 700,
    [int]$AlertGatewayMs = 1200,
    [int]$TrendWindow = 10,
    [int]$LongTrendWindow = 20,
    [double]$SpikeSigma = 2.0,
    [double]$TrendThresholdPercent = 10.0,
    [switch]$UseAdaptiveThresholds,
    [double]$AdaptiveWarnSigmas = 1.5,  # ?�균 + 1.5? (was 1.0?) - reduces false positives by ~50%
    [double]$AdaptiveAlertSigmas = 2.5,  # ?�균 + 2.5? (was 2.0?) - further reduces alert noise
    [switch]$HideOptional  # hide optional local channel (18090)
)

$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
try {
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::UTF8
    $OutputEncoding = [System.Text.UTF8Encoding]::UTF8
}
catch {}

$ErrorActionPreference = "Continue"

# Emit system startup event (best-effort)
try {
    $emitPath = Join-Path $PSScriptRoot 'emit_event.ps1'
    if (Test-Path -LiteralPath $emitPath) {
        & $emitPath -EventType "system_startup" -Payload @{
            component = "quick_status"
            timestamp = (Get-Date).ToUniversalTime().ToString("o")
        } -PersonaId "monitoring"
    }
}
catch {}

function Write-Header {
    Write-Host "`n================================================================" -ForegroundColor Cyan
    Write-Host "  UNIFIED MONITORING DASHBOARD - AGI + Lumen" -ForegroundColor Cyan
    Write-Host "================================================================`n" -ForegroundColor Cyan
}

function Test-Endpoint {
    param(
        [string]$Url,
        [string]$Method = 'GET',
        [string]$BodyJson = $null,
        [int]$TimeoutSec = 5
    )
    $result = @{ Online = $false; Ms = $null; Code = 0; Error = $null }
    try {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        if ($BodyJson) {
            $null = Invoke-RestMethod -Uri $Url -Method $Method -Body $BodyJson -ContentType "application/json" -TimeoutSec $TimeoutSec -ErrorAction Stop
        }
        else {
            $null = Invoke-RestMethod -Uri $Url -Method $Method -TimeoutSec $TimeoutSec -ErrorAction Stop
        }
        $sw.Stop()
        $result.Online = $true
        $result.Ms = [int][math]::Round($sw.Elapsed.TotalMilliseconds)
        $result.Code = 200
    }
    catch {
        $sw.Stop()
        $result.Online = $false
        $result.Ms = [int][math]::Round($sw.Elapsed.TotalMilliseconds)
        $result.Code = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode.value__ } else { 0 }
        $result.Error = $_.Exception.Message
    }
    return $result
}

function Show-LatencyLine {
    param(
        [string]$Label,
        [hashtable]$Probe,
        [int]$WarnMs,
        [int]$AlertMs,
        [int]$PrevMs = $null
    )
    $status = if ($Probe.Online) { "ONLINE" } else { "OFFLINE" }
    $color = if (-not $Probe.Online) { 'Red' } elseif ($Probe.Ms -ge $AlertMs) { 'Red' } elseif ($Probe.Ms -ge $WarnMs) { 'Yellow' } else { 'Green' }
    $arrow = ''
    if ($null -ne $PrevMs -and $PrevMs -gt 0 -and $Probe.Ms -gt 0) {
        # ASCII-only indicators for PowerShell 5.1 consoles
        if ($Probe.Ms -lt $PrevMs * 0.9) { $arrow = ' v' }
        elseif ($Probe.Ms -gt $PrevMs * 1.1) { $arrow = ' ^' }
        else { $arrow = ' -' }
    }
    Write-Host ("    {0,-24} " -f $Label) -NoNewline
    if ($Probe.Online) {
        Write-Host " $status" -ForegroundColor $color -NoNewline
        Write-Host " (" -NoNewline; Write-Host "$($Probe.Ms)" -ForegroundColor White -NoNewline; Write-Host " ms$arrow)"
    }
    else {
        Write-Host " $status" -ForegroundColor $color
        if ($Probe.Error) { Write-Host ("      Error: {0}" -f $Probe.Error) -ForegroundColor DarkGray }
    }
}

function Read-LastSnapshot {
    param([string]$Path)
    try {
        if (-not (Test-Path $Path)) { return $null }
        $line = Get-Content -LiteralPath $Path -Tail 1 -ErrorAction Stop
        if (-not $line) { return $null }
        return $line | ConvertFrom-Json -ErrorAction Stop
    }
    catch { return $null }
}

function Read-RecentSnapshots {
    param([string]$Path, [int]$MaxCount = 10)
    $items = @()
    try {
        if (-not (Test-Path $Path)) { return @() }
        $lines = Get-Content -LiteralPath $Path -Tail $MaxCount -ErrorAction Stop
        foreach ($ln in $lines) {
            try {
                if ([string]::IsNullOrWhiteSpace($ln)) { continue }
                $obj = $ln | ConvertFrom-Json -ErrorAction Stop
                if ($obj -and $obj.Channels) { $items += $obj }
            }
            catch { }
        }
    }
    catch { }
    return $items
}

# Show concise performance dashboard summary (from latest JSON)
function Show-PerfSummary {
    try {
        $perfPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'outputs\performance_metrics_latest.json'
        if (-not (Test-Path -LiteralPath $perfPath)) {
            Write-Host "[Perf] performance_metrics_latest.json not found" -ForegroundColor DarkGray
            return
        }
        $perf = Get-Content -LiteralPath $perfPath -Raw | ConvertFrom-Json
        $eff = [double]$perf.OverallEffectiveSuccessRate
        $overall = [double]$perf.OverallSuccessRate
        $systems = [int]$perf.SystemsConsidered
        $exAt = if ($perf.Thresholds -and $perf.Thresholds.ExcellentAt) { [double]$perf.Thresholds.ExcellentAt } else { 90 }
        $gdAt = if ($perf.Thresholds -and $perf.Thresholds.GoodAt) { [double]$perf.Thresholds.GoodAt } else { 70 }
        $band = $perf.BandCounts
        $top = ''
        if ($perf.PSObject.Properties.Name -contains 'TopAttention' -and $perf.TopAttention -and $perf.TopAttention.Count -gt 0) {
            $t0 = $perf.TopAttention[0]
            $top = ("{0} ({1}%)" -f $t0.System, ([double]$t0.EffectiveSuccessRate).ToString('F1'))
        }
        $color = if ($eff -ge $exAt) { 'Green' } elseif ($eff -ge $gdAt) { 'Yellow' } else { 'Red' }
        $bandsText = if ($band) { ("E={0} G={1} N={2} ND={3}" -f $band.Excellent, $band.Good, $band.Needs, $band.NoData) } else { '' }
        $topText = if ([string]::IsNullOrWhiteSpace($top)) { '' } else { " | Top: $top" }
        Write-Host ("[Perf] Effective {0}% (Systems {1}) | {2}{3}" -f $eff.ToString('F1'), $systems, $bandsText, $topText) -ForegroundColor $color
    }
    catch {
        Write-Host "[Perf] failed to load summary" -ForegroundColor DarkGray
    }
}

function Append-Snapshot {
    param([string]$Path, [hashtable]$Snapshot)
    try {
        $dir = Split-Path -Parent $Path
        if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
        $json = ($Snapshot | ConvertTo-Json -Depth 6 -Compress)
        # Append as UTF-8 without BOM to keep JSONL portable on PS 5.1
        try {
            $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
            [System.IO.File]::AppendAllText($Path, $json + [Environment]::NewLine, $utf8NoBom)
        }
        catch {
            # Fallback
            Add-Content -LiteralPath $Path -Value $json -Encoding UTF8
        }
    }
    catch { }
}

function Send-AlertIfNeeded {
    param(
        [hashtable]$Summary,
        [hashtable]$Trend = @{},
        [switch]$Force
    )
    $need = $Force -or (-not $Summary.AllGreen)
    if (-not $need) { return }
    # basic rate limiting (5 minutes)
    $coolFile = "C:\workspace\agi\outputs\last_alert.txt"
    try {
        if (-not $Force -and (Test-Path $coolFile)) {
            $last = Get-Content -LiteralPath $coolFile -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($last) {
                $lastDt = [datetime]::Parse($last)
                if ((Get-Date) -lt $lastDt.AddMinutes(5)) {
                    Write-Host "(Alert) Skipped due to cooldown window" -ForegroundColor DarkYellow
                    return
                }
            }
        }
    }
    catch { }
    $title = if ($Summary.IsDegraded) { "UNIFIED ALERT - Degraded" } else { "UNIFIED WARN - Latency" }
    $lines = @()
    foreach ($i in $Summary.Issues) { $lines += "- $i" }
    foreach ($w in $Summary.Warnings) { $lines += "- $w" }
    if ($lines.Count -eq 0) { $lines = @("- No details") }
    
    # Add trend context if available
    if ($Trend -and ($Trend.Local.Count -gt 0 -or $Trend.Cloud.Count -gt 0 -or $Trend.Gateway.Count -gt 0)) {
        $lines += ""
        $lines += "_Trend (short-term avg +/- std, direction):_"
        if ($Trend.Local.Count -gt 0) {
            $arrow = Get-TrendArrow -direction $Trend.Local.Direction
            $dirText = if ($Trend.Local.LongCount -ge $LongTrendWindow) { " $arrow $($Trend.Local.Direction)" } else { "" }
            $lines += ("Local: {0}ms +/- {1}ms (n={2}){3}" -f [int]$Trend.Local.ShortTermMeanMs, [int]$Trend.Local.StdMs, $Trend.Local.Count, $dirText)
        }
        if ($Trend.Cloud.Count -gt 0) {
            $arrow = Get-TrendArrow -direction $Trend.Cloud.Direction
            $dirText = if ($Trend.Cloud.LongCount -ge $LongTrendWindow) { " $arrow $($Trend.Cloud.Direction)" } else { "" }
            $lines += ("Cloud: {0}ms +/- {1}ms (n={2}){3}" -f [int]$Trend.Cloud.ShortTermMeanMs, [int]$Trend.Cloud.StdMs, $Trend.Cloud.Count, $dirText)
        }
        if ($Trend.Gateway.Count -gt 0) {
            $arrow = Get-TrendArrow -direction $Trend.Gateway.Direction
            $dirText = if ($Trend.Gateway.LongCount -ge $LongTrendWindow) { " $arrow $($Trend.Gateway.Direction)" } else { "" }
            $lines += ("Gateway: {0}ms +/- {1}ms (n={2}){3}" -f [int]$Trend.Gateway.ShortTermMeanMs, [int]$Trend.Gateway.StdMs, $Trend.Gateway.Count, $dirText)
        }
    }
    
    $text = "*$title*`n" + ($lines -join "`n")

    $slack = $env:SLACK_WEBHOOK_URL
    if ($slack) {
        try {
            $payload = @{ text = $text; username = "Unified Dashboard"; icon_emoji = ":rotating_light:" }
            $json = $payload | ConvertTo-Json -Compress
            Invoke-RestMethod -Uri $slack -Method POST -Body $json -ContentType "application/json" | Out-Null
        }
        catch { Write-Host "(Slack) send failed: $($_.Exception.Message)" -ForegroundColor Yellow }
    }
    $discord = $env:DISCORD_WEBHOOK_URL
    if ($discord) {
        try {
            $payload = @{ content = $title + "`n" + ($lines -join "`n") }
            $json = $payload | ConvertTo-Json -Compress
            Invoke-RestMethod -Uri $discord -Method POST -Body $json -ContentType "application/json" | Out-Null
        }
        catch { Write-Host "(Discord) send failed: $($_.Exception.Message)" -ForegroundColor Yellow }
    }
    try { $dir = Split-Path -Parent $coolFile; if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }; Set-Content -LiteralPath $coolFile -Value ((Get-Date).ToString('s')) } catch { }
}

Write-Header

# Initialize AGI metrics container for event emission later
$agiMetrics = @{ confidence = $null; quality = $null; second_pass_rate = $null }

# ===== AGI ?�스??=====
Write-Host "[1] AGI Orchestrator (fdo_agi_repo)" -ForegroundColor Yellow
Write-Host "    Status Check..." -NoNewline

$agiRoot = "C:\workspace\agi\fdo_agi_repo"
$pythonExe = if (Test-Path "$agiRoot\.venv\Scripts\python.exe") { "$agiRoot\.venv\Scripts\python.exe" } else { "python" }

$agiSummaryText = $null
try {
    Push-Location $agiRoot
    $agiOutput = & $pythonExe "scripts\ops_dashboard.py" 2>&1
    # Sanitize ANSI color codes and non-ASCII glyphs from child output for clean PowerShell 5.1 rendering
    $ansiPattern = "`e\[[0-9;]*m"
    $agiOutput = $agiOutput | ForEach-Object {
        $line = $_ -replace $ansiPattern, ""
        # Remove remaining ANSI remnants like "[0m" if any
        $line = $line -replace "\[[0-9;]*m", ""
        # Strip non-ASCII characters to avoid garbled symbols in legacy consoles
        ($line.ToCharArray() | Where-Object { [int]$_ -le 127 } | ForEach-Object { [string]$_ }) -join ''
    }
    Pop-Location
    
    if ($LASTEXITCODE -eq 0) {
        # Normalize and extract key metrics instead of printing raw lines (to avoid garbled glyphs)
        $summary = @()
        $agiText = ($agiOutput -join "`n")
        $status = if ([regex]::IsMatch($agiText, "\bUNHEALTHY\b")) { "UNHEALTHY" } elseif ([regex]::IsMatch($agiText, "\bHEALTHY\b")) { "HEALTHY" } else { "UNKNOWN" }
        if ($status -eq "HEALTHY") { Write-Host " HEALTHY" -ForegroundColor Green } elseif ($status -eq "UNHEALTHY") { Write-Host " UNHEALTHY" -ForegroundColor Red } else { Write-Host " UNKNOWN" -ForegroundColor Yellow }

        $m = [regex]::Match($agiText, "Confidence:\s*([0-9]+(?:\.[0-9]+)?)")
        if ($m.Success) {
            $conf = $m.Groups[1].Value
            Write-Host ("  Confidence: {0}" -f $conf) -ForegroundColor White
            $summary += "Confidence: $conf"
            $agiMetrics.confidence = [double]$conf
        }

        $m = [regex]::Match($agiText, "Quality:\s*([0-9]+(?:\.[0-9]+)?)")
        if ($m.Success) {
            $qual = $m.Groups[1].Value
            Write-Host ("  Quality:    {0}" -f $qual) -ForegroundColor White
            $summary += "Quality: $qual"
            $agiMetrics.quality = [double]$qual
        }

        $m = [regex]::Match($agiText, "2nd Pass:\s*([0-9]+(?:\.[0-9]+)?)")
        if ($m.Success) {
            $sec = $m.Groups[1].Value
            Write-Host ("  2nd Pass:   {0}" -f $sec) -ForegroundColor White
            $summary += "2nd Pass: $sec"
            $agiMetrics.second_pass_rate = [double]$sec
        }

        $m = [regex]::Match($agiText, "Port\s+(\d+):\s*([A-Za-z]+)")
        if ($m.Success) { $port = $m.Groups[1].Value; $pstatus = $m.Groups[2].Value; Write-Host ("  Port {0}: {1}" -f $port, $pstatus) -ForegroundColor White; $summary += ("Port {0}: {1}" -f $port, $pstatus) }

        $m = [regex]::Match($agiText, "CPU:\s*([0-9]+(?:\.[0-9]+)?)%")
        if ($m.Success) { $cpu = $m.Groups[1].Value; Write-Host ("  CPU:    {0}%" -f $cpu) -ForegroundColor White; $summary += "CPU: $cpu%" }

        $m = [regex]::Match($agiText, "Memory:\s*([0-9]+(?:\.[0-9]+)?)%")
        if ($m.Success) { $mem = $m.Groups[1].Value; Write-Host ("  Memory: {0}%" -f $mem) -ForegroundColor White; $summary += "Memory: $mem%" }
        $agiSummaryText = ($summary -join "\n")
    }
    else {
        Write-Host " ERROR" -ForegroundColor Red
    }
}
catch {
    Write-Host " ERROR" -ForegroundColor Red
    Write-Host "      $($_.Exception.Message)" -ForegroundColor Red
}

# BQI Pattern Learning Status
Write-Host ""
Write-Host "  BQI Learning Status:" -ForegroundColor Cyan
$bqiLogPath = "$agiRoot\outputs\bqi_learner_last_run.txt"
$bqiModelPath = "$agiRoot\outputs\bqi_pattern_model.json"
if (Test-Path $bqiLogPath) {
    try {
        $lastLine = Get-Content -LiteralPath $bqiLogPath -Tail 1 -ErrorAction Stop
        if ($lastLine -match "(\d{4}-\d{2}-\d{2}T[\d:\.+-]+Z?)\s*\|\s*status=(\w+)\s*\|.*prules=(\d+)\s+erules=(\d+)\s+rrules=(\d+)") {
            $ts = $Matches[1]; $st = $Matches[2]; $pr = $Matches[3]; $er = $Matches[4]; $rr = $Matches[5]
            $color = if ($st -eq 'ok') { 'Green' } else { 'Yellow' }
            Write-Host ("    Last Run: {0}" -f $ts) -ForegroundColor White
            Write-Host "    Status:   " -NoNewline
            Write-Host $st.ToUpper() -ForegroundColor $color
            Write-Host ("    Rules:    P:{0} E:{1} R:{2}" -f $pr, $er, $rr) -ForegroundColor White
            # Feedback Predictor (Phase 5) metrics from log, if present
            $mFbS = [regex]::Match($lastLine, "fb_samples=(\\d+)")
            $mFbP = [regex]::Match($lastLine, "fb_patterns=(\\d+)")
            $mFbR = [regex]::Match($lastLine, "fb_rules=(\\d+)")
            if ($mFbS.Success -or $mFbP.Success -or $mFbR.Success) {
                $fbS = if ($mFbS.Success) { $mFbS.Groups[1].Value } else { "0" }
                $fbP = if ($mFbP.Success) { $mFbP.Groups[1].Value } else { "0" }
                $fbR = if ($mFbR.Success) { $mFbR.Groups[1].Value } else { "0" }
                Write-Host ("    Feedback: Samples {0}, Patterns {1}, Rules {2}" -f $fbS, $fbP, $fbR) -ForegroundColor White
            }
        }
        else {
            Write-Host "    Last Run: (unparseable log)" -ForegroundColor DarkGray
        }
    }
    catch {
        Write-Host "    Last Run: (error reading log)" -ForegroundColor DarkGray
    }
}
else {
    Write-Host "    Last Run: (no log yet)" -ForegroundColor DarkGray
}

if (Test-Path $bqiModelPath) {
    try {
        $model = Get-Content -LiteralPath $bqiModelPath -Raw | ConvertFrom-Json
        if ($model.samples_used -ne $null) {
            Write-Host ("    Samples:  {0}" -f $model.samples_used) -ForegroundColor White
        }
    }
    catch { }
}

# Phase 6: Binoche Persona metrics
$personaJsonPath = Join-Path $agiRoot "outputs\binoche_persona.json"
if (Test-Path $personaJsonPath) {
    try {
        $persona = Get-Content -LiteralPath $personaJsonPath -Raw | ConvertFrom-Json
        Write-Host ""
        Write-Host "  Binoche Persona (Phase 6):" -ForegroundColor Cyan
        Write-Host ("    Tasks Analyzed: {0}" -f $persona.stats.total_tasks) -ForegroundColor White
        Write-Host ("    Decisions: {0} (A:{1:P0} R:{2:P0} X:{3:P0})" -f `
                $persona.stats.total_decisions, `
                $persona.stats.approve_rate, `
                $persona.stats.revise_rate, `
                $persona.stats.reject_rate) -ForegroundColor White
        $patternCount = ($persona.bqi_probabilities | Get-Member -MemberType NoteProperty).Count
        Write-Host ("    BQI Patterns: {0}" -f $patternCount) -ForegroundColor White
        Write-Host ("    Automation Rules: {0}" -f $persona.rules.Count) -ForegroundColor White
        
        # Top tech preferences (if any)
        if ($persona.tech_preferences.tech_stack -and ($persona.tech_preferences.tech_stack | Get-Member -MemberType NoteProperty).Count -gt 0) {
            $topTech = $persona.tech_preferences.tech_stack | Get-Member -MemberType NoteProperty | 
            Select-Object -First 3 | ForEach-Object { $_.Name }
            Write-Host ("    Top Tech: {0}" -f ($topTech -join ", ")) -ForegroundColor White
        }
    }
    catch {
        Write-Host ""
        Write-Host "  Binoche Persona: (error reading model)" -ForegroundColor DarkGray
    }
}

Write-Host ""

# ===== Lumen ?�스??=====
Write-Host "[2] Lumen Multi-Channel Gateway" -ForegroundColor Yellow

$prev = if ($LogJsonl) { Read-LastSnapshot -Path $LogPath } else { $null }
$prevLocalMs = $null; $prevCloudMs = $null; $prevGatewayMs = $null
if ($prev -and $prev.Channels) {
    if ($prev.Channels.LocalMs -ne $null) { $prevLocalMs = [int]$prev.Channels.LocalMs }
    if ($prev.Channels.CloudMs -ne $null) { $prevCloudMs = [int]$prev.Channels.CloudMs }
    if ($prev.Channels.GatewayMs -ne $null) { $prevGatewayMs = [int]$prev.Channels.GatewayMs }
}

# Local LLM (primary - 8080)
$localProbe = Test-Endpoint -Url "http://localhost:8080/v1/models" -TimeoutSec 3
Show-LatencyLine -Label "Local LLM (8080)" -Probe $localProbe -WarnMs $WarnLocalMs -AlertMs $AlertLocalMs -PrevMs $prevLocalMs

# Local LLM (secondary - 18090, optional; surface as non-blocking; allow hiding)
$localProbe2 = $null
if (-not $HideOptional) {
    $localProbeJson = "C:\workspace\agi\outputs\local_latency_probe_latest.json"
    if (Test-Path $localProbeJson) {
        try {
            $probeData = Get-Content -LiteralPath $localProbeJson -Raw | ConvertFrom-Json
            $ep18090 = $probeData.endpoints | Where-Object { $_.url -like '*18090*' } | Select-Object -First 1
            if ($ep18090) {
                $isOnline = ($ep18090.success_count -gt 0)
                $avgMs = if ($ep18090.mean_ms) { [int]$ep18090.mean_ms } else { $null }
                $errMsg = if ($ep18090.errors -and $ep18090.errors.Count -gt 0) { $ep18090.errors[0] } else { $null }
                $localProbe2 = @{ Online = $isOnline; Ms = $avgMs; Code = 200; Error = $errMsg }
                $labelOpt = "Local LLM (18090) (optional)"
                if ($localProbe2.Online) {
                    Show-LatencyLine -Label $labelOpt -Probe $localProbe2 -WarnMs $WarnLocalMs -AlertMs $AlertLocalMs
                }
                else {
                    # Render as non-blocking offline without noisy error stack
                    Write-Host ("    {0,-24} " -f $labelOpt) -NoNewline
                    Write-Host " OFFLINE (optional)" -ForegroundColor DarkGray
                }
            }
        }
        catch { }
    }
}

# Cloud AI
$cloudProbe = Test-Endpoint -Url "https://ion-api-64076350717.us-central1.run.app/chat" -Method POST -BodyJson '{"message":"ping"}' -TimeoutSec 5
Show-LatencyLine -Label "Cloud AI (ion-api)" -Probe $cloudProbe -WarnMs $WarnCloudMs -AlertMs $AlertCloudMs -PrevMs $prevCloudMs

# Lumen Gateway
$gwProbe = Test-Endpoint -Url "https://lumen-gateway-x4qvsargwa-uc.a.run.app/chat" -Method POST -BodyJson '{"message":"ping"}' -TimeoutSec 5
Show-LatencyLine -Label "Lumen Gateway" -Probe $gwProbe -WarnMs $WarnGatewayMs -AlertMs $AlertGatewayMs -PrevMs $prevGatewayMs

# ===== Trend Analytics =====
$recent = Read-RecentSnapshots -Path $LogPath -MaxCount $TrendWindow
$recentLong = Read-RecentSnapshots -Path $LogPath -MaxCount $LongTrendWindow

function _ComputeStats([double[]]$arr) {
    $res = @{ Count = 0; Mean = $null; Std = $null }
    if ($null -eq $arr -or $arr.Count -lt 1) { return $res }
    $n = [double]$arr.Count
    $mean = ($arr | Measure-Object -Average).Average
    if ($n -gt 1) {
        $sumSq = 0.0
        foreach ($v in $arr) { $sumSq += [math]::Pow(($v - $mean), 2) }
        # sample std (n-1)
        $std = [math]::Sqrt($sumSq / ($n - 1.0))
    }
    else { $std = 0.0 }
    return @{ Count = [int]$n; Mean = [double]$mean; Std = [double]$std }
}

function Get-TrendDirection([double]$shortMean, [double]$longMean, [double]$thresholdPercent) {
    if ($null -eq $shortMean -or $null -eq $longMean) { return "UNKNOWN" }
    $threshold = $longMean * ($thresholdPercent / 100.0)
    $diff = $shortMean - $longMean
    # Latency is better when lower: invert semantics
    if ($diff -lt - $threshold) { return "IMPROVING" }
    elseif ($diff -gt $threshold) { return "DEGRADING" }
    else { return "STABLE" }
}

function Get-TrendArrow([string]$direction) {
    switch ($direction) {
        "IMPROVING" { return "++"; }
        "DEGRADING" { return "--"; }
        "STABLE" { return "=="; }
        default { return "??"; }
    }
}

$localVals = @(); $cloudVals = @(); $gwVals = @();
foreach ($r in $recent) {
    try { if ($r.Channels.LocalMs -ne $null -and [int]$r.Channels.LocalMs -gt 0) { $localVals += [double]$r.Channels.LocalMs } } catch {}
    try { if ($r.Channels.CloudMs -ne $null -and [int]$r.Channels.CloudMs -gt 0) { $cloudVals += [double]$r.Channels.CloudMs } } catch {}
    try { if ($r.Channels.GatewayMs -ne $null -and [int]$r.Channels.GatewayMs -gt 0) { $gwVals += [double]$r.Channels.GatewayMs } } catch {}
}
$statLocal = _ComputeStats($localVals)
$statCloud = _ComputeStats($cloudVals)
$statGateway = _ComputeStats($gwVals)

# Long-term trend (if enough data)
$localValsLong = @(); $cloudValsLong = @(); $gwValsLong = @();
foreach ($r in $recentLong) {
    try { if ($r.Channels.LocalMs -ne $null -and [int]$r.Channels.LocalMs -gt 0) { $localValsLong += [double]$r.Channels.LocalMs } } catch {}
    try { if ($r.Channels.CloudMs -ne $null -and [int]$r.Channels.CloudMs -gt 0) { $cloudValsLong += [double]$r.Channels.CloudMs } } catch {}
    try { if ($r.Channels.GatewayMs -ne $null -and [int]$r.Channels.GatewayMs -gt 0) { $gwValsLong += [double]$r.Channels.GatewayMs } } catch {}
}
$statLocalLong = _ComputeStats($localValsLong)
$statCloudLong = _ComputeStats($cloudValsLong)
$statGatewayLong = _ComputeStats($gwValsLong)

# Determine trend direction
$dirLocal = Get-TrendDirection -shortMean $statLocal.Mean -longMean $statLocalLong.Mean -thresholdPercent $TrendThresholdPercent
$dirCloud = Get-TrendDirection -shortMean $statCloud.Mean -longMean $statCloudLong.Mean -thresholdPercent $TrendThresholdPercent
$dirGateway = Get-TrendDirection -shortMean $statGateway.Mean -longMean $statGatewayLong.Mean -thresholdPercent $TrendThresholdPercent

$trend = @{ 
    Local   = @{ 
        ShortTermMeanMs = $statLocal.Mean
        LongTermMeanMs  = $statLocalLong.Mean
        StdMs           = $statLocal.Std
        Count           = $statLocal.Count
        LongCount       = $statLocalLong.Count
        Direction       = $dirLocal
        PrevMs          = $prevLocalMs 
    }
    Cloud   = @{ 
        ShortTermMeanMs = $statCloud.Mean
        LongTermMeanMs  = $statCloudLong.Mean
        StdMs           = $statCloud.Std
        Count           = $statCloud.Count
        LongCount       = $statCloudLong.Count
        Direction       = $dirCloud
        PrevMs          = $prevCloudMs 
    }
    Gateway = @{ 
        ShortTermMeanMs = $statGateway.Mean
        LongTermMeanMs  = $statGatewayLong.Mean
        StdMs           = $statGateway.Std
        Count           = $statGateway.Count
        LongCount       = $statGatewayLong.Count
        Direction       = $dirGateway
        PrevMs          = $prevGatewayMs 
    }
}

# Display trend summary if we have data
if ($statLocal.Count -gt 0 -or $statCloud.Count -gt 0 -or $statGateway.Count -gt 0) {
    Write-Host ""
    Write-Host "    Trend Summary (short=$TrendWindow, long=$LongTrendWindow samples):" -ForegroundColor DarkCyan
    $parts = @()
    if ($statLocal.Count -gt 0) {
        $arrow = Get-TrendArrow -direction $dirLocal
        $longInfo = if ($statLocalLong.Count -ge $LongTrendWindow) { " $arrow" } else { "" }
        $parts += ("Local avg {0}ms (+/- {1}){2}" -f [int]$statLocal.Mean, [int]$statLocal.Std, $longInfo)
    }
    if ($statCloud.Count -gt 0) {
        $arrow = Get-TrendArrow -direction $dirCloud
        $longInfo = if ($statCloudLong.Count -ge $LongTrendWindow) { " $arrow" } else { "" }
        $parts += ("Cloud avg {0}ms (+/- {1}){2}" -f [int]$statCloud.Mean, [int]$statCloud.Std, $longInfo)
    }
    if ($statGateway.Count -gt 0) {
        $arrow = Get-TrendArrow -direction $dirGateway
        $longInfo = if ($statGatewayLong.Count -ge $LongTrendWindow) { " $arrow" } else { "" }
        $parts += ("Gateway avg {0}ms (+/- {1}){2}" -f [int]$statGateway.Mean, [int]$statGateway.Std, $longInfo)
    }
    Write-Host ("      " + ($parts -join " | ")) -ForegroundColor DarkGray
}

# ===== Summary & Export =====
$issues = @()
$warnings = @()

if (-not $localProbe.Online) { $issues += "Local LLM offline ($($localProbe.Code))" }
elseif ($localProbe.Ms -ge $AlertLocalMs) { $issues += "ALERT: Local LLM latency $($localProbe.Ms)ms" }
elseif ($localProbe.Ms -ge $WarnLocalMs) { $warnings += "WARN: Local LLM latency $($localProbe.Ms)ms" }

if (-not $cloudProbe.Online) { $issues += "Cloud AI offline ($($cloudProbe.Code))" }
elseif ($cloudProbe.Ms -ge $AlertCloudMs) { $issues += "ALERT: Cloud AI latency $($cloudProbe.Ms)ms" }
elseif ($cloudProbe.Ms -ge $WarnCloudMs) { $warnings += "WARN: Cloud AI latency $($cloudProbe.Ms)ms" }

if (-not $gwProbe.Online) { $issues += "Lumen Gateway offline ($($gwProbe.Code))" }
elseif ($gwProbe.Ms -ge $AlertGatewayMs) { $issues += "ALERT: Lumen Gateway latency $($gwProbe.Ms)ms" }
elseif ($gwProbe.Ms -ge $WarnGatewayMs) { $warnings += "WARN: Lumen Gateway latency $($gwProbe.Ms)ms" }

# Baseline detection using long-term mean (sustained high latency)
function Add-BaselineMsg {
    param(
        [string]$name,
        [double]$longMean,
        [int]$longCount,
        [int]$warnMs,
        [int]$alertMs,
        [ref]$issuesRef,
        [ref]$warningsRef,
        [string[]]$existingMsgs
    )
    if ($longCount -lt [Math]::Max(5, [int]($LongTrendWindow / 2))) { return }
    $hasCurrentAlert = $existingMsgs | Where-Object { $_ -like "ALERT: $name*" } | Select-Object -First 1
    if ($longMean -ge $alertMs -and -not $hasCurrentAlert) {
        $issuesRef.Value += "BASELINE ALERT: $name sustained latency $([int]$longMean)ms (avg over $longCount samples)"
    }
    elseif ($longMean -ge $warnMs -and -not $hasCurrentAlert) {
        $warningsRef.Value += "BASELINE WARN: $name sustained latency $([int]$longMean)ms (avg over $longCount samples)"
    }
}

Add-BaselineMsg -name 'Local LLM' -longMean $statLocalLong.Mean -longCount $statLocalLong.Count -warnMs $WarnLocalMs -alertMs $AlertLocalMs -issuesRef ([ref]$issues) -warningsRef ([ref]$warnings) -existingMsgs $issues
Add-BaselineMsg -name 'Cloud AI' -longMean $statCloudLong.Mean -longCount $statCloudLong.Count -warnMs $WarnCloudMs -alertMs $AlertCloudMs -issuesRef ([ref]$issues) -warningsRef ([ref]$warnings) -existingMsgs $issues
Add-BaselineMsg -name 'Lumen Gateway' -longMean $statGatewayLong.Mean -longCount $statGatewayLong.Count -warnMs $WarnGatewayMs -alertMs $AlertGatewayMs -issuesRef ([ref]$issues) -warningsRef ([ref]$warnings) -existingMsgs $issues

# Spike detection vs moving average (if enough history and current online)
if ($statLocal.Count -ge [Math]::Max(5, [int]$TrendWindow / 2) -and $localProbe.Online -and $localProbe.Ms -gt 0 -and $statLocal.Std -gt 0) {
    $thr = $statLocal.Mean + ($SpikeSigma * $statLocal.Std)
    if ($localProbe.Ms -gt [int]$thr) { $warnings += "SPIKE: Local LLM latency $($localProbe.Ms)ms (avg $([int]$statLocal.Mean) +/- $([int]$statLocal.Std))" }
}
if ($statCloud.Count -ge [Math]::Max(5, [int]$TrendWindow / 2) -and $cloudProbe.Online -and $cloudProbe.Ms -gt 0 -and $statCloud.Std -gt 0) {
    $thr = $statCloud.Mean + ($SpikeSigma * $statCloud.Std)
    if ($cloudProbe.Ms -gt [int]$thr) { $warnings += "SPIKE: Cloud AI latency $($cloudProbe.Ms)ms (avg $([int]$statCloud.Mean) +/- $([int]$statCloud.Std))" }
}
if ($statGateway.Count -ge [Math]::Max(5, [int]$TrendWindow / 2) -and $gwProbe.Online -and $gwProbe.Ms -gt 0 -and $statGateway.Std -gt 0) {
    $thr = $statGateway.Mean + ($SpikeSigma * $statGateway.Std)
    if ($gwProbe.Ms -gt [int]$thr) { $warnings += "SPIKE: Gateway latency $($gwProbe.Ms)ms (avg $([int]$statGateway.Mean) +/- $([int]$statGateway.Std))" }
}

# Adaptive thresholding (optional)
function Add-AdaptiveAlerts {
    param(
        [string]$name,
        [double]$currentMs,
        [bool]$online,
        [hashtable]$stat,
        [ref]$issuesRef,
        [ref]$warningsRef
    )
    if (-not $UseAdaptiveThresholds) { return }
    if (-not $online -or $currentMs -le 0) { return }
    if ($stat.Count -lt [Math]::Max(5, [int]($TrendWindow / 2)) -or $stat.Std -le 0) { return }
    $warnThr = $stat.Mean + ($AdaptiveWarnSigmas * $stat.Std)
    $alertThr = $stat.Mean + ($AdaptiveAlertSigmas * $stat.Std)
    if ($currentMs -ge [int]$alertThr) {
        $issuesRef.Value += "ADAPTIVE ALERT: $name latency $([int]$currentMs)ms (thr $([int]$alertThr) = avg $([int]$stat.Mean) + ${AdaptiveAlertSigmas} sig $([int]$stat.Std))"
    }
    elseif ($currentMs -ge [int]$warnThr) {
        $warningsRef.Value += "ADAPTIVE WARN: $name latency $([int]$currentMs)ms (thr $([int]$warnThr) = avg $([int]$stat.Mean) + ${AdaptiveWarnSigmas} sig $([int]$stat.Std))"
    }
}

Add-AdaptiveAlerts -name 'Local LLM' -currentMs $localProbe.Ms -online $localProbe.Online -stat $statLocal -issuesRef ([ref]$issues) -warningsRef ([ref]$warnings)
Add-AdaptiveAlerts -name 'Cloud AI' -currentMs $cloudProbe.Ms -online $cloudProbe.Online -stat $statCloud -issuesRef ([ref]$issues) -warningsRef ([ref]$warnings)
Add-AdaptiveAlerts -name 'Lumen Gateway' -currentMs $gwProbe.Ms -online $gwProbe.Online -stat $statGateway -issuesRef ([ref]$issues) -warningsRef ([ref]$warnings)

$hasAlerts = ($issues | Where-Object { $_ -like 'ALERT*' -or $_ -like '*offline*' }).Count -gt 0
$hasWarns = $warnings.Count -gt 0
$allGreen = (-not $hasAlerts -and -not $hasWarns)

Write-Host ""; Write-Host "----------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "Summary: " -NoNewline
if ($allGreen) { Write-Host "ALL GREEN - all systems OK" -ForegroundColor Green }
elseif ($hasAlerts) { Write-Host "ATTENTION - issues detected" -ForegroundColor Yellow }
else { Write-Host "WARNING - latency thresholds exceeded" -ForegroundColor Yellow }

if ($hasAlerts) { Write-Host "Issues:" -ForegroundColor Red; foreach ($i in $issues) { Write-Host "  - $i" -ForegroundColor Red } }
if ($hasWarns) { Write-Host "Warnings:" -ForegroundColor Yellow; foreach ($w in $warnings) { Write-Host "  - $w" -ForegroundColor Yellow } }

$snapshot = @{
    Timestamp = (Get-Date).ToString('s')
    Channels  = @{ 
        LocalMs   = $localProbe.Ms
        Local2Ms  = if ($localProbe2) { $localProbe2.Ms } else { $null }
        CloudMs   = $cloudProbe.Ms
        GatewayMs = $gwProbe.Ms 
    }
    Online    = @{ 
        Local   = $localProbe.Online
        Local2  = if ($localProbe2) { $localProbe2.Online } else { $false }
        Cloud   = $cloudProbe.Online
        Gateway = $gwProbe.Online 
    }
    Trend     = $trend
    Issues    = $issues
    Warnings  = $warnings
}

if ($OutJson) {
    try {
        $outPathResolved = $null
        try { $rp = Resolve-Path -LiteralPath $OutJson -ErrorAction Stop; if ($rp -and $rp.Path) { $outPathResolved = $rp.Path } } catch { }
        $outPathFinal = if ($outPathResolved) { $outPathResolved } else { $OutJson }
        $dir = Split-Path -Parent $outPathFinal
        if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
        [IO.File]::WriteAllText($outPathFinal, ($snapshot | ConvertTo-Json -Compress), [Text.Encoding]::UTF8)
    }
    catch { }
}
if ($LogJsonl) { Append-Snapshot -Path $LogPath -Snapshot $snapshot }

$summary = @{
    AllGreen   = $allGreen
    IsDegraded = $hasAlerts
    HasWarns   = $hasWarns
    Issues     = $issues
    Warnings   = $warnings
}

if ($AlertOnDegraded -and (-not $allGreen)) { Send-AlertIfNeeded -Summary $summary -Trend $trend }

if ($Perf) {
    Write-Host ""; Show-PerfSummary; Write-Host ""
}

# Emit health check event (best-effort)
try {
    $emitPath = Join-Path $PSScriptRoot 'emit_event.ps1'
    if (Test-Path -LiteralPath $emitPath) {
        & $emitPath -EventType "health_check" -Payload @{
            status           = if ($allGreen) { "HEALTHY" } else { "UNHEALTHY" }
            all_green        = $allGreen
            has_alerts       = $hasAlerts
            has_warnings     = $hasWarns
            agi_confidence   = $agiMetrics.confidence
            agi_quality      = $agiMetrics.quality
            agi_second_pass  = $agiMetrics.second_pass_rate
            lumen_latency_ms = $gwProbe.Ms
            timestamp        = (Get-Date).ToUniversalTime().ToString("o")
        } -PersonaId "monitoring"
    }
}
catch {}

Write-Host "`n================================================================`n" -ForegroundColor Cyan

# ensure non-zero exit codes from native commands do not bubble up
$global:LASTEXITCODE = 0
