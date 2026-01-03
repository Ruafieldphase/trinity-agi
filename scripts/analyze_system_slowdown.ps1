param([int]$Hours = 48)
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host $msg -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host $msg -ForegroundColor Green }
function Write-Warn($msg) { Write-Host $msg -ForegroundColor Yellow }

try {
    $ws = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
    $ledger = Join-Path $ws 'fdo_agi_repo\memory\resonance_ledger.jsonl'
    $metricsJson = Join-Path $ws 'outputs\monitoring_metrics_latest.json'
    $replanHistory = Join-Path $ws 'outputs\replan_rate_history.jsonl'

    Write-Info "Analyzing system performance trends..."
    $report = @{
        timestamp             = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss')
        analysis_window_hours = $Hours
        findings              = @()
        root_causes           = @()
        recommendations       = @()
    }

    # 1. Check monitoring metrics
    if (Test-Path $metricsJson) {
        $metrics = Get-Content $metricsJson -Raw | ConvertFrom-Json
        
        # Latency trend
        $local = $metrics.Channels.Local
        if ($local.Trend.Direction -eq 'DEGRADING') {
            $report.findings += "Local LLM latency is DEGRADING: short avg ${local.Trend.ShortMeanMs}ms vs long avg ${local.Trend.LongMeanMs}ms"
            $report.root_causes += "Local channel showing gradual slowdown"
        }
        
        $cloud = $metrics.Channels.Cloud
        if ($cloud.Trend.Direction -eq 'SLOWER' -or $cloud.Trend.Direction -eq 'DEGRADING') {
            $report.findings += "Cloud AI latency trend: $($cloud.Trend.Direction) (short ${cloud.Trend.ShortMeanMs}ms vs long ${cloud.Trend.LongMeanMs}ms)"
        }

        # ReplanRate trend
        $replanRate = $metrics.AGI.ReplanRate
        if ($replanRate -gt 15) {
            $report.findings += "ReplanRate is HIGH: ${replanRate}% (threshold 10%)"
            $report.root_causes += "Evidence retrieval quality may be degrading, forcing more replanning"
        }

        # Evidence correction metrics
        $evCorr = $metrics.AGI.EvidenceCorrection
        if ($evCorr -and $evCorr.success_rate -lt 0.1) {
            $report.findings += "Evidence correction success rate LOW: $([math]::Round($evCorr.success_rate*100,1))%"
            $report.root_causes += "RAG retrieval not finding relevant context efficiently"
        }
        if ($evCorr -and $evCorr.avg_relevance -lt 0.1) {
            $report.findings += "Evidence relevance score LOW: $([math]::Round($evCorr.avg_relevance,3))"
            $report.root_causes += "Retrieved evidence quality degrading over time"
        }
    }

    # 2. Check ReplanRate history trend
    if (Test-Path $replanHistory) {
        $history = Get-Content $replanHistory | ForEach-Object { $_ | ConvertFrom-Json -ErrorAction SilentlyContinue } | Where-Object { $_ }
        if ($history.Count -ge 4) {
            $recent = $history | Select-Object -Last 4
            $oldest = $recent[0].replan_rate
            $newest = $recent[-1].replan_rate
            $delta = $newest - $oldest
            if ($delta -gt 0.5) {
                $report.findings += "ReplanRate INCREASING over time: $oldest% -> $newest% (delta: +$([math]::Round($delta,2))%)"
                $report.root_causes += "System learning curve not flattening - may need tuning"
            }
            elseif ($delta -lt -0.5) {
                $report.findings += "ReplanRate DECREASING: $oldest% -> $newest% (delta: $([math]::Round($delta,2))%) - POSITIVE trend"
            }
            else {
                $report.findings += "ReplanRate STABLE: $oldest% -> $newest% (delta: $([math]::Round($delta,2))%)"
            }
        }
    }

    # 3. Check resonance ledger growth
    if (Test-Path $ledger) {
        $cutoff = (Get-Date).AddHours(-$Hours)
        $lines = Get-Content $ledger -Tail 1000
        $events = $lines | ForEach-Object { 
            try { $_ | ConvertFrom-Json } catch { $null }
        } | Where-Object { $_ -and $_.timestamp }
        
        $recent = $events | Where-Object { 
            try { [DateTime]$_.timestamp -gt $cutoff } catch { $false }
        }
        
        $report.findings += "Ledger events in last ${Hours}h: $($recent.Count)"
        
        # Group by 6-hour windows to see event rate
        $windows = $recent | Group-Object { 
            $dt = [DateTime]$_.timestamp
            [math]::Floor(($dt.Ticks - $cutoff.Ticks) / (6 * 3600 * 10000000))
        }
        
        if ($windows.Count -ge 2) {
            $early = ($windows[0..([math]::Min(1, $windows.Count - 1))] | Measure-Object -Property Count -Average).Average
            $late = ($windows[([math]::Max(0, $windows.Count - 2))..($windows.Count - 1)] | Measure-Object -Property Count -Average).Average
            $changePercent = if ($early -gt 0) { (($late - $early) / $early) * 100 } else { 0 }
            
            if ($changePercent -gt 20) {
                $report.findings += "Event rate INCREASING: early avg $([math]::Round($early,1))/6h -> late avg $([math]::Round($late,1))/6h (+$([math]::Round($changePercent,1))%)"
                $report.root_causes += "System activity ramping up - may indicate more correction cycles"
            }
            elseif ($changePercent -lt -20) {
                $report.findings += "Event rate DECREASING: early avg $([math]::Round($early,1))/6h -> late avg $([math]::Round($late,1))/6h ($([math]::Round($changePercent,1))%)"
            }
        }
        
        # Check evidence correction attempts
        $withEvidence = $recent | Where-Object { $_.evidence_correction }
        if ($withEvidence.Count -gt 0) {
            $avgAdded = ($withEvidence | Where-Object { $_.evidence_correction.added } | Measure-Object -Property { $_.evidence_correction.added } -Average).Average
            $report.findings += "Evidence added per correction attempt: $([math]::Round($avgAdded,2)) docs"
            
            if ($avgAdded -lt 0.3) {
                $report.root_causes += "Evidence retrieval yield is LOW - vector store may need reindexing"
            }
        }
    }

    # Generate recommendations
    if ($report.root_causes -contains "RAG retrieval not finding relevant context efficiently") {
        $report.recommendations += "1. Reindex vector store: scripts\reindex_vector_store.ps1"
        $report.recommendations += "2. Increase evidence_gate.top_k from 6 to 8-10"
    }
    if ($report.root_causes -contains "Evidence retrieval quality degrading over time") {
        $report.recommendations += "Raise evidence_gate.min_relevance from 0.20 to 0.25-0.30"
    }
    if ($report.root_causes -contains "System learning curve not flattening - may need tuning") {
        $report.recommendations += "Consider reducing policy check frequency or throttle learning cycles"
    }
    if ($report.root_causes -contains "Local channel showing gradual slowdown") {
        $report.recommendations += "Check local LLM proxy health and GPU utilization"
    }
    
    # Diagnosis summary
    Write-Host "`n=== SYSTEM SLOWDOWN ANALYSIS ===" -ForegroundColor Magenta
    Write-Host "Timestamp: $($report.timestamp)" -ForegroundColor Gray
    Write-Host "`nFINDINGS:" -ForegroundColor Yellow
    $report.findings | ForEach-Object { Write-Host "  • $_" }
    
    Write-Host "`nROOT CAUSES:" -ForegroundColor Red
    if ($report.root_causes.Count -eq 0) {
        Write-Ok "  ✓ No major root causes identified - slowdown may be temporary or within normal variance"
    }
    else {
        $report.root_causes | ForEach-Object { Write-Host "  ⚠ $_" }
    }
    
    Write-Host "`nRECOMMENDATIONS:" -ForegroundColor Cyan
    if ($report.recommendations.Count -eq 0) {
        Write-Info "  • System appears healthy - continue monitoring"
        Write-Info "  • Current performance within acceptable range for learning phase"
    }
    else {
        $report.recommendations | ForEach-Object { Write-Host "  → $_" }
    }
    
    # Save report
    $outJson = Join-Path $ws 'outputs\slowdown_analysis_latest.json'
    $report | ConvertTo-Json -Depth 10 | Set-Content $outJson -Encoding UTF8
    Write-Host "`nReport saved: $outJson" -ForegroundColor Green
    
    exit 0
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}