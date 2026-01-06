# Generate Monitoring Report: Comprehensive AGI + Core analytics
#
# QUICK USAGE:
#   generate_monitoring_report.ps1 -Hours 24        # last 24h
#   generate_monitoring_report.ps1 -Hours 168       # last week
#
# SECTIONS INDEX:
#   - Parameters (line 1-20)
#   - Threshold Config (line 25-80)
#   - AGI Ledger Parsing (line 85-500)
#   - Core Analysis (line 500-1000)
#   - Report Generation (line 1000-2000)
#   - HTML Dashboard (line 2000+)

param(
    [int]$Hours = 24,
    [string]$LogPath = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\status_snapshots.jsonl",
    [string]$OutMarkdown = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\monitoring_report_latest.md",
    [string]$OutJson = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\monitoring_metrics_latest.json",
    [string]$OutCsv = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\monitoring_timeseries_latest.csv",
    [switch]$SkipCsv,
    [string]$OutEventsCsv = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\monitoring_events_latest.csv",
    [switch]$SkipEvents,
    [string]$OutHtml = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\monitoring_dashboard_latest.html",
    [switch]$SkipHtml,
    [string]$ThresholdConfigPath = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\config\monitoring_thresholds.json",
    [int]$PeakStart = 9,
    [int]$PeakEnd = 18,
    [int]$SparklineLen = 30
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::UTF8; $OutputEncoding = [System.Text.UTF8Encoding]::UTF8 } catch {}

$ErrorActionPreference = "Continue"

