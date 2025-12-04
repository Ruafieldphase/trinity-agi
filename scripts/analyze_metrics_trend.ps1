#Requires -Version 5.1
<#
.SYNOPSIS
    시계열 메트릭 데이터 분석 및 트렌드 리포트 생성
#>

param(
    [int]$Hours = 24,
    [string]$OutMd = "$PSScriptRoot\..\outputs\metrics_trend_latest.md",
    [string]$OutJson = "$PSScriptRoot\..\outputs\metrics_trend_latest.json"
)

$ErrorActionPreference = 'Stop'

function Get-Stats {
    param([array]$values)
    if ($values.Count -eq 0) { return $null }
    $validValues = $values | Where-Object { $_ -ne $null }
    if ($validValues.Count -eq 0) { return $null }
    
    $avg = ($validValues | Measure-Object -Average).Average
    $min = ($validValues | Measure-Object -Minimum).Minimum
    $max = ($validValues | Measure-Object -Maximum).Maximum
    
    return @{
        avg   = [math]::Round($avg, 2)
        min   = [math]::Round($min, 2)
        max   = [math]::Round($max, 2)
        count = $validValues.Count
    }
}

try {
    $metricsPath = "$PSScriptRoot\..\outputs\system_metrics.jsonl"
    
    if (-not (Test-Path $metricsPath)) {
        Write-Host "No metrics found. Run collect_system_metrics.ps1 first." -ForegroundColor Yellow
        exit 1
    }

    $cutoffTime = (Get-Date).AddHours(-$Hours)
    $metrics = Get-Content $metricsPath | ForEach-Object {
        try {
            $m = $_ | ConvertFrom-Json
            $ts = [DateTime]::Parse($m.timestamp)
            if ($ts -gt $cutoffTime) { $m }
        }
        catch {}
    }

    if ($metrics.Count -eq 0) {
        Write-Host "No metrics in last $Hours hours." -ForegroundColor Yellow
        exit 1
    }

    $firstTime = [DateTime]::Parse($metrics[0].timestamp)
    $lastTime = [DateTime]::Parse($metrics[-1].timestamp)
    $duration = ($lastTime - $firstTime).TotalHours

    $schedulerUptime = ($metrics | Where-Object { $_.scheduler.healthy -eq $true }).Count / $metrics.Count * 100
    $queueUptime = ($metrics | Where-Object { $_.queue.healthy -eq $true }).Count / $metrics.Count * 100
    $opsManagerUptime = ($metrics | Where-Object { $_.opsManager.running -eq $true }).Count / $metrics.Count * 100

    $queueLatency = Get-Stats ($metrics | ForEach-Object { $_.queue.latencyMs })
    $agiConfidence = Get-Stats ($metrics | ForEach-Object { $_.agi.confidence })
    $agiQuality = Get-Stats ($metrics | ForEach-Object { $_.agi.quality })
    $agi2ndPass = Get-Stats ($metrics | ForEach-Object { $_.agi.secondPassRate })
    
    $lumenLocal = Get-Stats ($metrics | ForEach-Object { $_.lumen.localMs })
    $lumenCloud = Get-Stats ($metrics | ForEach-Object { $_.lumen.cloudMs })
    $lumenGateway = Get-Stats ($metrics | ForEach-Object { $_.lumen.gatewayMs })
    
    $cpuStats = Get-Stats ($metrics | ForEach-Object { $_.system.cpuPercent })
    $memoryStats = Get-Stats ($metrics | ForEach-Object { $_.system.memoryPercent })

    $report = @{
        generatedAt = (Get-Date -Format "o")
        timeRange   = @{
            hours       = $Hours
            actualHours = [math]::Round($duration, 2)
            sampleCount = $metrics.Count
        }
        uptime      = @{
            schedulerPercent  = [math]::Round($schedulerUptime, 2)
            queuePercent      = [math]::Round($queueUptime, 2)
            opsManagerPercent = [math]::Round($opsManagerUptime, 2)
        }
        performance = @{
            queueLatencyMs = $queueLatency
            agiConfidence  = $agiConfidence
            agiQuality     = $agiQuality
            agi2ndPassRate = $agi2ndPass
        }
        lumen       = @{
            localMs   = $lumenLocal
            cloudMs   = $lumenCloud
            gatewayMs = $lumenGateway
        }
        system      = @{
            cpuPercent    = $cpuStats
            memoryPercent = $memoryStats
        }
    }

    $report | ConvertTo-Json -Depth 10 | Out-File $OutJson -Encoding UTF8

    $md = "# System Metrics Trend`n`n"
    $md += "**Generated**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"
    $md += "**Duration**: $([math]::Round($duration, 2)) hours`n"
    $md += "**Samples**: $($metrics.Count)`n`n"
    $md += "## Uptime`n`n"
    $md += "| Service | Uptime | Status |`n"
    $md += "|---------|--------|--------|`n"
    $md += "| Scheduler | $([math]::Round($schedulerUptime, 1))% | $(if($schedulerUptime -gt 95){'OK'}else{'WARN'}) |`n"
    $md += "| Queue | $([math]::Round($queueUptime, 1))% | $(if($queueUptime -gt 95){'OK'}else{'WARN'}) |`n"
    $md += "| OpsManager | $([math]::Round($opsManagerUptime, 1))% | $(if($opsManagerUptime -gt 95){'OK'}else{'WARN'}) |`n`n"
    
    if ($queueLatency) {
        $md += "## Queue Latency`n"
        $md += "- Avg: $($queueLatency.avg)ms`n"
        $md += "- Min/Max: $($queueLatency.min)/$($queueLatency.max)ms`n`n"
    }
    
    if ($agiConfidence) {
        $md += "## AGI Metrics`n"
        $md += "- Confidence: $($agiConfidence.avg)`n"
        $md += "- Quality: $($agiQuality.avg)`n"
        $md += "- 2nd Pass: $($agi2ndPass.avg)`n`n"
    }
    
    if ($cpuStats) {
        $md += "## System`n"
        $md += "- CPU: $($cpuStats.avg)%`n"
        $md += "- Memory: $($memoryStats.avg)%`n`n"
    }

    $md | Out-File $OutMd -Encoding UTF8

    Write-Host "Analysis complete!" -ForegroundColor Green
    Write-Host "  MD: $OutMd" -ForegroundColor Cyan
    Write-Host "  JSON: $OutJson" -ForegroundColor Cyan
    exit 0

}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
