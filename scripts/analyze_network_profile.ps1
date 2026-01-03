#Requires -Version 5.1
<#
.SYNOPSIS
    Analyze Network Profile Results for Phase 8.5
.DESCRIPTION
    network_profile_latest.json 분석하여 병목 지점 발견
.EXAMPLE
    .\analyze_network_profile.ps1
#>

param(
    [string]$ProfileJson = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\network_profile_latest.json",
    [string]$OutMd = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\network_analysis_latest.md"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

Write-Host "=== Network Profile Analysis Start ===" -ForegroundColor Cyan
Write-Host "Input: $ProfileJson" -ForegroundColor White

if (-not (Test-Path -LiteralPath $ProfileJson)) {
    Write-Host "Error: Profile JSON not found: $ProfileJson" -ForegroundColor Red
    exit 1
}

# JSON 로드
$profile = Get-Content -Path $ProfileJson -Raw -Encoding UTF8 | ConvertFrom-Json

Write-Host "Loaded profile: $($profile.timestamp)" -ForegroundColor Green
Write-Host "Duration: $($profile.duration_seconds)s, Samples: $($profile.samples.Count)" -ForegroundColor White

# 분석 시작
$analysis = @"
# Network Profile Analysis Report

**Generated**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")  
**Profile Timestamp**: $($profile.timestamp)  
**Duration**: $($profile.duration_seconds) seconds  
**Sample Count**: $($profile.summary.sample_count)

---

## 📊 System Resource Summary

### CPU Usage
- **Average**: $($profile.summary.cpu.mean)%
- **Min**: $($profile.summary.cpu.min)%
- **Max**: $($profile.summary.cpu.max)%

### Memory Usage
- **Average**: $($profile.summary.memory.mean_percent)% ($($profile.summary.memory.mean_used_mb) MB)

### Network Traffic
- **Average**: $($profile.summary.network.mean_mbps) Mbps
- **Peak**: $($profile.summary.network.max_mbps) Mbps

### Disk I/O
- **Average**: $($profile.summary.disk.mean_mbps) MB/s
- **Peak**: $($profile.summary.disk.max_mbps) MB/s

---

## 🔍 Top Resource Consumers

"@

# Top Processes 분석
if ($profile.summary.frequent_processes) {
    $analysis += "`n### Frequent Processes (Top 5)`n`n"
    $analysis += "| Process | Frequency | Avg CPU (s) | Max Memory (MB) |`n"
    $analysis += "|---------|-----------|-------------|-----------------|`n"
    
    foreach ($proc in ($profile.summary.frequent_processes | Select-Object -First 5)) {
        $analysis += "| $($proc.name) | $($proc.frequency_percent)% | $($proc.avg_cpu_seconds) | $($proc.max_memory_mb) |`n"
    }
}

# 샘플별 변동성 분석
$cpuStdDev = 0
$netStdDev = 0
if ($profile.samples.Count -gt 1) {
    $cpuValues = @($profile.samples | Where-Object { $null -ne $_.cpu_percent } | ForEach-Object { $_.cpu_percent })
    $netValues = @($profile.samples | Where-Object { $null -ne $_.network_mbps } | ForEach-Object { $_.network_mbps })
    
    if ($cpuValues.Count -gt 1) {
        $cpuMean = ($cpuValues | Measure-Object -Average).Average
        $cpuVariance = ($cpuValues | ForEach-Object { [Math]::Pow($_ - $cpuMean, 2) } | Measure-Object -Average).Average
        $cpuStdDev = [Math]::Round([Math]::Sqrt($cpuVariance), 2)
    }
    
    if ($netValues.Count -gt 1) {
        $netMean = ($netValues | Measure-Object -Average).Average
        $netVariance = ($netValues | ForEach-Object { [Math]::Pow($_ - $netMean, 2) } | Measure-Object -Average).Average
        $netStdDev = [Math]::Round([Math]::Sqrt($netVariance), 2)
    }
}

$analysis += @"

---

## 📈 Variability Analysis

### CPU Variability
- **Standard Deviation**: $cpuStdDev%
- **Interpretation**: $(if ($cpuStdDev -lt 10) { "Low (Stable)" } elseif ($cpuStdDev -lt 20) { "Moderate" } else { "High (Unstable)" })

### Network Variability
- **Standard Deviation**: $netStdDev Mbps
- **Interpretation**: $(if ($netStdDev -lt 2) { "Low (Stable)" } elseif ($netStdDev -lt 5) { "Moderate" } else { "High (Bursty)" })

---

## 💡 Key Findings

"@

# 병목 지점 판단
$bottlenecks = @()

if ($profile.summary.cpu.max -gt 80) {
    $bottlenecks += "- 🔴 **CPU Bottleneck**: Peak usage $($profile.summary.cpu.max)% exceeds 80%"
}

if ($profile.summary.memory.mean_percent -gt 70) {
    $bottlenecks += "- 🔴 **Memory Pressure**: Average usage $($profile.summary.memory.mean_percent)% exceeds 70%"
}

if ($profile.summary.network.max_mbps -gt 50) {
    $bottlenecks += "- 🟡 **Network Saturation**: Peak traffic $($profile.summary.network.max_mbps) Mbps is high"
}

if ($profile.summary.disk.max_mbps -gt 100) {
    $bottlenecks += "- 🟡 **Disk I/O Pressure**: Peak $($profile.summary.disk.max_mbps) MB/s is high"
}

if ($bottlenecks.Count -eq 0) {
    $analysis += "`n✅ **No significant bottlenecks detected**`n"
    $analysis += "`nSystem resources are operating within normal parameters.`n"
}
else {
    foreach ($bottleneck in $bottlenecks) {
        $analysis += "`n$bottleneck`n"
    }
}

# 추천 사항
$analysis += @"

---

## 🎯 Recommendations

"@

if ($profile.summary.cpu.max -gt 80) {
    $analysis += @"
### CPU Optimization
- Identify high-CPU processes and optimize
- Consider process prioritization
- Evaluate async/parallel opportunities

"@
}

if ($profile.summary.network.mean_mbps -gt 5) {
    $analysis += @"
### Network Optimization
- Review network traffic patterns
- Consider request batching
- Evaluate caching strategies

"@
}

if ($cpuStdDev -gt 20) {
    $analysis += @"
### Stability Improvement
- High CPU variability detected
- Investigate workload spikes
- Consider load smoothing

"@
}

$analysis += @"

---

## 📁 Related Files

- Profile Data: `outputs/network_profile_latest.json`
- Phase 8.5 Document: `docs/PHASE8_5_PARADOXICAL_RESONANCE.md`

---

*Automatically generated by Phase 8.5 Task 1*
"@

# Markdown 저장
$outDir = Split-Path -Parent $OutMd
if (-not (Test-Path -LiteralPath $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

$analysis | Out-File -FilePath $OutMd -Encoding utf8 -Force

Write-Host "`n=== Analysis Complete ===" -ForegroundColor Cyan
Write-Host "Report saved: $OutMd" -ForegroundColor Green

# 요약 출력
Write-Host "`n=== Quick Summary ===" -ForegroundColor Yellow
Write-Host "CPU: avg $($profile.summary.cpu.mean)%, max $($profile.summary.cpu.max)%" -ForegroundColor White
Write-Host "Network: avg $($profile.summary.network.mean_mbps) Mbps, max $($profile.summary.network.max_mbps) Mbps" -ForegroundColor White
Write-Host "Bottlenecks: $($bottlenecks.Count)" -ForegroundColor $(if ($bottlenecks.Count -eq 0) { "Green" } else { "Yellow" })

exit 0