# ========================================
# AGI Ledger Parsing Functions
# ========================================
function Load-ThresholdConfig {
    param(
        [string]$Path = $ThresholdConfigPath
    )

    $defaults = @{
        AGI = @{
            thresholds = @{
                min_quality                  = 0.6
                min_confidence               = 0.6
                min_success_rate_percent     = 70
                replan_rate_percent          = 10
                max_avg_duration_sec         = 10
                inactive_hours               = 2
                evidence_forced_warn_percent = 70
                evidence_forced_crit_percent = 50
                evidence_forced_ma_window    = 5
                persona                      = @{
                    low_success_warn_percent = 60
                    low_success_crit_percent = 50
                    slow_duration_sec        = 10
                }
            }
        }
    }

    try {
        if (Test-Path -LiteralPath $Path) {
            $json = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json -ErrorAction Stop
            return $json
        }
        else {
            $dir = Split-Path -Parent $Path
            if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
            return $defaults | ConvertTo-Json -Depth 6 | ConvertFrom-Json
        }
    }
    catch {
        Write-Host "Warning: Failed to load threshold config: $($_.Exception.Message). Using defaults." -ForegroundColor Yellow
        return $defaults | ConvertTo-Json -Depth 6 | ConvertFrom-Json
    }
}
function Parse-AGILedger {
    param(
        [string]$Path = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\fdo_agi_repo\memory\resonance_ledger.jsonl",
        [datetime]$Since
    )
    
    $events = @()
    try {
        if (-not (Test-Path $Path)) {
            Write-Host "Warning: AGI Ledger not found at $Path" -ForegroundColor Yellow
            return @()
        }
        
        $lines = Get-Content -LiteralPath $Path -ErrorAction Stop
        foreach ($line in $lines) {
            try {
                if ([string]::IsNullOrWhiteSpace($line)) { continue }
                $obj = $line | ConvertFrom-Json -ErrorAction Stop
                
                # Parse timestamp (Unix timestamp)
                if ($obj.ts) {
                    $unixEpoch = [datetime]::new(1970, 1, 1, 0, 0, 0, 0, [System.DateTimeKind]::Utc)
                    $ts = $unixEpoch.AddSeconds($obj.ts).ToLocalTime()
                    
                    if ($ts -ge $Since) {
                        $obj | Add-Member -NotePropertyName "ParsedTimestamp" -NotePropertyValue $ts -Force
                        $events += $obj
                    }
                }
            }
            catch { }
        }
    }
    catch {
        Write-Host "Error reading AGI Ledger: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    return $events
}

function Compute-AGIMetrics {
    param([object[]]$Events)
    
    $metrics = @{
        TotalEvents        = $Events.Count
        EventTypes         = @{}
        TaskCount          = 0
        AvgQuality         = $null
        AvgDuration        = $null
        SuccessRate        = $null
        ReplanRate         = $null
        LastActivity       = $null
        EvidenceCorrection = @{}
    }
    
    if ($Events.Count -eq 0) { return $metrics }
    
    # Count event types
    $eventTypeGroups = $Events | Group-Object -Property event
    foreach ($group in $eventTypeGroups) {
        $metrics.EventTypes[$group.Name] = $group.Count
    }
    
    # Extract unique tasks
    $uniqueTasks = $Events | Where-Object { $_.task_id } | Select-Object -ExpandProperty task_id -Unique
    $metrics.TaskCount = $uniqueTasks.Count
    
    # Calculate quality metrics
    $evalEvents = $Events | Where-Object { $_.event -eq "eval" -and $null -ne $_.quality }
    if ($evalEvents.Count -gt 0) {
        $metrics.AvgQuality = [math]::Round(($evalEvents | Measure-Object -Property quality -Average).Average, 2)
    }
    
    # Calculate duration metrics
    $durationEvents = $Events | Where-Object { $_.event -eq "synthesis_end" -and $_.duration_sec }
    if ($durationEvents.Count -gt 0) {
        $metrics.AvgDuration = [math]::Round(($durationEvents | Measure-Object -Property duration_sec -Average).Average, 2)
    }
    
    # Calculate success rate (quality >= 0.7)
    if ($evalEvents.Count -gt 0) {
        $successCount = ($evalEvents | Where-Object { $_.quality -ge 0.7 }).Count
        $metrics.SuccessRate = [math]::Round(($successCount / $evalEvents.Count) * 100, 2)
    }
    
    # Calculate replan rate
    $runeEvents = $Events | Where-Object { $_.event -eq "rune" -and $null -ne $_.rune.replan }
    if ($runeEvents.Count -gt 0) {
        $replanCount = ($runeEvents | Where-Object { $_.rune.replan -eq $true }).Count
        $metrics.ReplanRate = [math]::Round(($replanCount / $runeEvents.Count) * 100, 2)
    }
    
    # Last activity timestamp
    $sortedEvents = $Events | Sort-Object -Property ParsedTimestamp -Descending
    if ($sortedEvents.Count -gt 0) {
        $metrics.LastActivity = $sortedEvents[0].ParsedTimestamp
    }

    # Evidence correction aggregation (fallback path)
    try {
        $ecEvents = $Events | Where-Object { $_.event -eq 'evidence_correction' }
        $attempts = $ecEvents.Count
        if ($attempts -gt 0) {
            # Collect numeric arrays safely
            $hitsArr = @()
            $addedArr = @()
            $relArr = @()
            $fallbacks = 0
            $retries = 0
            $synthetics = 0

            foreach ($e in $ecEvents) {
                if ($null -ne $e.hits -and ($e.hits -is [int] -or $e.hits -is [double])) { $hitsArr += [double]$e.hits }
                if ($null -ne $e.added -and ($e.added -is [int] -or $e.added -is [double])) { $addedArr += [double]$e.added }
                if ($null -ne $e.avg_relevance -and ($e.avg_relevance -is [int] -or $e.avg_relevance -is [double])) { $relArr += [double]$e.avg_relevance }
                if ($e.fallback_used) { $fallbacks += 1 }
                if ($e.retry_broaden_used) { $retries += 1 }
                if ($e.synthetic_used) { $synthetics += 1 }
            }

            function _avg([double[]]$arr) { if ($arr -and $arr.Count -gt 0) { ([double]($arr | Measure-Object -Average).Average) } else { 0.0 } }
            $avgHits = _avg $hitsArr
            $avgAdded = _avg $addedArr
            $avgRel = _avg $relArr
            $successRate = if ($hitsArr.Count -gt 0) { ([double](($hitsArr | Where-Object { $_ -gt 0 }).Count) / [double]$hitsArr.Count) } else { 0.0 }
            $fallbackRate = if ($attempts -gt 0) { [double]$fallbacks / [double]$attempts } else { 0.0 }
            $retryRate = if ($attempts -gt 0) { [double]$retries / [double]$attempts } else { 0.0 }
            $syntheticRate = if ($attempts -gt 0) { [double]$synthetics / [double]$attempts } else { 0.0 }

            # Forced-only aggregation
            $forcedEvents = $ecEvents | Where-Object { $_.forced }
            $forcedAttempts = if ($null -eq $forcedEvents) { 0 } else { [int]$forcedEvents.Count }
            $forcedHitsArr = @()
            $forcedAddedArr = @()
            if ($forcedAttempts -gt 0) {
                foreach ($fe in $forcedEvents) {
                    if ($null -ne $fe.hits -and ($fe.hits -is [int] -or $fe.hits -is [double])) { $forcedHitsArr += [double]$fe.hits }
                    if ($null -ne $fe.added -and ($fe.added -is [int] -or $fe.added -is [double])) { $forcedAddedArr += [double]$fe.added }
                }
            }
            $forcedAvgHits = _avg $forcedHitsArr
            $forcedAvgAdded = _avg $forcedAddedArr
            $forcedSuccessRate = if ($forcedHitsArr.Count -gt 0) { ([double](($forcedHitsArr | Where-Object { $_ -gt 0 }).Count) / [double]$forcedHitsArr.Count) } else { 0.0 }

            $metrics.EvidenceCorrection = @{
                attempts                 = $attempts
                avg_hits                 = [math]::Round($avgHits, 2)
                avg_added                = [math]::Round($avgAdded, 2)
                avg_relevance            = [math]::Round($avgRel, 3)
                success_rate             = [math]::Round($successRate, 3)
                fallback_rate            = [math]::Round($fallbackRate, 3)
                retry_rate               = [math]::Round($retryRate, 3)
                synthetic_rate           = [math]::Round($syntheticRate, 3)
                forced_attempts          = $forcedAttempts
                forced_avg_hits          = [math]::Round($forcedAvgHits, 2)
                forced_avg_added         = [math]::Round($forcedAvgAdded, 2)
                forced_success_rate      = [math]::Round($forcedSuccessRate, 3)
                forced_success_sparkline = @()
                forced_samples           = @()
            }

            # Build forced success sparkline (0/1 over last N events, oldest->newest)
            try {
                $sparkLen = if ($script:SparklineLen) { [int]$script:SparklineLen } else { 30 }
                if ($forcedAttempts -gt 0) {
                    $orderedForced = $forcedEvents | Sort-Object -Property ParsedTimestamp
                    $tail = $orderedForced | Select-Object -Last $sparkLen
                    $spark = @()
                    foreach ($ev in $tail) {
                        $val = 0
                        try { if ($null -ne $ev.hits -and [double]$ev.hits -gt 0) { $val = 1 } } catch { $val = 0 }
                        $spark += $val
                    }
                    $metrics.EvidenceCorrection.forced_success_sparkline = $spark
                }
            }
            catch { }

            # Collect recent forced samples (latest 10)
            try {
                if ($forcedAttempts -gt 0) {
                    $recent = ($forcedEvents | Sort-Object -Property ParsedTimestamp -Descending) | Select-Object -First 10
                    $samples = @()
                    foreach ($ev in $recent) {
                        $tsOut = $null
                        try { $tsOut = $ev.ParsedTimestamp.ToString('s') } catch { $tsOut = $null }
                        $hitsOut = $null; $addedOut = $null; $relOut = $null; $succOut = $null; $fbOut = $false
                        try { if ($null -ne $ev.hits) { $hitsOut = [double]$ev.hits } } catch { $hitsOut = $null }
                        try { if ($null -ne $ev.added) { $addedOut = [double]$ev.added } } catch { $addedOut = $null }
                        try { if ($null -ne $ev.avg_relevance) { $relOut = [double]$ev.avg_relevance } } catch { $relOut = $null }
                        try { $succOut = ($hitsOut -ne $null -and $hitsOut -gt 0) } catch { $succOut = $false }
                        try { if ($ev.fallback_used) { $fbOut = $true } } catch { $fbOut = $false }
                        $samples += @{
                            time          = $tsOut
                            hits          = $hitsOut
                            added         = $addedOut
                            avg_relevance = $relOut
                            success       = $succOut
                            fallback      = $fbOut
                        }
                    }
                    $metrics.EvidenceCorrection.forced_samples = $samples
                }
            }
            catch { }
        }
    }
    catch {
        # Keep EvidenceCorrection empty on any parsing error
        $metrics.EvidenceCorrection = @{}
    }
    
    return $metrics
}

function Set-ObjectPropertySafe {
    param(
        [Parameter(Mandatory = $true)]$Object,
        [Parameter(Mandatory = $true)][string]$Name,
        $Value
    )
    try {
        if ($null -eq $Object) { return }
        if ($Object -is [hashtable]) {
            $Object[$Name] = $Value
            return
        }
        # PSCustomObject or other .NET object with PSObject
        $props = $Object.PSObject.Properties
        if ($props -and ($props.Name -contains $Name)) {
            # Set existing property
            try { $Object.$Name = $Value } catch { }
        }
        else {
            # Add as NoteProperty
            $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force
        }
    }
    catch { }
}

function Get-SessionSummaryContent {
    param(
        [string]$SessionId,
        [object]$Entry
    )

    try {
        $filePath = $Entry.file_path
        if (-not $filePath -or -not (Test-Path -LiteralPath $filePath)) {
            return $null
        }

        $lines = Get-Content -LiteralPath $filePath -Encoding UTF8
        foreach ($line in $lines) {
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            $obj = $line | ConvertFrom-Json -ErrorAction Stop
            if ($obj.session_id -eq $SessionId) {
                return $obj
            }
        }
    }
    catch {
        # swallow and return null
    }
    return $null
}

function Get-SessionSummaryMetrics {
    param(
        [string]$IndexPath,
        [int]$RecentLimit = 5
    )

    $result = @{
        Available         = $false
        TotalSessions     = 0
        LlmSessions       = 0
        RuleSessions      = 0
        Recent24h         = 0
        Embeddings        = 0
        EmbeddingCoverage = 0
        LastUpdated       = $null
        IndexPath         = $IndexPath
        RecentSessions    = @()
    }

    if (-not (Test-Path -LiteralPath $IndexPath)) {
        return $result
    }

    try {
        $raw = Get-Content -LiteralPath $IndexPath -Raw -Encoding UTF8
        if ([string]::IsNullOrWhiteSpace($raw)) {
            return $result
        }

        $json = $raw | ConvertFrom-Json -ErrorAction Stop
        $entries = @()
        foreach ($prop in $json.PSObject.Properties) {
            $value = $prop.Value
            if (-not $value) { continue }
            $value | Add-Member -NotePropertyName "session_id" -NotePropertyValue $prop.Name -Force
            $entries += $value
        }

        if (-not $entries) {
            return $result
        }

        foreach ($entry in $entries) {
            $createdDt = $null
            if ($entry.created_at) {
                try { $createdDt = [datetime]$entry.created_at }
                catch { $createdDt = $null }
            }
            $entry | Add-Member -NotePropertyName "created_dt" -NotePropertyValue $createdDt -Force
        }

        $result.Available = $true
        $result.TotalSessions = $entries.Count
        $result.LlmSessions = ($entries | Where-Object { $_.summary_type -eq "llm" }).Count
        $result.RuleSessions = ($entries | Where-Object { $_.summary_type -eq "rule_based" }).Count
        $result.Embeddings = ($entries | Where-Object { $_.embedding_path }).Count

        # Write optional channels CSV (non-breaking): include only when Local2 present
        if ($hasLocal2) {
            $optCsvLines = @("Timestamp,Local2Ms,Local2Online")
            foreach ($snap in $snapshots) {
                $ts2 = $snap.Timestamp
                $l2ms = if ($snap.Channels -and $null -ne $snap.Channels.Local2Ms) { $snap.Channels.Local2Ms } else { "" }
                $l2on = if ($snap.Online -and $snap.Online.Local2) { "1" } else { "0" }
                $optCsvLines += "$ts2,$l2ms,$l2on"
            }
            $optCsv = $optCsvLines -join "`r`n"
            $optCsvPath = Join-Path $csvDir "monitoring_timeseries_optional_latest.csv"
            [System.IO.File]::WriteAllText($optCsvPath, $optCsv, [System.Text.Encoding]::UTF8)
            Write-Host "Optional CSV written to: $optCsvPath" -ForegroundColor Green
        }
        if ($result.TotalSessions -gt 0) {
            $result.EmbeddingCoverage = [math]::Round(($result.Embeddings / $result.TotalSessions) * 100, 1)
        }

        $cutoff = (Get-Date).AddHours(-24)
        $result.Recent24h = (
            $entries | Where-Object { $_.created_dt -and $_.created_dt -ge $cutoff }
        ).Count

        $ordered = $entries | Sort-Object -Property created_dt -Descending
        $latestEntry = $ordered | Where-Object { $_.created_dt } | Select-Object -First 1
        if ($latestEntry) {
            $result.LastUpdated = $latestEntry.created_dt.ToString("s")
        }

        $recent = @()
        foreach ($entry in $ordered | Select-Object -First $RecentLimit) {
            $content = Get-SessionSummaryContent -SessionId $entry.session_id -Entry $entry
            $preview = $null
            if ($content -and $content.summary) {
                $text = [string]$content.summary
                $preview = if ($text.Length -gt 140) { $text.Substring(0, 140) + "..." } else { $text }
            }
            $recent += @{
                session_id     = $entry.session_id
                user_id        = $entry.user_id
                created_at     = $entry.created_at
                summary_type   = $entry.summary_type
                message_count  = $entry.message_count
                embedding_dims = $entry.embedding_dims
                preview        = $preview
            }
        }
        $result.RecentSessions = $recent
    }
    catch {
        Write-Host "Warning: Failed to aggregate session summaries: $($_.Exception.Message)" -ForegroundColor Yellow
    }

    return $result
}

function Get-AGIMetricsFromPython {
    param(
        [double]$Hours = 1.0,
        [string]$PythonExe = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\fdo_agi_repo\.venv\Scripts\python.exe",
        [string]$DashboardScript = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\fdo_agi_repo\scripts\ops_dashboard.py"
    )
    
    try {
        # Python ?�크립트 ?�행?�여 JSON 출력 받기
        if (-not (Test-Path $PythonExe)) {
            Write-Host "Warning: Python executable not found at $PythonExe" -ForegroundColor Yellow
            return $null
        }
        
        if (-not (Test-Path $DashboardScript)) {
            Write-Host "Warning: Dashboard script not found at $DashboardScript" -ForegroundColor Yellow
            return $null
        }
        
        # UTF-8 ?�코???�정 (Windows CP949 문제 ?�결)
        $originalEncoding = $env:PYTHONIOENCODING
        $env:PYTHONIOENCODING = 'utf-8'
        
        try {
            # stdout�?stderr 분리?�여 JSON 출력�?캡처
            $output = & $PythonExe $DashboardScript --hours $Hours --json 2>&1
            $exitCode = $LASTEXITCODE
            
            # 문자?�만 ?�터링하�?JSON ?�작?�는 �?�?찾기
            $jsonLines = @()
            $inJson = $false
            foreach ($line in $output) {
                if ($line -is [string]) {
                    if ($line.Trim().StartsWith("{")) {
                        $inJson = $true
                    }
                    if ($inJson) {
                        $jsonLines += $line
                    }
                }
            }
            
            if ($jsonLines.Count -eq 0) {
                Write-Host "Warning: No JSON output from Python collector" -ForegroundColor Yellow
                # ?�버깅을 ?�해 �?5�?출력
                $output | Select-Object -First 5 | ForEach-Object { 
                    Write-Host "  Debug output: $_" -ForegroundColor Gray 
                }
                return $null
            }
            
            $jsonString = $jsonLines -join "`n"
            $result = $jsonString | ConvertFrom-Json
            return $result
        }
        finally {
            # ?�코??복원
            if ($originalEncoding) {
                $env:PYTHONIOENCODING = $originalEncoding
            }
            else {
                Remove-Item Env:\PYTHONIOENCODING -ErrorAction SilentlyContinue
            }
        }
    }
    catch {
        Write-Host "Warning: Failed to get AGI metrics from Python: $($_.Exception.Message)" -ForegroundColor Yellow
        return $null
    }
}
function Parse-Snapshots {
    param(
        [string]$Path, 
        [datetime]$Since,
        [datetime]$Until = [datetime]::MaxValue
    )
    $snapshots = @()
    try {
        if (-not (Test-Path $Path)) {
            Write-Host "Warning: Log file not found at $Path" -ForegroundColor Yellow
            return @()
        }
        
        $lines = Get-Content -LiteralPath $Path -ErrorAction Stop
        foreach ($line in $lines) {
            try {
                if ([string]::IsNullOrWhiteSpace($line)) { continue }
                $obj = $line | ConvertFrom-Json -ErrorAction Stop
                if (-not $obj.Timestamp) { continue }
                
                $ts = [datetime]::Parse($obj.Timestamp)
                if ($ts -ge $Since -and $ts -lt $Until) {
                    $snapshots += $obj
                }
            }
            catch { }
        }
    }
    catch {
        Write-Host "Error reading log: $($_.Exception.Message)" -ForegroundColor Red
    }
    return $snapshots
}

function Compute-ChannelStats {
    param([object[]]$Snapshots, [string]$ChannelKey)
    
    $values = @()
    $onlineCount = 0
    $totalCount = 0
    
    # Map channel keys to Online field names
    $onlineKeyMap = @{
        "LocalMs"   = "Local"
        "CloudMs"   = "Cloud"
        "GatewayMs" = "Gateway"
        # Optional channels (not part of overall health):
        "Local2Ms"  = "Local2"
    }
    $onlineKey = $onlineKeyMap[$ChannelKey]
    
    foreach ($snap in $Snapshots) {
        $totalCount++
        if ($snap.Channels -and $null -ne $snap.Channels.$ChannelKey) {
            $val = [int]$snap.Channels.$ChannelKey
            if ($val -gt 0) { $values += [double]$val }
        }
        if ($snap.Online -and $snap.Online.$onlineKey -eq $true) {
            $onlineCount++
        }
    }
    
    $stats = @{
        Count        = $values.Count
        Mean         = $null
        Min          = $null
        Max          = $null
        Median       = $null
        P95          = $null
        Std          = $null
        Availability = if ($totalCount -gt 0) { [math]::Round(($onlineCount / $totalCount) * 100, 2) } else { $null }
    }
    
    if ($values.Count -eq 0) { return $stats }
    
    $sorted = $values | Sort-Object
    $stats.Mean = [math]::Round(($values | Measure-Object -Average).Average, 2)
    $stats.Min = [int]$sorted[0]
    $stats.Max = [int]$sorted[-1]
    
    $medianIdx = [math]::Floor($sorted.Count / 2)
    $stats.Median = [int]$sorted[$medianIdx]
    
    $p95Idx = [math]::Floor($sorted.Count * 0.95)
    $stats.P95 = [int]$sorted[$p95Idx]
    
    if ($values.Count -gt 1) {
        $mean = ($values | Measure-Object -Average).Average
        $sumSq = 0.0
        foreach ($v in $values) { $sumSq += [math]::Pow(($v - $mean), 2) }
        $stats.Std = [math]::Round([math]::Sqrt($sumSq / ($values.Count - 1)), 2)
    }
    else {
        $stats.Std = 0
    }
    
    return $stats
}

function Count-Alerts {
    param([object[]]$Snapshots)
    $alertCount = 0
    $warnCount = 0
    $spikeCount = 0
    
    foreach ($snap in $Snapshots) {
        if ($snap.Issues) {
            foreach ($issue in $snap.Issues) {
                if ($issue -like 'ALERT*') { $alertCount++ }
                elseif ($issue -like '*offline*') { $alertCount++ }
            }
        }
        if ($snap.Warnings) {
            foreach ($warn in $snap.Warnings) {
                if ($warn -like 'WARN*') { $warnCount++ }
                if ($warn -like 'SPIKE*') { $spikeCount++ }
            }
        }
    }
    
    return @{
        Alerts   = $alertCount
        Warnings = $warnCount
        Spikes   = $spikeCount
    }
}

function Get-AlertSeverity {
    param([string]$Message)
    
    # Critical: System offline, ALERT prefix, high latency spikes
    if ($Message -match '(?i)(offline|down|unavailable|ALERT:)') {
        return "Critical"
    }
    
    # Critical: Extreme latency spikes (SPIKE with > 3x baseline)
    if ($Message -match 'SPIKE.*\((\d+)ms vs \d+ms baseline\)') {
        $spikeMs = [int]$Matches[1]
        if ($spikeMs -gt 5000) { return "Critical" }
    }
    
    # Warning: BASELINE ALERT, ADAPTIVE ALERT
    if ($Message -match '(?i)(BASELINE ALERT|ADAPTIVE ALERT)') {
        return "Warning"
    }
    
    # Info: BASELINE WARN, ADAPTIVE WARN, minor spikes
    if ($Message -match '(?i)(BASELINE WARN|ADAPTIVE WARN|SPIKE)') {
        return "Info"
    }
    
    # Default to Info for unclassified messages
    return "Info"
}

function Categorize-Alerts {
    param([object[]]$Snapshots)
    
    $critical = @()
    $warning = @()
    $info = @()
    
    foreach ($snap in $Snapshots) {
        $timestamp = $snap.Timestamp
        
        # Process Issues (typically critical)
        if ($snap.Issues) {
            foreach ($issue in $snap.Issues) {
                $severity = Get-AlertSeverity -Message $issue
                $entry = @{ Timestamp = $timestamp; Message = $issue; Severity = $severity }
                
                switch ($severity) {
                    "Critical" { $critical += $entry }
                    "Warning" { $warning += $entry }
                    "Info" { $info += $entry }
                }
            }
        }
        
        # Process Warnings
        if ($snap.Warnings) {
            foreach ($warn in $snap.Warnings) {
                $severity = Get-AlertSeverity -Message $warn
                $entry = @{ Timestamp = $timestamp; Message = $warn; Severity = $severity }
                
                switch ($severity) {
                    "Critical" { $critical += $entry }
                    "Warning" { $warning += $entry }
                    "Info" { $info += $entry }
                }
            }
        }
    }
    
    return @{
        Critical      = $critical
        Warning       = $warning
        Info          = $info
        Total         = $critical.Count + $warning.Count + $info.Count
        CriticalCount = $critical.Count
        WarningCount  = $warning.Count
        InfoCount     = $info.Count
    }
}

function Compare-PeriodMetrics {
    param(
        [hashtable]$CurrentStats,
        [hashtable]$PreviousStats
    )
    
    $upArrow = [char]0x25B2    # ??    $downArrow = [char]0x25BC  # ??    $equalSign = "="
    
    $comparison = @{
        AvailabilityChange = @{}
        LatencyChange      = @{}
        AlertsChange       = @{}
    }
    
    # Compare availability for each channel
    foreach ($channel in @('Local', 'Cloud', 'Gateway')) {
        $current = if ($CurrentStats.ContainsKey($channel)) { $CurrentStats[$channel].Availability } else { 0 }
        $previous = if ($PreviousStats.ContainsKey($channel)) { $PreviousStats[$channel].Availability } else { 0 }
        
        $change = $current - $previous
        $changePercent = if ($previous -gt 0) { [math]::Round(($change / $previous) * 100, 1) } else { 0 }
        
        $arrow = if ($change -gt 0) { $upArrow } elseif ($change -lt 0) { $downArrow } else { $equalSign }
        
        $comparison.AvailabilityChange[$channel] = @{
            Current       = $current
            Previous      = $previous
            Change        = $change
            ChangePercent = $changePercent
            Trend         = if ($change -gt 0) { "UP" } elseif ($change -lt 0) { "DOWN" } else { "STABLE" }
            Arrow         = $arrow
        }
    }
    
    # Compare mean latency for each channel
    foreach ($channel in @('Local', 'Cloud', 'Gateway')) {
        $current = if ($CurrentStats.ContainsKey($channel)) { $CurrentStats[$channel].Mean } else { 0 }
        $previous = if ($PreviousStats.ContainsKey($channel)) { $PreviousStats[$channel].Mean } else { 0 }
        
        $change = $current - $previous
        $changePercent = if ($previous -gt 0) { [math]::Round(($change / $previous) * 100, 1) } else { 0 }
        
        $arrow = if ($change -gt 0) { $upArrow } elseif ($change -lt 0) { $downArrow } else { $equalSign }
        
        $comparison.LatencyChange[$channel] = @{
            Current       = $current
            Previous      = $previous
            Change        = $change
            ChangePercent = $changePercent
            Trend         = if ($change -gt 0) { "SLOWER" } elseif ($change -lt 0) { "FASTER" } else { "STABLE" }
            Arrow         = $arrow
        }
    }
    
    return $comparison
}

# Count SPIKE warnings per channel based on warning message prefix
function Count-SpikesByChannel {
    param([object[]]$Snapshots)
    $counts = @{ Local = 0; Cloud = 0; Gateway = 0 }
    foreach ($snap in $Snapshots) {
        if (-not $snap.Warnings) { continue }
        foreach ($warn in $snap.Warnings) {
            try {
                if ($warn -like 'SPIKE*') {
                    $m = [regex]::Match([string]$warn, '^SPIKE:\s*(Local LLM|Cloud AI|Gateway)\b')
                    if ($m.Success) {
                        $ch = $m.Groups[1].Value
                        switch ($ch) {
                            'Local LLM' { $counts.Local++ }
                            'Cloud AI' { $counts.Cloud++ }
                            'Gateway' { $counts.Gateway++ }
                        }
                    }
                }
            }
            catch { }
        }
    }
    return $counts
}

# Count Baseline/Adaptive Alerts/Warns per channel
function Count-AdvancedByChannel {
    param([object[]]$Snapshots)
    $res = @{
        Local   = @{ BaselineAlerts = 0; BaselineWarns = 0; AdaptiveAlerts = 0; AdaptiveWarns = 0 }
        Cloud   = @{ BaselineAlerts = 0; BaselineWarns = 0; AdaptiveAlerts = 0; AdaptiveWarns = 0 }
        Gateway = @{ BaselineAlerts = 0; BaselineWarns = 0; AdaptiveAlerts = 0; AdaptiveWarns = 0 }
    }
    foreach ($snap in $Snapshots) {
        # Issues: may contain BASELINE ALERT / ADAPTIVE ALERT
        if ($snap.Issues) {
            foreach ($issue in $snap.Issues) {
                $text = [string]$issue
                # Baseline Alerts
                $m = [regex]::Match($text, '^BASELINE ALERT:\s*(Local LLM|Cloud AI|Core Gateway)\b')
                if ($m.Success) {
                    switch ($m.Groups[1].Value) {
                        'Local LLM' { $res.Local.BaselineAlerts++ }
                        'Cloud AI' { $res.Cloud.BaselineAlerts++ }
                        'Core Gateway' { $res.Gateway.BaselineAlerts++ }
                    }
                    continue
                }
                # Adaptive Alerts
                $m = [regex]::Match($text, '^ADAPTIVE ALERT:\s*(Local LLM|Cloud AI|Core Gateway)\b')
                if ($m.Success) {
                    switch ($m.Groups[1].Value) {
                        'Local LLM' { $res.Local.AdaptiveAlerts++ }
                        'Cloud AI' { $res.Cloud.AdaptiveAlerts++ }
                        'Core Gateway' { $res.Gateway.AdaptiveAlerts++ }
                    }
                    continue
                }
            }
        }
        # Warnings: may contain BASELINE WARN / ADAPTIVE WARN
        if ($snap.Warnings) {
            foreach ($warn in $snap.Warnings) {
                $text = [string]$warn
                # Baseline Warns
                $m = [regex]::Match($text, '^BASELINE WARN:\s*(Local LLM|Cloud AI|Core Gateway)\b')
                if ($m.Success) {
                    switch ($m.Groups[1].Value) {
                        'Local LLM' { $res.Local.BaselineWarns++ }
                        'Cloud AI' { $res.Cloud.BaselineWarns++ }
                        'Core Gateway' { $res.Gateway.BaselineWarns++ }
                    }
                    continue
                }
                # Adaptive Warns
                $m = [regex]::Match($text, '^ADAPTIVE WARN:\s*(Local LLM|Cloud AI|Core Gateway)\b')
                if ($m.Success) {
                    switch ($m.Groups[1].Value) {
                        'Local LLM' { $res.Local.AdaptiveWarns++ }
                        'Cloud AI' { $res.Cloud.AdaptiveWarns++ }
                        'Core Gateway' { $res.Gateway.AdaptiveWarns++ }
                    }
                    continue
                }
            }
        }
    }
    return $res
}

# Helpers for trend direction (short vs long moving averages)
function Get-ChannelValues {
    param([object[]]$Snapshots, [string]$ChannelKey)
    $vals = @()
    foreach ($snap in $Snapshots) {
        try {
            if ($snap.Channels -and $null -ne $snap.Channels.$ChannelKey) {
                $v = [int]$snap.Channels.$ChannelKey
                if ($v -gt 0) { $vals += [double]$v }
            }
        }
        catch { }
    }
    return $vals
}

# Return time series of { Timestamp, Value } for a channel
function Get-ChannelSeries {
    param([object[]]$Snapshots, [string]$ChannelKey)
    $series = @()
    foreach ($snap in $Snapshots) {
        try {
            if ($snap.Channels -and $null -ne $snap.Channels.$ChannelKey) {
                $v = [int]$snap.Channels.$ChannelKey
                if ($v -gt 0 -and $snap.Timestamp) {
                    $series += [PSCustomObject]@{ Timestamp = [datetime]::Parse($snap.Timestamp); Value = [double]$v }
                }
            }
        }
        catch { }
    }
    return $series
}

# Compute time-of-day baselines (Peak 09-18, OffPeak otherwise)
function Compute-TOD-Baseline {
    param([object[]]$Snapshots, [string]$ChannelKey, [int]$PeakStart, [int]$PeakEnd)
    $peakVals = @()
    $offVals = @()
    foreach ($snap in $Snapshots) {
        try {
            if (-not $snap.Timestamp) { continue }
            if (-not $snap.Channels) { continue }
            $v = $snap.Channels.$ChannelKey
            if ($null -eq $v -or [int]$v -le 0) { continue }
            $ts = [datetime]::Parse($snap.Timestamp)
            $hour = $ts.Hour
            if ($hour -ge $PeakStart -and $hour -lt $PeakEnd) { $peakVals += [double]$v } else { $offVals += [double]$v }
        }
        catch { }
    }
    function _stats($arr) {
        if ($null -eq $arr -or $arr.Count -eq 0) { return @{ Mean = $null; Std = $null; Count = 0 } }
        $mean = ($arr | Measure-Object -Average).Average
        if ($arr.Count -gt 1) {
            $sumSq = 0.0; foreach ($x in $arr) { $sumSq += [math]::Pow(($x - $mean), 2) }
            $std = [math]::Sqrt($sumSq / ($arr.Count - 1))
        }
        else { $std = 0 }
        return @{ Mean = [math]::Round([double]$mean, 2); Std = [math]::Round([double]$std, 2); Count = [int]$arr.Count }
    }
    return @{ Peak = (_stats $peakVals); OffPeak = (_stats $offVals) }
}

# Generate ASCII sparkline using levels " .:-=+*#%@"
function Generate-AsciiSparkline {
    param([double[]]$Values, [int]$MaxLen)
    if ($null -eq $Values -or $Values.Count -eq 0) { return "(no-data)" }
    $chars = @(' ', '.', ':', '-', '=', '+', '*', '#', '%', '@')
    $n = [Math]::Min($MaxLen, $Values.Count)
    $arr = $Values | Select-Object -Last $n
    $min = ($arr | Measure-Object -Minimum).Minimum
    $max = ($arr | Measure-Object -Maximum).Maximum
    if ($max -le $min) { return ('-' * $n) }
    $sb = New-Object System.Text.StringBuilder
    foreach ($v in $arr) {
        $t = ($v - $min) / ($max - $min)
        $idx = [int][math]::Floor($t * ($chars.Count - 1))
        if ($idx -lt 0) { $idx = 0 }
        if ($idx -ge $chars.Count) { $idx = $chars.Count - 1 }
        [void]$sb.Append($chars[$idx])
    }
    return $sb.ToString()
}

function Compute-ShortLongTrend {
    param(
        [double[]]$Values,
        [int]$ShortN = 10,
        [int]$LongN = 20,
        [double]$ThresholdPercent = 10.0
    )
    $result = @{ ShortMean = $null; LongMean = $null; ShortCount = 0; LongCount = 0; Direction = 'UNKNOWN' }
    if ($null -eq $Values -or $Values.Count -eq 0) { return $result }
    $shortCount = [Math]::Min($ShortN, $Values.Count)
    $longCount = [Math]::Min($LongN, $Values.Count)
    $shortArr = $Values | Select-Object -Last $shortCount
    $longArr = $Values | Select-Object -Last $longCount
    $shortMean = ($shortArr | Measure-Object -Average).Average
    $longMean = ($longArr  | Measure-Object -Average).Average
    $result.ShortMean = [math]::Round([double]$shortMean, 2)
    $result.LongMean = [math]::Round([double]$longMean, 2)
    $result.ShortCount = [int]$shortCount
    $result.LongCount = [int]$longCount
    if ($null -ne $shortMean -and $null -ne $longMean -and $longMean -gt 0) {
        $threshold = $longMean * ($ThresholdPercent / 100.0)
        $diff = $shortMean - $longMean
        # Latency: lower is better
        if ($diff -lt - $threshold) { $result.Direction = 'IMPROVING' }
        elseif ($diff -gt $threshold) { $result.Direction = 'DEGRADING' }
        else { $result.Direction = 'STABLE' }
    }
    return $result
}

# Build hourly bins between start and end (UTC)
function Build-HourlyBins {
    param([datetime]$StartUtc, [datetime]$EndUtc)
    $bins = @()
    $cur = $StartUtc
    while ($cur -lt $EndUtc) { $bins += $cur; $cur = $cur.AddHours(1) }
    if ($bins.Count -eq 0) { $bins = @($StartUtc) }
    return $bins
}

# Compute hourly mean latency per channel (ms)
function Compute-HourlyMeanLatency {
    param([object[]]$Snapshots, [string]$ChannelKey, [datetime[]]$BinsUtc)
    $arr = New-Object double[] ($BinsUtc.Count)
    for ($i = 0; $i -lt $BinsUtc.Count; $i++) { $arr[$i] = 0 }
    $counts = New-Object int[] ($BinsUtc.Count)
    foreach ($snap in $Snapshots) {
        try {
            if (-not $snap.Timestamp) { continue }
            $ts = [datetime]::Parse($snap.Timestamp).ToUniversalTime()
            $val = $snap.Channels.$ChannelKey
            if ($null -eq $val -or [int]$val -le 0) { continue }
            for ($i = 0; $i -lt $BinsUtc.Count; $i++) {
                $start = $BinsUtc[$i]; $end = $start.AddHours(1)
                if ($ts -ge $start -and $ts -lt $end) { $arr[$i] += [double]$val; $counts[$i]++; break }
            }
        }
        catch { }
    }
    for ($i = 0; $i -lt $arr.Length; $i++) { if ($counts[$i] -gt 0) { $arr[$i] = [math]::Round($arr[$i] / $counts[$i], 2) } else { $arr[$i] = 0 } }
    return $arr
}

# Compute hourly availability percent per channel
function Compute-HourlyAvailability {
    param([object[]]$Snapshots, [string]$OnlineKey, [datetime[]]$BinsUtc)
    $arr = New-Object double[] ($BinsUtc.Count)
    for ($i = 0; $i -lt $BinsUtc.Count; $i++) { $arr[$i] = 0 }
    $counts = New-Object int[] ($BinsUtc.Count)
    foreach ($snap in $Snapshots) {
        try {
            if (-not $snap.Timestamp) { continue }
            $ts = [datetime]::Parse($snap.Timestamp).ToUniversalTime()
            for ($i = 0; $i -lt $BinsUtc.Count; $i++) {
                $start = $BinsUtc[$i]; $end = $start.AddHours(1)
                if ($ts -ge $start -and $ts -lt $end) {
                    $counts[$i]++
                    if ($snap.Online -and $snap.Online.$OnlineKey -eq $true) { $arr[$i]++ }
                    break
                }
            }
        }
        catch { }
    }
    for ($i = 0; $i -lt $arr.Length; $i++) { if ($counts[$i] -gt 0) { $arr[$i] = [math]::Round(($arr[$i] / $counts[$i]) * 100, 2) } else { $arr[$i] = 0 } }
    return $arr
}

# ===== Main =====
Write-Host "`nGenerating Monitoring Report..." -ForegroundColor Cyan
Write-Host "Time Window: Last $Hours hours" -ForegroundColor Gray

$now = Get-Date
$cutoff = $now.AddHours(-$Hours)
$previousCutoff = $cutoff.AddHours(-$Hours)

# Parse current period snapshots
$snapshots = Parse-Snapshots -Path $LogPath -Since $cutoff -Until $now

# Parse previous period snapshots for comparison
$previousSnapshots = Parse-Snapshots -Path $LogPath -Since $previousCutoff -Until $cutoff

if ($snapshots.Count -eq 0) {
    Write-Host "No snapshots found in the specified time window." -ForegroundColor Yellow
    exit 0
}

Write-Host "Loaded $($snapshots.Count) current snapshots" -ForegroundColor Green
if ($previousSnapshots.Count -gt 0) {
    Write-Host "Loaded $($previousSnapshots.Count) previous period snapshots for comparison" -ForegroundColor Green
}

# Compute statistics for current period
$localStats = Compute-ChannelStats -Snapshots $snapshots -ChannelKey "LocalMs"
$cloudStats = Compute-ChannelStats -Snapshots $snapshots -ChannelKey "CloudMs"
$gatewayStats = Compute-ChannelStats -Snapshots $snapshots -ChannelKey "GatewayMs"
try {
    $local2Stats = Compute-ChannelStats -Snapshots $snapshots -ChannelKey "Local2Ms"
}
catch { $local2Stats = @{} }

# Detect presence of optional Local2 channel in inputs
$hasLocal2 = $false
foreach ($snap in $snapshots) {
    try {
        if ($snap.Channels -and $null -ne $snap.Channels.Local2Ms) { $hasLocal2 = $true; break }
    }
    catch { }
}

# Compute statistics for previous period
$prevLocalStats = if ($previousSnapshots.Count -gt 0) { Compute-ChannelStats -Snapshots $previousSnapshots -ChannelKey "LocalMs" } else { @{} }
$prevCloudStats = if ($previousSnapshots.Count -gt 0) { Compute-ChannelStats -Snapshots $previousSnapshots -ChannelKey "CloudMs" } else { @{} }
$prevGatewayStats = if ($previousSnapshots.Count -gt 0) { Compute-ChannelStats -Snapshots $previousSnapshots -ChannelKey "GatewayMs" } else { @{} }

# Compare periods
$periodComparison = $null
if ($previousSnapshots.Count -gt 0) {
    $currentPeriodStats = @{
        Local   = $localStats
        Cloud   = $cloudStats
        Gateway = $gatewayStats
    }
    $previousPeriodStats = @{
        Local   = $prevLocalStats
        Cloud   = $prevCloudStats
        Gateway = $prevGatewayStats
    }
    $periodComparison = Compare-PeriodMetrics -CurrentStats $currentPeriodStats -PreviousStats $previousPeriodStats
}

# Compute trend directions (short vs long)
$localVals = Get-ChannelValues -Snapshots $snapshots -ChannelKey "LocalMs"
$cloudVals = Get-ChannelValues -Snapshots $snapshots -ChannelKey "CloudMs"
$gatewayVals = Get-ChannelValues -Snapshots $snapshots -ChannelKey "GatewayMs"

# Time-of-day baselines
$localTOD = Compute-TOD-Baseline -Snapshots $snapshots -ChannelKey "LocalMs" -PeakStart $PeakStart -PeakEnd $PeakEnd
$cloudTOD = Compute-TOD-Baseline -Snapshots $snapshots -ChannelKey "CloudMs" -PeakStart $PeakStart -PeakEnd $PeakEnd
$gatewayTOD = Compute-TOD-Baseline -Snapshots $snapshots -ChannelKey "GatewayMs" -PeakStart $PeakStart -PeakEnd $PeakEnd

# Build hourly bins once (UTC)
$bins = Build-HourlyBins -StartUtc $cutoff.ToUniversalTime() -EndUtc $now.ToUniversalTime()

# Hourly mean latency per channel
$localHourly = Compute-HourlyMeanLatency -Snapshots $snapshots -ChannelKey "LocalMs" -BinsUtc $bins
$cloudHourly = Compute-HourlyMeanLatency -Snapshots $snapshots -ChannelKey "CloudMs" -BinsUtc $bins
$gatewayHourly = Compute-HourlyMeanLatency -Snapshots $snapshots -ChannelKey "GatewayMs" -BinsUtc $bins

# Hourly availability percent per channel
$localAvailHourly = Compute-HourlyAvailability -Snapshots $snapshots -OnlineKey "Local" -BinsUtc $bins
$cloudAvailHourly = Compute-HourlyAvailability -Snapshots $snapshots -OnlineKey "Cloud" -BinsUtc $bins
$gatewayAvailHourly = Compute-HourlyAvailability -Snapshots $snapshots -OnlineKey "Gateway" -BinsUtc $bins

$localTrend = Compute-ShortLongTrend -Values $localVals
$cloudTrend = Compute-ShortLongTrend -Values $cloudVals
$gatewayTrend = Compute-ShortLongTrend -Values $gatewayVals

# Attach trend summary to stats for JSON output
$localStats.Trend = @{ ShortMeanMs = $localTrend.ShortMean; LongMeanMs = $localTrend.LongMean; ShortCount = $localTrend.ShortCount; LongCount = $localTrend.LongCount; Direction = $localTrend.Direction }
$cloudStats.Trend = @{ ShortMeanMs = $cloudTrend.ShortMean; LongMeanMs = $cloudTrend.LongMean; ShortCount = $cloudTrend.ShortCount; LongCount = $cloudTrend.LongCount; Direction = $cloudTrend.Direction }
$gatewayStats.Trend = @{ ShortMeanMs = $gatewayTrend.ShortMean; LongMeanMs = $gatewayTrend.LongMean; ShortCount = $gatewayTrend.ShortCount; LongCount = $gatewayTrend.LongCount; Direction = $gatewayTrend.Direction }

# Attach TOD baselines and sparklines
$localStats.BaselineByTOD = $localTOD
$cloudStats.BaselineByTOD = $cloudTOD
$gatewayStats.BaselineByTOD = $gatewayTOD

$localStats.Sparkline = Generate-AsciiSparkline -Values $localVals -MaxLen $SparklineLen
$cloudStats.Sparkline = Generate-AsciiSparkline -Values $cloudVals -MaxLen $SparklineLen
$gatewayStats.Sparkline = Generate-AsciiSparkline -Values $gatewayVals -MaxLen $SparklineLen

# Attach hourly latency arrays and sparklines
$localStats.HourlyLatency = @($localHourly | ForEach-Object { [double]$_ })
$cloudStats.HourlyLatency = @($cloudHourly | ForEach-Object { [double]$_ })
$gatewayStats.HourlyLatency = @($gatewayHourly | ForEach-Object { [double]$_ })
$localStats.SparklineHourlyLatency = Generate-AsciiSparkline -Values $localHourly -MaxLen $SparklineLen
$cloudStats.SparklineHourlyLatency = Generate-AsciiSparkline -Values $cloudHourly -MaxLen $SparklineLen
$gatewayStats.SparklineHourlyLatency = Generate-AsciiSparkline -Values $gatewayHourly -MaxLen $SparklineLen

# Count alerts/warnings
$alertCounts = Count-Alerts -Snapshots $snapshots

# Categorize alerts by severity
$alertsBySeverity = Categorize-Alerts -Snapshots $snapshots

# Count spikes per channel
$spikesPer = Count-SpikesByChannel -Snapshots $snapshots

# Count baseline/adaptive per channel
$advPer = Count-AdvancedByChannel -Snapshots $snapshots

# Attach spike counts into channel stats for Markdown/JSON output
$localStats.Spikes = $spikesPer.Local
$cloudStats.Spikes = $spikesPer.Cloud
$gatewayStats.Spikes = $spikesPer.Gateway

# Attach baseline/adaptive counts into stats
$localStats.BaselineAlerts = $advPer.Local.BaselineAlerts
$localStats.BaselineWarns = $advPer.Local.BaselineWarns
$localStats.AdaptiveAlerts = $advPer.Local.AdaptiveAlerts
$localStats.AdaptiveWarns = $advPer.Local.AdaptiveWarns

$cloudStats.BaselineAlerts = $advPer.Cloud.BaselineAlerts
$cloudStats.BaselineWarns = $advPer.Cloud.BaselineWarns
$cloudStats.AdaptiveAlerts = $advPer.Cloud.AdaptiveAlerts
$cloudStats.AdaptiveWarns = $advPer.Cloud.AdaptiveWarns

$gatewayStats.BaselineAlerts = $advPer.Gateway.BaselineAlerts
$gatewayStats.BaselineWarns = $advPer.Gateway.BaselineWarns
$gatewayStats.AdaptiveAlerts = $advPer.Gateway.AdaptiveAlerts
$gatewayStats.AdaptiveWarns = $advPer.Gateway.AdaptiveWarns

# Determine overall health
$allAvailabilities = @($localStats.Availability, $cloudStats.Availability, $gatewayStats.Availability) | Where-Object { $_ -ne $null }
$avgAvailability = if ($allAvailabilities.Count -gt 0) { [math]::Round(($allAvailabilities | Measure-Object -Average).Average, 2) } else { 0 }

$healthStatus = if ($avgAvailability -ge 99.5) { "EXCELLENT" }
elseif ($avgAvailability -ge 95) { "GOOD" }
elseif ($avgAvailability -ge 90) { "DEGRADED" }
else { "CRITICAL" }

# ===== Parse AGI Ledger =====
Write-Host "Parsing AGI Ledger..." -ForegroundColor Cyan

# Try to get comprehensive metrics from Python collector first
$pythonMetrics = $null
$pythonExePath = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
$dashboardScriptPath = "$WorkspaceRoot\fdo_agi_repo\scripts\ops_dashboard.py"

# Load thresholds configuration (for alerts and UI consumption)
$thresholdConfig = Load-ThresholdConfig -Path $ThresholdConfigPath
$agiThresholds = $thresholdConfig.AGI.thresholds

if ((Test-Path $pythonExePath) -and (Test-Path $dashboardScriptPath)) {
    Write-Host "  Attempting to collect AGI metrics from Python..." -ForegroundColor Gray
    $pythonMetrics = Get-AGIMetricsFromPython -Hours $Hours -PythonExe $pythonExePath -DashboardScript $dashboardScriptPath
    if ($pythonMetrics) {
        Write-Host "  ??Python metrics collected successfully" -ForegroundColor Green
    }
}

# Always parse events for backward compatibility and as fallback
$agiEvents = Parse-AGILedger -Since $cutoff
Write-Host "AGI Events parsed: $($agiEvents.Count)" -ForegroundColor Gray

# Compute metrics: use Python data if available, otherwise fallback to manual computation
if ($pythonMetrics -and $pythonMetrics.metrics) {
    Write-Host "  Using comprehensive Python metrics" -ForegroundColor Cyan
    
    # Map Python metrics to PowerShell object structure
    # ops_dashboard.py --json structure: flat pythonMetrics.metrics.* 
    $pyMetrics = $pythonMetrics.metrics
    $pyEventCounts = $null # ops_dashboard doesn't export event_counts
    
    # Calculate success rate from AGI Resonance Ledger events
    # Event structure: { "event": "health_check", "agi_quality": 0.8, "agi_confidence": 0.9, "timestamp": "2025-11-03T..." }
    # Consider successful: agi_quality >= 0.6 OR agi_confidence >= 0.7
    
    # Time Window: Filter events within the specified time range (e.g., last 24 hours)
    $now = Get-Date
    $timeWindowHours = 24  # Configurable: 1, 6, 24, 168 (7 days)
    $timeWindowStart = $now.AddHours(-$timeWindowHours)
    
    $recentEvents = $agiEvents | Where-Object {
        if ($_.timestamp) {
            try {
                $eventTime = [DateTime]::Parse($_.timestamp)
                $eventTime -ge $timeWindowStart
            }
            catch {
                $false  # Skip events with invalid timestamp
            }
        }
        elseif ($_.ts) {
            try {
                $eventTime = [DateTime]::Parse($_.ts)
                $eventTime -ge $timeWindowStart
            }
            catch {
                $false
            }
        }
        else {
            $false  # Skip events without timestamp
        }
    }
    
    # Filter task-related events (exclude system events like 'system_startup')
    $taskEvents = $recentEvents | Where-Object { 
        $_.event -notin @('system_startup', 'system_shutdown') -and
        ($null -ne $_.agi_quality -or $null -ne $_.agi_confidence)
    }
    
    $successfulTasks = ($taskEvents | Where-Object { 
            ($_.agi_quality -and $_.agi_quality -ge 0.6) -or 
            ($_.agi_confidence -and $_.agi_confidence -ge 0.7)
        }).Count
    $totalEvalTasks = $taskEvents.Count
    $successRate = if ($totalEvalTasks -gt 0) { 
        [math]::Round(($successfulTasks / $totalEvalTasks) * 100, 2) 
    }
    else { 0.0 }
    
    Write-Host "  Success Rate (last ${timeWindowHours}h): $successRate% ($successfulTasks/$totalEvalTasks)" -ForegroundColor Gray
    
    $agiMetrics = @{
        TotalEvents         = $agiEvents.Count
        TotalTasks          = if ($pyMetrics.total_tasks) { $pyMetrics.total_tasks } else { 0 }
        AvgConfidence       = if ($pyMetrics.avg_confidence) { $pyMetrics.avg_confidence } else { 0.0 }
        AvgQuality          = if ($pyMetrics.avg_quality) { $pyMetrics.avg_quality } else { 0.0 }
        SuccessRate         = $successRate
        ReplanRate          = if ($pyMetrics.replan_count -and $pyMetrics.total_tasks -gt 0) { 
            [math]::Round(($pyMetrics.replan_count / $pyMetrics.total_tasks) * 100, 2) 
        }
        else { 0.0 }
        SecondPassRate      = if ($pyMetrics.second_pass_rate) { $pyMetrics.second_pass_rate * 100 } else { 0.0 }
        AvgDurationSec      = $null # not available in ops_dashboard JSON
        
        # Evidence & RAG metrics
        EvidenceCorrection  = if ($pyMetrics.evidence_correction) { $pyMetrics.evidence_correction } else { @{} }
        
        # Add new comprehensive fields from Python collector
        Health              = @{
            checks            = $pythonMetrics.health_checks
            healthy           = $pythonMetrics.healthy
            policy            = $pythonMetrics.policy
            external_services = $pythonMetrics.external_services
        }
        Timeline            = $pythonMetrics.timeline
        EventTypes          = @{} # not available in ops_dashboard JSON
        PersonaStats        = @{} # not available in ops_dashboard JSON
        TimeWindow          = $Hours
        CollectionTimestamp = $pythonMetrics.timestamp
        
        # Compute LastActivity from events
        LastActivity        = if ($agiEvents.Count -gt 0) {
            $latestEvent = $agiEvents | Sort-Object -Property ts -Descending | Select-Object -First 1
            $unixEpoch = [datetime]::new(1970, 1, 1, 0, 0, 0, 0, [System.DateTimeKind]::Utc)
            $unixEpoch.AddSeconds($latestEvent.ts).ToLocalTime()
        }
        else { $null }
    }

    # Augment Python EvidenceCorrection with forced-only aggregates if missing
    try {
        $hasForced = $false
        if ($agiMetrics.EvidenceCorrection) {
            $props = $agiMetrics.EvidenceCorrection.PSObject.Properties
            if ($props) { $hasForced = $props.Name -contains 'forced_attempts' }
        }
        if (-not $hasForced) {
            $manualFromEvents = Compute-AGIMetrics -Events $agiEvents
            if ($manualFromEvents -and $manualFromEvents.EvidenceCorrection) {
                $forcedEC = $manualFromEvents.EvidenceCorrection
                # Ensure EvidenceCorrection exists as container
                if (-not $agiMetrics.EvidenceCorrection) { $agiMetrics.EvidenceCorrection = @{} }

                # Always add keys so UI can rely on presence (even when zero)
                Set-ObjectPropertySafe -Object $agiMetrics.EvidenceCorrection -Name 'forced_attempts' -Value $forcedEC.forced_attempts
                Set-ObjectPropertySafe -Object $agiMetrics.EvidenceCorrection -Name 'forced_avg_hits' -Value $forcedEC.forced_avg_hits
                Set-ObjectPropertySafe -Object $agiMetrics.EvidenceCorrection -Name 'forced_avg_added' -Value $forcedEC.forced_avg_added
                Set-ObjectPropertySafe -Object $agiMetrics.EvidenceCorrection -Name 'forced_success_rate' -Value $forcedEC.forced_success_rate
                Set-ObjectPropertySafe -Object $agiMetrics.EvidenceCorrection -Name 'forced_success_sparkline' -Value $forcedEC.forced_success_sparkline
                Set-ObjectPropertySafe -Object $agiMetrics.EvidenceCorrection -Name 'forced_samples' -Value $forcedEC.forced_samples
            }
        }
    }
    catch { }
}
else {
    Write-Host "  Using fallback manual metrics computation" -ForegroundColor Yellow
    $agiMetrics = Compute-AGIMetrics -Events $agiEvents
}

# ===== Aggregate Resonance Policy Events (from AGI Ledger) =====
try {
    $policyEvents = $agiEvents | Where-Object { $_.event -eq 'resonance_policy' }
    $policyCounts = @{ allow = 0; warn = 0; block = 0 }
    $lastPolicy = $null
    foreach ($pe in $policyEvents) {
        try {
            $act = if ($pe.action) { ("" + $pe.action).ToLower() } else { "" }
            if ($policyCounts.ContainsKey($act)) { $policyCounts[$act] += 1 }
        }
        catch {}
        $lastPolicy = $pe
    }
    $lastPolTimeIso = $null
    if ($lastPolicy -and $lastPolicy.ts) {
        try {
            $unixEpoch = [datetime]::new(1970, 1, 1, 0, 0, 0, 0, [System.DateTimeKind]::Utc)
            $lastPolTimeIso = $unixEpoch.AddSeconds([double]$lastPolicy.ts).ToString('s')
        }
        catch { $lastPolTimeIso = $null }
    }
    $agiPolicy = @{
        counts    = $policyCounts
        last      = if ($lastPolicy) { @{ mode = $lastPolicy.mode; policy = $lastPolicy.policy; reasons = $lastPolicy.reasons } } else { @{} }
        last_time = $lastPolTimeIso
    }
    
    # Also surface currently configured active policy from configs/resonance_config.json (or example)
    try {
        $cfgDir = Join-Path (Split-Path -Parent $PSScriptRoot) 'configs'
        $primaryCfg = Join-Path $cfgDir 'resonance_config.json'
        $exampleCfg = Join-Path $cfgDir 'resonance_config.example.json'
        $cfgPath = if (Test-Path -LiteralPath $primaryCfg) { $primaryCfg } elseif (Test-Path -LiteralPath $exampleCfg) { $exampleCfg } else { $null }
        if ($cfgPath) {
            $cfgJson = Get-Content -LiteralPath $cfgPath -Raw | ConvertFrom-Json -ErrorAction Stop
            $activePol = $null
            if ($cfgJson.active_policy) { $activePol = [string]$cfgJson.active_policy }
            elseif ($cfgJson.default_policy) { $activePol = [string]$cfgJson.default_policy }
            if ($activePol) { $agiPolicy.active = $activePol }

            if ($cfgJson.optimization) {
                $agiPolicy.config_optimization = $cfgJson.optimization
            }
        }
    }
    catch { }

    try {
        $optEvents = $agiEvents | Where-Object { $_.event -eq 'resonance_optimization' }
        $optSummary = @{
            total             = $optEvents.Count
            peak              = 0
            offpeak           = 0
            throttle          = 0
            prefer_gateway    = 0
            preferred_primary = @{}
            last              = @{}
        }

        if ($optEvents.Count -gt 0) {
            $latestOpt = $null
            foreach ($opt in $optEvents) {
                try {
                    $isPeak = $false
                    if ($null -ne $opt.is_peak_now) {
                        $isPeak = [bool]$opt.is_peak_now
                    }
                    if ($isPeak) { $optSummary.peak += 1 } else { $optSummary.offpeak += 1 }

                    if ($opt.should_throttle_offpeak) { $optSummary.throttle += 1 }
                    if ($opt.prefer_gateway) { $optSummary.prefer_gateway += 1 }

                    $channels = @()
                    if ($opt.preferred_channels) {
                        $channels = @($opt.preferred_channels)
                    }
                    if ($channels.Count -gt 0) {
                        $first = [string]$channels[0]
                        if ($optSummary.preferred_primary.ContainsKey($first)) {
                            $optSummary.preferred_primary[$first] += 1
                        }
                        else {
                            $optSummary.preferred_primary[$first] = 1
                        }
                    }

                    if ($opt.ts) {
                        if (-not $latestOpt -or ($opt.ts -gt $latestOpt.ts)) {
                            $latestOpt = $opt
                        }
                    }
                }
                catch { }
            }

            if ($latestOpt) {
                $optSummary.last = @{
                    is_peak_now        = $latestOpt.is_peak_now
                    preferred_channels = $latestOpt.preferred_channels
                    offpeak_mode       = $latestOpt.offpeak_mode
                    batch_compression  = $latestOpt.batch_compression
                    learning_bias      = $latestOpt.learning_bias
                    should_throttle    = $latestOpt.should_throttle_offpeak
                    timestamp          = $latestOpt.ts
                }
            }
        }

        $agiPolicy.optimization = $optSummary
    }
    catch { }
    # Attach to metrics object in a safe way
    if (-not $agiMetrics) { $agiMetrics = @{} }
    $agiMetrics.Policy = $agiPolicy

    # Derive last task latency (ms): prefer last policy observed.latency_ms, fallback to recent duration fields
    $lastLatencyMs = $null
    try {
        if ($lastPolicy -and $lastPolicy.observed -and $lastPolicy.observed.latency_ms) {
            $lastLatencyMs = [double]$lastPolicy.observed.latency_ms
        }
    }
    catch { $lastLatencyMs = $null }
    if ($null -eq $lastLatencyMs) {
        try {
            $rev = $agiEvents | Sort-Object -Property ts -Descending
            foreach ($ev in $rev) {
                if ($ev.duration_ms) { $lastLatencyMs = [double]$ev.duration_ms; break }
                elseif ($ev.duration_sec) { $lastLatencyMs = [double]$ev.duration_sec * 1000.0; break }
                elseif ($ev.duration) { $lastLatencyMs = [double]$ev.duration * 1000.0; break }
            }
        }
        catch { $lastLatencyMs = $null }
    }
    try { $agiMetrics.LastTaskLatencyMs = $lastLatencyMs } catch { }
}
catch { }

# ===== Gateway Optimization Log Summary =====
try {
    $optLogPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'outputs\gateway_optimization_log.jsonl'
    if (Test-Path -LiteralPath $optLogPath) {
        $rawLines = Get-Content -LiteralPath $optLogPath -Tail 200 -ErrorAction Stop
        $optEvents = @()
        foreach ($line in $rawLines) {
            try {
                if ([string]::IsNullOrWhiteSpace($line)) { continue }
                $obj = $line | ConvertFrom-Json -ErrorAction Stop
                if ($obj.timestamp) {
                    try { $obj | Add-Member -NotePropertyName 'ParsedTimestamp' -NotePropertyValue ([datetime]$obj.timestamp) -Force }
                    catch { }
                }
                $optEvents += $obj
            }
            catch { }
        }

        if ($optEvents.Count -gt 0) {
            $sortedOpt = $optEvents | Where-Object { $_.ParsedTimestamp } | Sort-Object -Property ParsedTimestamp
            if (-not $sortedOpt) { $sortedOpt = $optEvents }
            $lastOpt = $sortedOpt[-1]

            $gatewayOptSummary = @{
                total_entries   = $optEvents.Count
                peak_entries    = ($optEvents | Where-Object { $_.phase -eq 'peak' }).Count
                offpeak_entries = ($optEvents | Where-Object { $_.phase -eq 'off-peak' }).Count
                warmup_triggers = ($optEvents | Where-Object { $_.strategies.off_peak_warmup.should_warmup }).Count
                dry_run         = $lastOpt.dry_run
                log_path        = $optLogPath
                last            = @{}
            }

            try {
                $gatewayOptSummary.last = @{
                    timestamp      = $lastOpt.timestamp
                    phase          = $lastOpt.phase
                    timeout_ms     = $lastOpt.strategies.adaptive_timeout.timeout_ms
                    retry_attempts = $lastOpt.strategies.adaptive_timeout.retry_attempts
                    concurrency    = $lastOpt.strategies.phase_sync_scheduler.concurrency
                    warmup_active  = $lastOpt.strategies.off_peak_warmup.should_warmup
                    next_warmup    = if ($lastOpt.strategies.off_peak_warmup.should_warmup) { $lastOpt.strategies.off_peak_warmup.schedule } else { $lastOpt.strategies.off_peak_warmup.next_schedule }
                }
            }
            catch { }

            if ($lastOpt.thresholds) {
                $gatewayOptSummary.thresholds = $lastOpt.thresholds
            }

            if (-not $agiMetrics) { $agiMetrics = @{} }
            $agiMetrics.GatewayOptimization = $gatewayOptSummary
        }
    }
}
catch { }

# ===== Read Evaluation Config (min_quality) via Python loader (best-effort) =====
$evalMinQ = $null
try {
    $pyCmd = "import json; from fdo_agi_repo.orchestrator.config import get_evaluation_config as g; print(json.dumps(g()))"
    $pyOut = & python -c $pyCmd 2>$null
    if ($LASTEXITCODE -eq 0 -and $pyOut) {
        try {
            $evObj = $pyOut | ConvertFrom-Json -ErrorAction Stop
            if ($evObj.min_quality -ne $null) { $evalMinQ = [double]$evObj.min_quality }
        }
        catch {}
    }
}
catch {}

# ===== Extract Closed-loop Snapshot (from AGI Ledger) =====
try {
    $clsEvents = $agiEvents | Where-Object { $_.event -eq 'closed_loop_snapshot' }
    if ($clsEvents -and $clsEvents.Count -gt 0) {
        $lastCls = ($clsEvents | Sort-Object -Property ts -Descending | Select-Object -First 1)
        $snap = $lastCls.snapshot
        $sim = $null; $rt = $null
        try { $sim = $snap.resonance_simulator } catch {}
        try { $rt = $snap.realtime_resonance } catch {}

        $closedLoop = @{}
        if ($sim) {
            $closedLoop["simulator"] = @{
                summary        = $sim.summary
                last_resonance = $sim.last_resonance
                last_entropy   = $sim.last_entropy
            }
        }
        if ($rt) {
            $closedLoop["realtime"] = @{
                strength  = $rt.strength
                coherence = $rt.coherence
                phase     = $rt.phase
            }
        }
        # Add last snapshot time (ISO)
        try {
            $unixEpoch = [datetime]::new(1970, 1, 1, 0, 0, 0, 0, [System.DateTimeKind]::Utc)
            $closedLoop["last_time"] = $unixEpoch.AddSeconds([double]$lastCls.ts).ToString('s')
        }
        catch {}
        if (-not $agiMetrics) { $agiMetrics = @{} }
        $agiMetrics.ClosedLoop = $closedLoop
    }
}
catch { }

# ===== Generate Markdown Report =====
$reportLines = @()
$reportLines += "# Monitoring Report"
$reportLines += ""
$reportLines += "**Generated**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$reportLines += "**Time Window**: Last $Hours hours"
$reportLines += "**Data Points**: $($snapshots.Count) snapshots"
$reportLines += ""
$reportLines += "---"
$reportLines += ""
$reportLines += "## Executive Summary"
$reportLines += ""
$reportLines += '```'
$localAvailStr = if ($localStats.Availability -ne $null) { "$($localStats.Availability)%" } else { "n/a" }
$localMeanStr = if ($localStats.Mean -ne $null) { "$($localStats.Mean)ms" } else { "n/a" }
$cloudAvailStr = if ($cloudStats.Availability -ne $null) { "$($cloudStats.Availability)%" } else { "n/a" }
$cloudMeanStr = if ($cloudStats.Mean -ne $null) { "$($cloudStats.Mean)ms" } else { "n/a" }
$gatewayAvailStr = if ($gatewayStats.Availability -ne $null) { "$($gatewayStats.Availability)%" } else { "n/a" }
$gatewayMeanStr = if ($gatewayStats.Mean -ne $null) { "$($gatewayStats.Mean)ms" } else { "n/a" }

$reportLines += "  HEALTH: $healthStatus"
$reportLines += "  Availability: $avgAvailability%  |  Alerts: $($alertCounts.Alerts)  |  Warnings: $($alertCounts.Warnings)  |  Spikes: $($alertCounts.Spikes)"
$reportLines += ""

# Add Alert Severity breakdown
$criticalIcon = "[!]"
$warningIcon = "[*]"
$infoIcon = "[i]"
$reportLines += "  Alert Severity:"
$reportLines += "    $criticalIcon Critical: $($alertsBySeverity.CriticalCount)  |  $warningIcon Warning: $($alertsBySeverity.WarningCount)  |  $infoIcon Info: $($alertsBySeverity.InfoCount)"
$reportLines += ""

$reportLines += "  Local LLM:     $localAvailStr avail  |  $localMeanStr mean"
$reportLines += "  Cloud AI:      $cloudAvailStr avail  |  $cloudMeanStr mean"
$reportLines += "  Core Gateway: $gatewayAvailStr avail  |  $gatewayMeanStr mean"

# Show Resonance Policy summary (if available)
if ($agiMetrics.Policy) {
    try {
        $pc = $agiMetrics.Policy.counts
        $lastMode = if ($agiMetrics.Policy.last.mode) { $agiMetrics.Policy.last.mode } else { 'n/a' }
        $lastPol = if ($agiMetrics.Policy.last.policy) { $agiMetrics.Policy.last.policy } else { 'n/a' }
        $activePol = if ($agiMetrics.Policy.active) { $agiMetrics.Policy.active } else { 'n/a' }
        $reportLines += "  Resonance Policy: mode=$lastMode active=$activePol last=$lastPol | allow=$($pc.allow) warn=$($pc.warn) block=$($pc.block)"
        if ($agiMetrics.Policy.optimization) {
            $opt = $agiMetrics.Policy.optimization
            $primarySummary = ""
            try {
                if ($opt.preferred_primary) {
                    $pairs = @()
                    foreach ($k in ($opt.preferred_primary.Keys | Sort-Object)) {
                        $pairs += ("{0}:{1}" -f $k, $opt.preferred_primary[$k])
                    }
                    if ($pairs.Count -gt 0) {
                        $primarySummary = " primary=[" + ($pairs -join ", ") + "]"
                    }
                }
            }
            catch { $primarySummary = "" }

            $reportLines += (
                "  Resonance Optimization: total={0} peak={1} offpeak={2} throttle={3} gateway_pref={4}{5}" -f 
                $opt.total,
                $opt.peak,
                $opt.offpeak,
                $opt.throttle,
                $opt.prefer_gateway,
                $primarySummary
            )
        }
        if ($agiMetrics.GatewayOptimization) {
            $gopt = $agiMetrics.GatewayOptimization
            $lastGo = $gopt.last
            $lastPhase = if ($lastGo.phase) { $lastGo.phase } else { 'n/a' }
            $lastTimeout = if ($lastGo.timeout_ms) { [int]$lastGo.timeout_ms } else { 0 }
            $lastConc = if ($lastGo.concurrency) { [int]$lastGo.concurrency } else { 0 }
            $warmup = if ($lastGo.warmup_active) { 'warmup' } else { 'idle' }
            $reportLines += (
                "  Gateway Optimizer: last={0} phase={1} timeout={2}ms concurrency={3} state={4} entries={5}" -f 
                (if ($lastGo.timestamp) { $lastGo.timestamp } else { 'n/a' }),
                $lastPhase,
                $lastTimeout,
                $lastConc,
                $warmup,
                $gopt.total_entries
            )
        }
        if ($pc.block -gt 0) {
            $reportLines += "  !!! POLICY BLOCKS DETECTED: $($pc.block) in window !!!"
        }
    }
    catch { }
}

# Show last task latency (if available)
if ($agiMetrics.LastTaskLatencyMs) {
    try {
        $reportLines += ("  Last Task: {0}ms" -f [int]$agiMetrics.LastTaskLatencyMs)
    }
    catch { }
}

# Show Evaluation Config summary (if available)
if ($evalMinQ -ne $null) {
    $reportLines += "  AGI Eval: min_quality=$evalMinQ"
}

# Show Feedback Loop stats (if available)
try {
    $ytFeedbackPath = "$WorkspaceRoot\fdo_agi_repo\outputs\youtube_feedback_bqi.jsonl"
    $rpaFeedbackPath = "$WorkspaceRoot\fdo_agi_repo\outputs\rpa_feedback_bqi.jsonl"
    $ytCount = 0
    $rpaCount = 0
    if (Test-Path $ytFeedbackPath) {
        $ytCount = @(Get-Content $ytFeedbackPath | Where-Object { $_.Trim() -ne "" }).Count
    }
    if (Test-Path $rpaFeedbackPath) {
        $rpaCount = @(Get-Content $rpaFeedbackPath | Where-Object { $_.Trim() -ne "" }).Count
    }
    if ($ytCount -gt 0 -or $rpaCount -gt 0) {
        $reportLines += "  Feedback Loop: YouTube=$ytCount RPA=$rpaCount events ingested"
    }
}
catch { }

# Add Historical Comparison if available
if ($periodComparison) {
    $reportLines += ""
    $reportLines += "  --- vs Previous Period (${Hours}h ago) ---"
    
    # Local LLM comparison
    $localLatChange = $periodComparison.LatencyChange.Local
    $localAvailChange = $periodComparison.AvailabilityChange.Local
    if ($localLatChange.Current -gt 0) {
        $latArrow = $localLatChange.Arrow
        $latChangeText = if ($localLatChange.ChangePercent -ne 0) { "$latArrow$([math]::Abs($localLatChange.ChangePercent))%" } else { "=" }
        $availChangeText = if ($localAvailChange.ChangePercent -ne 0) { "$($localAvailChange.Arrow)$([math]::Abs($localAvailChange.ChangePercent))%" } else { "=" }
        $reportLines += "  Local:   Latency $latChangeText  |  Avail $availChangeText"
    }
    
    # Cloud AI comparison
    $cloudLatChange = $periodComparison.LatencyChange.Cloud
    $cloudAvailChange = $periodComparison.AvailabilityChange.Cloud
    if ($cloudLatChange.Current -gt 0) {
        $latArrow = $cloudLatChange.Arrow
        $latChangeText = if ($cloudLatChange.ChangePercent -ne 0) { "$latArrow$([math]::Abs($cloudLatChange.ChangePercent))%" } else { "=" }
        $availChangeText = if ($cloudAvailChange.ChangePercent -ne 0) { "$($cloudAvailChange.Arrow)$([math]::Abs($cloudAvailChange.ChangePercent))%" } else { "=" }
        $reportLines += "  Cloud:   Latency $latChangeText  |  Avail $availChangeText"
    }
    
    # Gateway comparison
    $gatewayLatChange = $periodComparison.LatencyChange.Gateway
    $gatewayAvailChange = $periodComparison.AvailabilityChange.Gateway
    if ($gatewayLatChange.Current -gt 0) {
        $latArrow = $gatewayLatChange.Arrow
        $latChangeText = if ($gatewayLatChange.ChangePercent -ne 0) { "$latArrow$([math]::Abs($gatewayLatChange.ChangePercent))%" } else { "=" }
        $availChangeText = if ($gatewayAvailChange.ChangePercent -ne 0) { "$($gatewayAvailChange.Arrow)$([math]::Abs($gatewayAvailChange.ChangePercent))%" } else { "=" }
        $reportLines += "  Gateway: Latency $latChangeText  |  Avail $availChangeText"
    }
}
$reportLines += '```'
$reportLines += ""
$reportLines += "---"
$reportLines += ""
$reportLines += "## Report Configuration"
$reportLines += ""
$reportLines += "- **Time Window**: Last $Hours hours"
$reportLines += "- **Peak Hours**: $PeakStart:00-$PeakEnd:00"
$reportLines += "- **Sparkline Length**: $SparklineLen"
$reportLines += "- **Data Points**: $($snapshots.Count) snapshots"
if ($hasLocal2) {
    $reportLines += "- **Optional Channel Detected**: Local2 (port 18090). Excluded from overall health/availability calculations."
    $reportLines += "  - To include this probe in console view, run quick_status.ps1 without -HideOptional."
    $reportLines += "  - Optional CSV: outputs/monitoring_timeseries_optional_latest.csv"
}
$reportLines += ""
$reportLines += "---"
$reportLines += ""
$reportLines += "## Overall Health"
$reportLines += ""
$reportLines += "- **Status**: $healthStatus"
$reportLines += "- **Average Availability**: $avgAvailability%"
$reportLines += "- **Alerts**: $($alertCounts.Alerts)"
$reportLines += "- **Warnings**: $($alertCounts.Warnings)"
$reportLines += "- **Spikes**: $($alertCounts.Spikes)"
$reportLines += ""
$reportLines += "---"
$reportLines += ""
$reportLines += "## Performance Snapshot"
$reportLines += ""
try {
    $perfJsonPath = Join-Path (Split-Path -Parent $PSScriptRoot) "outputs\performance_metrics_latest.json"
    if (Test-Path -LiteralPath $perfJsonPath) {
        $perf = Get-Content -LiteralPath $perfJsonPath -Raw | ConvertFrom-Json
        $overall = [double]$perf.OverallSuccessRate
        $effective = [double]$perf.OverallEffectiveSuccessRate
        $bands = $perf.BandCounts
        $systems = [int]$perf.SystemsConsidered
        $topAttn = @()
        if ($perf.PSObject.Properties.Name -contains 'TopAttention') {
            foreach ($t in $perf.TopAttention) { $topAttn += ("{0} ({1}%)" -f $t.System, ([double]$t.EffectiveSuccessRate).ToString('F1')) }
        }
        $reportLines += ("- **Systems Considered**: {0}" -f $systems)
        $reportLines += ("- **Overall Success**: {0}%  |  **Effective**: {1}%" -f $overall.ToString('F1'), $effective.ToString('F1'))
        if ($bands) {
            $reportLines += ("- **Bands**: Excellent={0}  Good={1}  Needs={2}  NoData={3}" -f $bands.Excellent, $bands.Good, $bands.Needs, $bands.NoData)
        }
        if ($topAttn.Count -gt 0) { $reportLines += ("- **Top Attention**: {0}" -f ($topAttn -join ', ')) }
        $dashMd = Join-Path (Split-Path -Parent $PSScriptRoot) "outputs\performance_dashboard_latest.md"
        if (Test-Path -LiteralPath $dashMd) { $reportLines += ("- See: performance_dashboard_latest.md") }
    }
    else {
        $reportLines += "_No performance dashboard data found (outputs/performance_metrics_latest.json missing)._"
    }
}
catch {
    $reportLines += "_Failed to load performance snapshot._"
}

$reportLines += "---"
$reportLines += ""
$reportLines += "## Channel Statistics"
$reportLines += ""

function Add-ChannelSection([string]$Name, [hashtable]$Stats) {
    $script:reportLines += "### $Name"
    $script:reportLines += ""
    if ($Stats.Count -eq 0) {
        $script:reportLines += "_No data available_"
    }
    else {
        $script:reportLines += "| Metric | Value |"
        $script:reportLines += "|--------|-------|"
        $script:reportLines += "| Availability | $($Stats.Availability)% |"
        $script:reportLines += "| Mean Latency | $($Stats.Mean) ms |"
        $script:reportLines += "| Median Latency | $($Stats.Median) ms |"
        $script:reportLines += "| Min Latency | $($Stats.Min) ms |"
        $script:reportLines += "| Max Latency | $($Stats.Max) ms |"
        $script:reportLines += "| 95th Percentile | $($Stats.P95) ms |"
        $script:reportLines += "| Std Deviation | +/- $($Stats.Std) ms |"
        if ($Stats.Spikes -ne $null) { $script:reportLines += "| Spike Count | $($Stats.Spikes) |" }
        if ($Stats.BaselineAlerts -ne $null) { $script:reportLines += "| Baseline Alerts | $($Stats.BaselineAlerts) |" }
        if ($Stats.BaselineWarns -ne $null) { $script:reportLines += "| Baseline Warns | $($Stats.BaselineWarns) |" }
        if ($Stats.AdaptiveAlerts -ne $null) { $script:reportLines += "| Adaptive Alerts | $($Stats.AdaptiveAlerts) |" }
        if ($Stats.AdaptiveWarns -ne $null) { $script:reportLines += "| Adaptive Warns | $($Stats.AdaptiveWarns) |" }
        $script:reportLines += "| Sample Count | $($Stats.Count) |"
        if ($Stats.Trend) {
            $arrow = switch ($Stats.Trend.Direction) { 'IMPROVING' { '++' } 'DEGRADING' { '--' } 'STABLE' { '==' } default { '??' } }
            $script:reportLines += ""
            $script:reportLines += ("Trend: {0} {1} (short {2}ms vs long {3}ms; n={4}/{5})" -f $arrow, $Stats.Trend.Direction, $Stats.Trend.ShortMeanMs, $Stats.Trend.LongMeanMs, $Stats.Trend.ShortCount, $Stats.Trend.LongCount)
        }
        if ($Stats.Sparkline) {
            $script:reportLines += "Sparkline (last 30): " + $Stats.Sparkline
        }
        if ($Stats.SparklineHourlyLatency) {
            $script:reportLines += "Hourly Latency Sparkline: " + $Stats.SparklineHourlyLatency
        }
        if ($Stats.BaselineByTOD) {
            $pk = $Stats.BaselineByTOD.Peak
            $op = $Stats.BaselineByTOD.OffPeak
            $pkMean = if ($pk.Mean -ne $null) { $pk.Mean } else { 'n/a' }
            $pkStd = if ($pk.Std -ne $null) { $pk.Std } else { 'n/a' }
            $opMean = if ($op.Mean -ne $null) { $op.Mean } else { 'n/a' }
            $opStd = if ($op.Std -ne $null) { $op.Std } else { 'n/a' }
            $script:reportLines += ""
            $line = "Time-of-day Baselines: Peak mean $pkMean ms (+/- $pkStd) [n=$($pk.Count)] | Off-peak mean $opMean ms (+/- $opStd) [n=$($op.Count)]"
            $script:reportLines += $line
        }
    }
    $script:reportLines += ""
}

Add-ChannelSection -Name "Local LLM (LM Studio)" -Stats $localStats
Add-ChannelSection -Name "Cloud AI (ion-api)" -Stats $cloudStats
Add-ChannelSection -Name "Core Gateway" -Stats $gatewayStats

if ($hasLocal2 -and $local2Stats.Count -gt 0) {
    $reportLines += "### Optional Channels"
    $reportLines += ""
    Add-ChannelSection -Name "Local LLM (Secondary 18090, optional)" -Stats $local2Stats
}

$reportLines += "---"
$reportLines += ""
$reportLines += "## AGI System Status"
$reportLines += ""

if ($agiMetrics.TotalEvents -eq 0) {
    $reportLines += "_No AGI activity in the selected time window_"
}
else {
    $reportLines += "| Metric | Value |"
    $reportLines += "|--------|-------|"
    $reportLines += "| Total Events | $($agiMetrics.TotalEvents) |"
    $reportLines += "| Unique Tasks | $($agiMetrics.TaskCount) |"
    if ($agiMetrics.AvgQuality -ne $null) {
        $qualityStatus = if ($agiMetrics.AvgQuality -ge 0.8) { "?��" } elseif ($agiMetrics.AvgQuality -ge 0.7) { "?��" } else { "?��" }
        $reportLines += "| Avg Quality | $qualityStatus $($agiMetrics.AvgQuality) |"
    }
    if ($agiMetrics.SuccessRate -ne $null) {
        $successStatus = if ($agiMetrics.SuccessRate -ge 80) { "?��" } elseif ($agiMetrics.SuccessRate -ge 70) { "?��" } else { "?��" }
        $reportLines += "| Success Rate | $successStatus $($agiMetrics.SuccessRate)% |"
    }
    if ($agiMetrics.AvgDuration -ne $null) {
        $reportLines += "| Avg Duration | $($agiMetrics.AvgDuration)s |"
    }
    if ($agiMetrics.ReplanRate -ne $null) {
        $reportLines += "| Replan Rate | $($agiMetrics.ReplanRate)% |"
    }
    if ($agiMetrics.LastActivity) {
        $timeSince = (Get-Date) - $agiMetrics.LastActivity
        $timeText = if ($timeSince.TotalMinutes -lt 60) { 
            "$([math]::Round($timeSince.TotalMinutes, 1)) minutes ago" 
        }
        elseif ($timeSince.TotalHours -lt 24) {
            "$([math]::Round($timeSince.TotalHours, 1)) hours ago"
        }
        else {
            "$([math]::Round($timeSince.TotalDays, 1)) days ago"
        }
        $reportLines += "| Last Activity | $timeText |"
    }
    
    # Event type breakdown
    if ($agiMetrics.EventTypes.Count -gt 0) {
        $reportLines += ""
        $reportLines += "**Event Type Breakdown:**"
        $reportLines += ""
        $reportLines += "| Event Type | Count |"
        $reportLines += "|------------|-------|"
        foreach ($eventType in ($agiMetrics.EventTypes.Keys | Sort-Object)) {
            $reportLines += "| $eventType | $($agiMetrics.EventTypes[$eventType]) |"
        }
    }
}

$reportLines += ""

# AGI Alerts Check
if ($agiMetrics.TotalEvents -gt 0) {
    $agiAlerts = @()
    
    # Low Quality Alert (configurable)
    $minQuality = [double]$agiThresholds.min_quality
    $critQuality = [double]([math]::Max(0, $minQuality - 0.1))
    if ($null -ne $agiMetrics.AvgQuality -and $agiMetrics.AvgQuality -lt $minQuality) {
        $severity = if ($agiMetrics.AvgQuality -lt $critQuality) { "?�� CRITICAL" } else { "?�� WARNING" }
        $agiAlerts += "$severity AGI Quality: $($agiMetrics.AvgQuality) (threshold: $minQuality)"
    }
    
    # Low Success Rate Alert (configurable)
    $minSuccess = [double]$agiThresholds.min_success_rate_percent
    $critSuccess = [double]([math]::Max(0, $minSuccess - 10))
    if ($null -ne $agiMetrics.SuccessRate -and $agiMetrics.SuccessRate -lt $minSuccess) {
        $severity = if ($agiMetrics.SuccessRate -lt $critSuccess) { "?�� CRITICAL" } else { "?�� WARNING" }
        $agiAlerts += "$severity AGI Success Rate: $($agiMetrics.SuccessRate)% (threshold: $minSuccess%)"
    }
    
    # High Replan Rate Alert (configurable)
    $replanThresh = [double]$agiThresholds.replan_rate_percent
    $replanCrit = [double]($replanThresh * 2)
    if ($null -ne $agiMetrics.ReplanRate -and $agiMetrics.ReplanRate -gt $replanThresh) {
        $severity = if ($agiMetrics.ReplanRate -gt $replanCrit) { "?�� CRITICAL" } else { "?�� WARNING" }
        $agiAlerts += "$severity AGI Replan Rate: $($agiMetrics.ReplanRate)% (threshold: $replanThresh%)"
    }
    
    # High Average Duration Alert (configurable)
    $maxAvgDur = [double]$agiThresholds.max_avg_duration_sec
    $critAvgDur = [double]($maxAvgDur + 5)
    $avgDurToUse = if ($agiMetrics.AvgDurationSec -ne $null) { $agiMetrics.AvgDurationSec } else { $agiMetrics.AvgDuration }
    if ($null -ne $avgDurToUse -and $avgDurToUse -gt $maxAvgDur) {
        $severity = if ($avgDurToUse -gt $critAvgDur) { "?�� CRITICAL" } else { "?�� WARNING" }
        $agiAlerts += "$severity AGI Avg Duration: $([math]::Round($avgDurToUse,1))s (threshold: ${maxAvgDur}s)"
    }
    
    # Inactivity Alert (configurable)
    if ($agiMetrics.LastActivity) {
        $timeSince = (Get-Date) - $agiMetrics.LastActivity
        $inactiveHours = [double]$agiThresholds.inactive_hours
        if ($timeSince.TotalHours -gt $inactiveHours) {
            $severity = if ($timeSince.TotalHours -gt ($inactiveHours * 3)) { "?�� CRITICAL" } else { "?�� WARNING" }
            $hoursSince = [math]::Round($timeSince.TotalHours, 1)
            $agiAlerts += "$severity AGI Inactive: $hoursSince hours since last activity (threshold: ${inactiveHours}h)"
        }
    }
    
    if ($agiAlerts.Count -gt 0) {
        $reportLines += "**[WARN] AGI System Alerts:**"
        $reportLines += ""
        foreach ($alert in $agiAlerts) {
            $reportLines += "- $alert"
        }
        $reportLines += ""
    }
}

$reportLines += "---"
$reportLines += ""
$reportLines += "## Alerts Summary"
$reportLines += ""

# Build Alerts Summary table for Markdown and JSON
$totalBaselineAlerts = $advPer.Local.BaselineAlerts + $advPer.Cloud.BaselineAlerts + $advPer.Gateway.BaselineAlerts
$totalBaselineWarns = $advPer.Local.BaselineWarns + $advPer.Cloud.BaselineWarns + $advPer.Gateway.BaselineWarns
$totalAdaptiveAlerts = $advPer.Local.AdaptiveAlerts + $advPer.Cloud.AdaptiveAlerts + $advPer.Gateway.AdaptiveAlerts
$totalAdaptiveWarns = $advPer.Local.AdaptiveWarns + $advPer.Cloud.AdaptiveWarns + $advPer.Gateway.AdaptiveWarns
$totalSpikes = $spikesPer.Local + $spikesPer.Cloud + $spikesPer.Gateway

$reportLines += "| Channel | Baseline Alerts | Baseline Warns | Adaptive Alerts | Adaptive Warns | Spikes |"
$reportLines += "|---------|------------------|----------------|------------------|----------------|--------|"
$reportLines += ("| Local   | {0} | {1} | {2} | {3} | {4} |" -f $advPer.Local.BaselineAlerts, $advPer.Local.BaselineWarns, $advPer.Local.AdaptiveAlerts, $advPer.Local.AdaptiveWarns, $spikesPer.Local)
$reportLines += ("| Cloud   | {0} | {1} | {2} | {3} | {4} |" -f $advPer.Cloud.BaselineAlerts, $advPer.Cloud.BaselineWarns, $advPer.Cloud.AdaptiveAlerts, $advPer.Cloud.AdaptiveWarns, $spikesPer.Cloud)
$reportLines += ("| Gateway | {0} | {1} | {2} | {3} | {4} |" -f $advPer.Gateway.BaselineAlerts, $advPer.Gateway.BaselineWarns, $advPer.Gateway.AdaptiveAlerts, $advPer.Gateway.AdaptiveWarns, $spikesPer.Gateway)
$reportLines += ("| Total   | {0} | {1} | {2} | {3} | {4} |" -f $totalBaselineAlerts, $totalBaselineWarns, $totalAdaptiveAlerts, $totalAdaptiveWarns, $totalSpikes)

$reportLines += "---"
$reportLines += ""
$reportLines += "### Alert Severity Details"
$reportLines += ""

if ($alertsBySeverity.Total -eq 0) {
    $reportLines += "_No alerts in this period_"
}
else {
    # Critical Alerts
    if ($alertsBySeverity.CriticalCount -gt 0) {
        $reportLines += "#### [!] Critical ($($alertsBySeverity.CriticalCount))"
        $reportLines += ""
        $reportLines += "| Timestamp | Message |"
        $reportLines += "|-----------|---------|"
        foreach ($alert in ($alertsBySeverity.Critical | Select-Object -First 5)) {
            $ts = ([datetime]::Parse($alert.Timestamp)).ToString('HH:mm:ss')
            $msg = $alert.Message -replace '\|', '\|'
            $reportLines += "| $ts | $msg |"
        }
        if ($alertsBySeverity.CriticalCount -gt 5) {
            $reportLines += ""
            $reportLines += "_... and $($alertsBySeverity.CriticalCount - 5) more critical alerts_"
        }
        $reportLines += ""
    }
    
    # Warning Alerts
    if ($alertsBySeverity.WarningCount -gt 0) {
        $reportLines += "#### [*] Warning ($($alertsBySeverity.WarningCount))"
        $reportLines += ""
        $reportLines += "| Timestamp | Message |"
        $reportLines += "|-----------|---------|"
        foreach ($alert in ($alertsBySeverity.Warning | Select-Object -First 3)) {
            $ts = ([datetime]::Parse($alert.Timestamp)).ToString('HH:mm:ss')
            $msg = $alert.Message -replace '\|', '\|'
            $reportLines += "| $ts | $msg |"
        }
        if ($alertsBySeverity.WarningCount -gt 3) {
            $reportLines += ""
            $reportLines += "_... and $($alertsBySeverity.WarningCount - 3) more warnings_"
        }
        $reportLines += ""
    }
    
    # Info Alerts (summary only, no details)
    if ($alertsBySeverity.InfoCount -gt 0) {
        $reportLines += "#### [i] Info ($($alertsBySeverity.InfoCount))"
        $reportLines += ""
        $reportLines += "_Minor alerts and informational messages. See JSON output for full details._"
        $reportLines += ""
    }
}

$reportLines += "---"
$reportLines += ""
$reportLines += "### Alerts Trend (hourly)"
$reportLines += ""

# Build hourly bins from cutoff to now
$now = Get-Date
$binStart = $cutoff.ToUniversalTime()
$binEnd = $now.ToUniversalTime()
$bins = @()
while ($binStart -lt $binEnd) {
    $bins += $binStart
    $binStart = $binStart.AddHours(1)
}
if ($bins.Count -eq 0) { $bins = @($cutoff.ToUniversalTime()) }

$alertsPerHour = New-Object int[] ($bins.Count)
$warnsPerHour = New-Object int[] ($bins.Count)
$spikesPerHour = New-Object int[] ($bins.Count)

foreach ($snap in $snapshots) {
    try {
        if (-not $snap.Timestamp) { continue }
        $ts = [datetime]::Parse($snap.Timestamp).ToUniversalTime()
        # Find bin index: max hour i where bins[i] <= ts < bins[i]+1h
        for ($i = 0; $i -lt $bins.Count; $i++) {
            $start = $bins[$i]
            $end = $start.AddHours(1)
            if ($ts -ge $start -and $ts -lt $end) {
                if ($snap.Issues) { $alertsPerHour[$i] += @($snap.Issues).Count }
                if ($snap.Warnings) {
                    $warnsPerHour[$i] += @($snap.Warnings).Count
                    foreach ($w in $snap.Warnings) { if ([string]$w -like 'SPIKE*') { $spikesPerHour[$i]++ } }
                }
                break
            }
        }
    }
    catch { }
}

$alertsSpark = Generate-AsciiSparkline -Values $alertsPerHour -MaxLen $SparklineLen
$warnsSpark = Generate-AsciiSparkline -Values $warnsPerHour -MaxLen $SparklineLen
$spikesSpark = Generate-AsciiSparkline -Values $spikesPerHour -MaxLen $SparklineLen

$reportLines += ("Alerts:    " + $alertsSpark)
$reportLines += ("Warnings:  " + $warnsSpark)
$reportLines += ("Spikes:    " + $spikesSpark)

$reportLines += "---"
$reportLines += ""
$reportLines += "### Availability Trend (hourly)"
$reportLines += ""
$localAvailSpark = Generate-AsciiSparkline -Values $localAvailHourly -MaxLen $SparklineLen
$cloudAvailSpark = Generate-AsciiSparkline -Values $cloudAvailHourly -MaxLen $SparklineLen
$gatewayAvailSpark = Generate-AsciiSparkline -Values $gatewayAvailHourly -MaxLen $SparklineLen
$reportLines += ("Local:     " + $localAvailSpark)
$reportLines += ("Cloud:     " + $cloudAvailSpark)
$reportLines += ("Gateway:   " + $gatewayAvailSpark)

$reportLines += "---"
$reportLines += ""
$reportLines += "## Recommendations"
$reportLines += ""

# Generate recommendations based on data
$recommendations = @()

# Critical issues first (high priority)
if ($alertsBySeverity.CriticalCount -gt 0) {
    $recommendations += "- **[CRITICAL]** $($alertsBySeverity.CriticalCount) critical alert(s) detected"
    $recommendations += "  - Action: Review critical alerts immediately in 'Alert Severity Details' section"
    $recommendations += "  - Action: Check system availability and response times"
    $recommendations += "  - Action: Verify all services are online and responsive"
    $recommendations += ""
}

if ($null -ne $localStats.Mean -and $localStats.Mean -gt 1500) {
    $severity = if ($localStats.Mean -gt 3000) { "[HIGH]" } else { "[MEDIUM]" }
    $recommendations += "- **$severity Local LLM**: High latency detected (avg $($localStats.Mean)ms)."
    $recommendations += "  - Action: Check LM Studio process CPU/GPU usage and memory"
    $recommendations += "  - Action: Consider model optimization or hardware upgrade"
    $recommendations += "  - Action: Review recent logs for performance degradation patterns"
}
if ($null -ne $localStats.Availability -and $localStats.Availability -lt 95) {
    $severity = if ($localStats.Availability -lt 90) { "[HIGH]" } else { "[MEDIUM]" }
    $recommendations += "- **$severity Local LLM**: Low availability ($($localStats.Availability)%)."
    $recommendations += "  - Action: Check LM Studio process stability and restart if needed"
    $recommendations += "  - Action: Verify model loading configuration"
    $recommendations += "  - Action: Review system resource constraints"
}

if ($null -ne $cloudStats.Std -and $cloudStats.Std -gt 500) {
    $severity = if ($cloudStats.Std -gt 1000) { "[MEDIUM]" } else { "[LOW]" }
    $recommendations += "- **$severity Cloud AI**: High variability detected (+/- $($cloudStats.Std)ms)."
    $recommendations += "  - Action: Check network latency and bandwidth to Cloud Run"
    $recommendations += "  - Action: Review Cloud Run instance scaling and cold start patterns"
    $recommendations += "  - Action: Investigate backend API performance metrics"
}
if ($null -ne $cloudStats.Availability -and $cloudStats.Availability -lt 95) {
    $severity = if ($cloudStats.Availability -lt 90) { "[HIGH]" } else { "[MEDIUM]" }
    $recommendations += "- **$severity Cloud AI**: Low availability ($($cloudStats.Availability)%)."
    $recommendations += "  - Action: Check Cloud Run service health and error rates"
    $recommendations += "  - Action: Verify authentication and quota limits"
    $recommendations += "  - Action: Review recent deployment changes"
}

if ($null -ne $gatewayStats.Availability -and $gatewayStats.Availability -lt 95) {
    $severity = if ($gatewayStats.Availability -lt 90) { "[HIGH]" } else { "[MEDIUM]" }
    $recommendations += "- **$severity Core Gateway**: Low availability ($($gatewayStats.Availability)%)."
    $recommendations += "  - Action: Verify routing configuration and backend connections"
    $recommendations += "  - Action: Check gateway process health and logs"
    $recommendations += "  - Action: Test backend endpoints independently"
}

if ($alertCounts.Spikes -gt 5) {
    $recommendations += "- **Spikes**: $($alertCounts.Spikes) latency spikes detected. Review system load and resource allocation."
}

# AGI-based recommendations
if ($agiMetrics.TotalEvents -gt 0) {
    if ($null -ne $agiMetrics.AvgQuality -and $agiMetrics.AvgQuality -lt 0.7) {
        $severity = if ($agiMetrics.AvgQuality -lt 0.6) { "[HIGH]" } else { "[MEDIUM]" }
        $recommendations += "- **$severity AGI System**: Low quality score ($($agiMetrics.AvgQuality))."
        $recommendations += "  - Action: Review recent AGI task outputs for errors"
        $recommendations += "  - Action: Check persona LLM configuration and prompts"
        $recommendations += "  - Action: Verify synthesis/antithesis/thesis pipeline"
    }
    
    if ($null -ne $agiMetrics.ReplanRate -and $agiMetrics.ReplanRate -gt 10) {
        $severity = if ($agiMetrics.ReplanRate -gt 20) { "[HIGH]" } else { "[MEDIUM]" }
        $recommendations += "- **$severity AGI System**: High replan rate ($($agiMetrics.ReplanRate)%)."
        $recommendations += "  - Action: Investigate task complexity and initial planning quality"
        $recommendations += "  - Action: Review rune event logs for replan patterns"
        $recommendations += "  - Action: Consider adjusting AGI planning parameters"
    }
    
    if ($null -ne $agiMetrics.AvgDuration -and $agiMetrics.AvgDuration -gt 10) {
        $severity = if ($agiMetrics.AvgDuration -gt 15) { "[HIGH]" } else { "[MEDIUM]" }
        $recommendations += "- **$severity AGI System**: High average duration ($($agiMetrics.AvgDuration)s)."
        $recommendations += "  - Action: Check LLM response times and token limits"
        $recommendations += "  - Action: Review task complexity and input sizes"
        $recommendations += "  - Action: Consider parallelization or optimization"
    }
}

$policySnapshotPath = Join-Path (Split-Path -Parent $OutMarkdown) "policy_ab_snapshot_latest.md"
if (Test-Path -LiteralPath $policySnapshotPath) {
    $reportLines += "## Policy Snapshot (Latest)"
    $reportLines += ""
    try {
        $snapshotPreview = Get-Content -LiteralPath $policySnapshotPath -TotalCount 60
        if ($snapshotPreview) {
            $reportLines += $snapshotPreview
        }
    }
    catch {
        $reportLines += "_Failed to load policy snapshot: $($_.Exception.Message)_"
    }
    $reportLines += ""
}

$stabilizerSummaryPath = Join-Path (Split-Path -Parent $OutMarkdown) "auto_stabilizer_summary.txt"
if (Test-Path -LiteralPath $stabilizerSummaryPath) {
    try {
        $summaryLine = Get-Content -LiteralPath $stabilizerSummaryPath -TotalCount 1
        if ($summaryLine) {
            $reportLines += "Auto Stabilizer Summary: $summaryLine"
            $reportLines += ""
        }
    }
    catch {
        $reportLines += "(Auto Stabilizer summary unavailable: $($_.Exception.Message))"
        $reportLines += ""
    }
}

$rpaSummaryPath = Join-Path (Split-Path -Parent $OutMarkdown) "rpa_worker_status.txt"
if (Test-Path -LiteralPath $rpaSummaryPath) {
    try {
        $rpaLine = Get-Content -LiteralPath $rpaSummaryPath -TotalCount 1
        if ($rpaLine) {
            $reportLines += "RPA Worker Summary: $rpaLine"
            $reportLines += ""
        }
    }
    catch {
        $reportLines += "(RPA Worker summary unavailable: $($_.Exception.Message))"
        $reportLines += ""
    }
}

$rpaAlertPath = Join-Path (Split-Path -Parent $OutMarkdown) "alerts\rpa_worker_alert.json"
if (Test-Path -LiteralPath $rpaAlertPath) {
    try {
        $alertRaw = Get-Content -LiteralPath $rpaAlertPath -Raw
        if (-not [string]::IsNullOrWhiteSpace($alertRaw)) {
            $alertObj = $alertRaw | ConvertFrom-Json -ErrorAction Stop
            $alertMessage = if ($alertObj.message) { $alertObj.message } else { "RPA worker restart limit reached." }
            $alertTs = $null
            if ($alertObj.timestamp) { $alertTs = $alertObj.timestamp }
            else {
                try { $alertTs = (Get-Item -LiteralPath $rpaAlertPath).LastWriteTime.ToString("o") } catch {}
            }
            $alertDetails = @()
            if ($alertTs) { $alertDetails += "timestamp=$alertTs" }
            if ($alertObj.recent_restarts -ne $null -and $alertObj.max_restarts -ne $null) {
                $alertDetails += "recent_restarts=$($alertObj.recent_restarts)/$($alertObj.max_restarts)"
            }
            if ($alertObj.window_seconds -ne $null) { $alertDetails += "window_seconds=$($alertObj.window_seconds)" }
            $detailText = if ($alertDetails.Count) { " (" + ($alertDetails -join ", ") + ")" } else { "" }
            $reportLines += "RPA Worker Alert: $alertMessage$detailText"
            $reportLines += ""
        }
    }
    catch {
        $reportLines += "(RPA Worker alert unavailable: $($_.Exception.Message))"
        $reportLines += ""
    }
}

$resourceSummaryPath = Join-Path (Split-Path -Parent $OutMarkdown) "resource_optimizer_summary.md"
if (Test-Path -LiteralPath $resourceSummaryPath) {
    try {
        $resourceLines = Get-Content -LiteralPath $resourceSummaryPath -TotalCount 20
        if ($resourceLines) {
            $reportLines += "## Resource Optimizer Summary"
            $reportLines += ""
            $reportLines += $resourceLines
            $reportLines += ""
        }
    }
    catch {
        $reportLines += "(Resource optimizer summary unavailable: $($_.Exception.Message))"
        $reportLines += ""
    }
}

if ($recommendations.Count -eq 0) {
    $reportLines += "_All systems operating within normal parameters._"
}
else {
    $reportLines += ($recommendations -join "`n")
}
$reportLines += ""
$reportLines += "---"
$reportLines += ""
$reportLines += "_Report generated by unified monitoring dashboard_"

$markdown = $reportLines -join "`r`n"

# Write Markdown
try {
    $mdDir = Split-Path -Parent $OutMarkdown
    if ($mdDir -and -not (Test-Path $mdDir)) { New-Item -ItemType Directory -Path $mdDir | Out-Null }
    [System.IO.File]::WriteAllText($OutMarkdown, $markdown, [System.Text.Encoding]::UTF8)
    Write-Host "Markdown report written to: $OutMarkdown" -ForegroundColor Green
}
catch {
    Write-Host "Error writing Markdown: $($_.Exception.Message)" -ForegroundColor Red
}

# ===== Generate JSON Metrics =====
# Prepare AGI health with thresholds attached for UI/HTML consumers
$agiHealthObj = @{}
if ($agiMetrics.Health) {
    if ($agiMetrics.Health -is [hashtable]) {
        foreach ($kv in $agiMetrics.Health.GetEnumerator()) {
            $agiHealthObj[$kv.Key] = $kv.Value
        }
    }
    else {
        foreach ($prop in $agiMetrics.Health.PSObject.Properties) {
            $agiHealthObj[$prop.Name] = $prop.Value
        }
    }
}
if ($agiThresholds) {
    $agiHealthObj["thresholds"] = $agiThresholds
    $agiHealthObj["thresholds_ui"] = $agiThresholds
}

$sessionIndexPath = Join-Path (Split-Path $PSScriptRoot -Parent) "LLM_Unified\ion-mentoring\data\session_summaries\index.json"
$sessionSummaryMetrics = Get-SessionSummaryMetrics -IndexPath $sessionIndexPath -RecentLimit 5

$metrics = @{
    Generated            = (Get-Date).ToString('s')
    TimeWindowHours      = $Hours
    SnapshotCount        = $snapshots.Count
    Config               = @{
        Hours                   = $Hours
        PeakStart               = $PeakStart
        PeakEnd                 = $PeakEnd
        SparklineLen            = $SparklineLen
        GeneratedAt             = (Get-Date).ToString('s')
        LogPath                 = $LogPath
        OptionalChannelsPresent = $hasLocal2
    }
    Health               = @{
        Status          = $healthStatus
        AvgAvailability = $avgAvailability
        Alerts          = $alertCounts.Alerts
        Warnings        = $alertCounts.Warnings
        Spikes          = $alertCounts.Spikes
    }
    AlertsBySeverity     = @{
        Critical      = @($alertsBySeverity.Critical | ForEach-Object { @{ Timestamp = $_.Timestamp; Message = $_.Message } })
        Warning       = @($alertsBySeverity.Warning | ForEach-Object { @{ Timestamp = $_.Timestamp; Message = $_.Message } })
        Info          = @($alertsBySeverity.Info | ForEach-Object { @{ Timestamp = $_.Timestamp; Message = $_.Message } })
        CriticalCount = $alertsBySeverity.CriticalCount
        WarningCount  = $alertsBySeverity.WarningCount
        InfoCount     = $alertsBySeverity.InfoCount
        Total         = $alertsBySeverity.Total
    }
    AGI                  = @{
        TotalEvents        = $agiMetrics.TotalEvents
        TaskCount          = if ($agiMetrics.TotalTasks) { $agiMetrics.TotalTasks } else { $agiMetrics.TaskCount }
        AvgQuality         = $agiMetrics.AvgQuality
        AvgConfidence      = if ($agiMetrics.AvgConfidence) { $agiMetrics.AvgConfidence } else { $null }
        AvgDuration        = if ($agiMetrics.AvgDurationSec) { $agiMetrics.AvgDurationSec } else { $agiMetrics.AvgDuration }
        SuccessRate        = $agiMetrics.SuccessRate
        ReplanRate         = $agiMetrics.ReplanRate
        SecondPassRate     = if ($agiMetrics.SecondPassRate) { $agiMetrics.SecondPassRate } else { $null }
        LastActivity       = if ($agiMetrics.LastActivity) { $agiMetrics.LastActivity.ToString('s') } else { $null }
        EventTypes         = if ($agiMetrics.EventTypes) { $agiMetrics.EventTypes } else { @{} }
        PersonaStats       = if ($agiMetrics.PersonaStats) { $agiMetrics.PersonaStats } else { @{} }
        PersonaTimeline    = if ($agiMetrics.PersonaTimeline) { $agiMetrics.PersonaTimeline } else { if ($pythonMetrics.persona_timeline) { $pythonMetrics.persona_timeline } else { @{} } }
        Thresholds         = $agiThresholds
        Health             = $agiHealthObj
        LastTaskLatencyMs  = if ($agiMetrics.LastTaskLatencyMs) { [double]$agiMetrics.LastTaskLatencyMs } else { $null }
        Policy             = if ($agiMetrics.Policy) { $agiMetrics.Policy } else { @{} }
        ClosedLoop         = if ($agiMetrics.ClosedLoop) { $agiMetrics.ClosedLoop } else { @{} }
        Timeline           = if ($agiMetrics.Timeline) { $agiMetrics.Timeline } else { @() }
        TimeWindow         = if ($agiMetrics.TimeWindow) { $agiMetrics.TimeWindow } else { $Hours }
        CollectionTime     = if ($agiMetrics.CollectionTimestamp) { $agiMetrics.CollectionTimestamp } else { (Get-Date).ToString('s') }
        EvidenceCorrection = if ($agiMetrics.EvidenceCorrection) { $agiMetrics.EvidenceCorrection } else { @{} }
        Config             = @{ Evaluation = @{ min_quality = $evalMinQ } }
        Alerts             = @{
            LowQuality      = ($null -ne $agiMetrics.AvgQuality -and $agiMetrics.AvgQuality -lt [double]$agiThresholds.min_quality)
            LowSuccessRate  = ($null -ne $agiMetrics.SuccessRate -and $agiMetrics.SuccessRate -lt [double]$agiThresholds.min_success_rate_percent)
            HighReplanRate  = ($null -ne $agiMetrics.ReplanRate -and $agiMetrics.ReplanRate -gt [double]$agiThresholds.replan_rate_percent)
            HighAvgDuration = ($null -ne $agiMetrics.AvgDurationSec -and $agiMetrics.AvgDurationSec -gt [double]$agiThresholds.max_avg_duration_sec)
            Inactive        = if ($agiMetrics.LastActivity) { ((Get-Date) - $agiMetrics.LastActivity).TotalHours -gt [double]$agiThresholds.inactive_hours } else { $false }
        }
    }
    GatewayOptimizer     = if ($agiMetrics.GatewayOptimization) { $agiMetrics.GatewayOptimization } else { @{} }
    SessionSummaries     = $sessionSummaryMetrics
    Channels             = @{
        Local   = $localStats
        Cloud   = $cloudStats
        Gateway = $gatewayStats
    }
    OptionalChannels     = if ($hasLocal2) { @{ Local2 = $local2Stats } } else { @{} }
    AlertsSummary        = @{
        Local   = @{ BaselineAlerts = $advPer.Local.BaselineAlerts; BaselineWarns = $advPer.Local.BaselineWarns; AdaptiveAlerts = $advPer.Local.AdaptiveAlerts; AdaptiveWarns = $advPer.Local.AdaptiveWarns; Spikes = $spikesPer.Local }
        Cloud   = @{ BaselineAlerts = $advPer.Cloud.BaselineAlerts; BaselineWarns = $advPer.Cloud.BaselineWarns; AdaptiveAlerts = $advPer.Cloud.AdaptiveAlerts; AdaptiveWarns = $advPer.Cloud.AdaptiveWarns; Spikes = $spikesPer.Cloud }
        Gateway = @{ BaselineAlerts = $advPer.Gateway.BaselineAlerts; BaselineWarns = $advPer.Gateway.BaselineWarns; AdaptiveAlerts = $advPer.Gateway.AdaptiveAlerts; AdaptiveWarns = $advPer.Gateway.AdaptiveWarns; Spikes = $spikesPer.Gateway }
        Total   = @{ BaselineAlerts = $totalBaselineAlerts; BaselineWarns = $totalBaselineWarns; AdaptiveAlerts = $totalAdaptiveAlerts; AdaptiveWarns = $totalAdaptiveWarns; Spikes = $totalSpikes }
    }
    AlertsTimeline       = @{
        StartIso  = $cutoff.ToUniversalTime().ToString('s')
        EndIso    = (Get-Date).ToUniversalTime().ToString('s')
        Interval  = '1h'
        Hours     = @($bins | ForEach-Object { $_.ToString('s') })
        Alerts    = @($alertsPerHour | ForEach-Object { [int]$_ })
        Warnings  = @($warnsPerHour | ForEach-Object { [int]$_ })
        Spikes    = @($spikesPerHour | ForEach-Object { [int]$_ })
        Sparkline = @{ Alerts = $alertsSpark; Warnings = $warnsSpark; Spikes = $spikesSpark }
    }
    AvailabilityTimeline = @{
        StartIso  = $cutoff.ToUniversalTime().ToString('s')
        EndIso    = (Get-Date).ToUniversalTime().ToString('s')
        Interval  = '1h'
        Hours     = @($bins | ForEach-Object { $_.ToString('s') })
        Local     = @($localAvailHourly | ForEach-Object { [double]$_ })
        Cloud     = @($cloudAvailHourly | ForEach-Object { [double]$_ })
        Gateway   = @($gatewayAvailHourly | ForEach-Object { [double]$_ })
        Sparkline = @{ Local = $localAvailSpark; Cloud = $cloudAvailSpark; Gateway = $gatewayAvailSpark }
    }
}

# Add period comparison to JSON if available
if ($periodComparison) {
    $metrics.PeriodComparison = @{
        ComparisonWindow   = "${Hours}h"
        CurrentPeriod      = @{
            Start = $cutoff.ToUniversalTime().ToString('s')
            End   = $now.ToUniversalTime().ToString('s')
            Count = $snapshots.Count
        }
        PreviousPeriod     = @{
            Start = $previousCutoff.ToUniversalTime().ToString('s')
            End   = $cutoff.ToUniversalTime().ToString('s')
            Count = $previousSnapshots.Count
        }
        AvailabilityChange = $periodComparison.AvailabilityChange
        LatencyChange      = $periodComparison.LatencyChange
    }
}

try {
    $jsonDir = Split-Path -Parent $OutJson
    if ($jsonDir -and -not (Test-Path $jsonDir)) { New-Item -ItemType Directory -Path $jsonDir | Out-Null }
    $jsonText = $metrics | ConvertTo-Json -Depth 10 -Compress
    [System.IO.File]::WriteAllText($OutJson, $jsonText, [System.Text.Encoding]::UTF8)
    Write-Host "JSON metrics written to: $OutJson" -ForegroundColor Green
}
catch {
    Write-Host "Error writing JSON: $($_.Exception.Message)" -ForegroundColor Red
}

# ===== Generate CSV Timeseries (optional) =====
if (-not $SkipCsv) {
    try {
        $csvLines = @("Timestamp,LocalMs,CloudMs,GatewayMs,LocalOnline,CloudOnline,GatewayOnline")
        foreach ($snap in $snapshots) {
            $ts = $snap.Timestamp
            $localMs = if ($snap.Channels.LocalMs) { $snap.Channels.LocalMs } else { "" }
            $cloudMs = if ($snap.Channels.CloudMs) { $snap.Channels.CloudMs } else { "" }
            $gwMs = if ($snap.Channels.GatewayMs) { $snap.Channels.GatewayMs } else { "" }
            $localOn = if ($snap.Online.Local) { "1" } else { "0" }
            $cloudOn = if ($snap.Online.Cloud) { "1" } else { "0" }
            $gwOn = if ($snap.Online.Gateway) { "1" } else { "0" }
            $csvLines += "$ts,$localMs,$cloudMs,$gwMs,$localOn,$cloudOn,$gwOn"
        }
        $csv = $csvLines -join "`r`n"
        
        $csvDir = Split-Path -Parent $OutCsv
        if ($csvDir -and -not (Test-Path $csvDir)) { New-Item -ItemType Directory -Path $csvDir | Out-Null }
        [System.IO.File]::WriteAllText($OutCsv, $csv, [System.Text.Encoding]::UTF8)
        Write-Host "CSV timeseries written to: $OutCsv" -ForegroundColor Green
    }
    catch {
        Write-Host "Error writing CSV: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# ===== Generate Events CSV (optional) =====
if (-not $SkipEvents) {
    try {
        $evLines = @("Timestamp,Level,Type,Channel,Message")
        foreach ($snap in $snapshots) {
            $ts = $snap.Timestamp
            if ($snap.Issues) {
                foreach ($issue in $snap.Issues) {
                    $msg = [string]$issue
                    $level = "ALERT"
                    $type = "Other"
                    $channel = ""
                    $m = [regex]::Match($msg, '^(BASELINE ALERT|ADAPTIVE ALERT):\s*(Local LLM|Cloud AI|Core Gateway)')
                    if ($m.Success) {
                        $type = ($m.Groups[1].Value -replace ' ', '') # BaselineAlert/AdaptiveAlert
                        $channel = $m.Groups[2].Value
                    }
                    elseif ($msg -like 'ALERT*') {
                        $type = 'Alert'
                    }
                    $escaped = ($msg -replace '"', '''')
                    $evLines += ($ts + "," + $level + "," + $type + "," + $channel + "," + '"' + $escaped + '"')
                }
            }
            if ($snap.Warnings) {
                foreach ($warn in $snap.Warnings) {
                    $msg = [string]$warn
                    $level = "WARN"
                    $type = "Other"
                    $channel = ""
                    $m = [regex]::Match($msg, '^(BASELINE WARN|ADAPTIVE WARN):\s*(Local LLM|Cloud AI|Core Gateway)')
                    if ($m.Success) {
                        $type = ($m.Groups[1].Value -replace ' ', '') # BaselineWarn/AdaptiveWarn
                        $channel = $m.Groups[2].Value
                    }
                    else {
                        $m2 = [regex]::Match($msg, '^SPIKE:\s*(Local LLM|Cloud AI|Gateway)')
                        if ($m2.Success) { $type = 'Spike'; $channel = $m2.Groups[1].Value }
                    }
                    $escaped = ($msg -replace '"', '''')
                    $evLines += ($ts + "," + $level + "," + $type + "," + $channel + "," + '"' + $escaped + '"')
                }
            }
        }
        $evCsv = $evLines -join "`r`n"
        $evDir = Split-Path -Parent $OutEventsCsv
        if ($evDir -and -not (Test-Path $evDir)) { New-Item -ItemType Directory -Path $evDir | Out-Null }
        [System.IO.File]::WriteAllText($OutEventsCsv, $evCsv, [System.Text.Encoding]::UTF8)
        Write-Host "Events CSV written to: $OutEventsCsv" -ForegroundColor Green
    }
    catch {
        Write-Host "Error writing Events CSV: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# ========================================
# Generate HTML Dashboard (if not skipped)
# ========================================
if (-not $SkipHtml) {
    try {
        Write-Host "`n[HTML Dashboard Generation]" -ForegroundColor Cyan
        
        # Read template
        $templatePath = Join-Path (Split-Path $PSScriptRoot -Parent) "scripts\monitoring_dashboard_template.html"
        if (-not (Test-Path $templatePath)) {
            Write-Host "Warning: Template not found at $templatePath, skipping HTML generation" -ForegroundColor Yellow
        }
        else {
            $template = [System.IO.File]::ReadAllText($templatePath, [System.Text.Encoding]::UTF8)
            
            # Inject metrics JSON
            $metricsJson = $metrics | ConvertTo-Json -Depth 10 -Compress
            $htmlContent = $template -replace '\{\{METRICS_JSON\}\}', $metricsJson
            
            # Ensure output directory exists
            $htmlDir = Split-Path -Parent $OutHtml
            if ($htmlDir -and -not (Test-Path $htmlDir)) { 
                New-Item -ItemType Directory -Path $htmlDir | Out-Null 
            }
            
            # Write HTML
            [System.IO.File]::WriteAllText($OutHtml, $htmlContent, [System.Text.Encoding]::UTF8)
            Write-Host "HTML Dashboard written to: $OutHtml" -ForegroundColor Green
            Write-Host "  Open in browser to view interactive dashboard" -ForegroundColor Gray

            # Copy Health Gate state JSON next to HTML (for relative loading in dashboard)
            try {
                $htmlDir = Split-Path -Parent $OutHtml
                $repoRoot = Split-Path -Parent $PSScriptRoot
                $healthGateSrc = Join-Path $repoRoot "fdo_agi_repo\outputs\health_gate_state.json"
                $healthGateDst = Join-Path $htmlDir "health_gate_state.json"
                if (Test-Path -LiteralPath $healthGateSrc) {
                    Copy-Item -LiteralPath $healthGateSrc -Destination $healthGateDst -Force -ErrorAction Stop
                    Write-Host "Health Gate state copied to: $healthGateDst" -ForegroundColor DarkGreen
                }
                else {
                    Write-Host "Health Gate state not found at $healthGateSrc (skip copy)" -ForegroundColor DarkYellow
                }
            }
            catch {
                Write-Host "Warning: Failed to copy Health Gate state JSON: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    }
    catch {
        Write-Host "Error generating HTML dashboard: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`nReport Generation Complete!" -ForegroundColor Cyan
Write-Host "Overall Health: $healthStatus ($avgAvailability% availability)" -ForegroundColor $(if ($healthStatus -eq "EXCELLENT" -or $healthStatus -eq "GOOD") { "Green" } else { "Yellow" })