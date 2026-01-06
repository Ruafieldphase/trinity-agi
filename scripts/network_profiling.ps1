#Requires -Version 5.1
<#
.SYNOPSIS
    Network and Process Profiling for Phase 8.5 Task 1
.DESCRIPTION
    Off-peak 시간 네트워크 및 프로세스 프로파일링
    Gateway 병목 지점 발견
.PARAMETER Duration
    프로파일링 지속 시간 (초)
.PARAMETER OutJson
    결과 JSON 파일 경로
.EXAMPLE
    .\network_profiling.ps1 -Duration 300 -OutJson outputs\network_profile.json
#>

param(
    [int]$Duration = 60,
    [string]$OutJson = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\network_profile_latest.json",
    [switch]$Verbose
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

Write-Host "=== Network Profiling Start ===" -ForegroundColor Cyan
Write-Host "Duration: $Duration seconds" -ForegroundColor White
Write-Host "Output: $OutJson" -ForegroundColor White
Write-Host ""

# 결과 객체 초기화
$result = @{
    timestamp        = Get-Date -Format "o"
    duration_seconds = $Duration
    samples          = @()
    summary          = @{}
}

$startTime = Get-Date
$iteration = 0

Write-Host "Collecting samples..." -ForegroundColor Yellow

# 샘플링 루프 (5초 간격)
$interval = 5
$totalIterations = [Math]::Ceiling($Duration / $interval)

while ((Get-Date) -lt $startTime.AddSeconds($Duration)) {
    $iteration++
    $progress = [Math]::Round(($iteration / $totalIterations) * 100)
    
    Write-Progress -Activity "Network Profiling" -Status "Sample $iteration/$totalIterations" -PercentComplete $progress
    
    $sample = @{
        timestamp = Get-Date -Format "o"
        iteration = $iteration
    }
    
    try {
        # 1. CPU 사용률
        $cpu = Get-Counter '\Processor(_Total)\% Processor Time' -ErrorAction SilentlyContinue
        if ($cpu) {
            $sample.cpu_percent = [Math]::Round($cpu.CounterSamples[0].CookedValue, 2)
        }
        
        # 2. 메모리 사용률
        $mem = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
        if ($mem) {
            $totalMB = [Math]::Round($mem.TotalVisibleMemorySize / 1KB, 0)
            $freeMB = [Math]::Round($mem.FreePhysicalMemory / 1KB, 0)
            $usedMB = $totalMB - $freeMB
            $sample.memory_used_mb = $usedMB
            $sample.memory_total_mb = $totalMB
            $sample.memory_percent = [Math]::Round(($usedMB / $totalMB) * 100, 2)
        }
        
        # 3. 네트워크 트래픽 (모든 인터페이스)
        $netCounters = Get-Counter '\Network Interface(*)\Bytes Total/sec' -ErrorAction SilentlyContinue
        if ($netCounters) {
            $totalBytesPerSec = ($netCounters.CounterSamples | Where-Object { $_.InstanceName -notlike '*isatap*' -and $_.InstanceName -notlike '*Pseudo*' } | Measure-Object -Property CookedValue -Sum).Sum
            $sample.network_bytes_per_sec = [Math]::Round($totalBytesPerSec, 0)
            $sample.network_mbps = [Math]::Round(($totalBytesPerSec * 8) / 1MB, 2)
        }
        
        # 4. 디스크 I/O
        $disk = Get-Counter '\PhysicalDisk(_Total)\Disk Bytes/sec' -ErrorAction SilentlyContinue
        if ($disk) {
            $sample.disk_bytes_per_sec = [Math]::Round($disk.CounterSamples[0].CookedValue, 0)
            $sample.disk_mbps = [Math]::Round($disk.CounterSamples[0].CookedValue / 1MB, 2)
        }
        
        # 5. 상위 CPU 사용 프로세스 (Top 5)
        $topProcesses = Get-Process | 
        Where-Object { $_.CPU -gt 0 } | 
        Sort-Object CPU -Descending | 
        Select-Object -First 5 -Property Name, CPU, WorkingSet64, Id
        
        $sample.top_processes = @($topProcesses | ForEach-Object {
                @{
                    name        = $_.Name
                    cpu_seconds = [Math]::Round($_.CPU, 2)
                    memory_mb   = [Math]::Round($_.WorkingSet64 / 1MB, 0)
                    pid         = $_.Id
                }
            })
        
        # 6. 네트워크 연결 (Established)
        $connections = Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue | 
        Where-Object { $_.OwningProcess -ne 0 } |
        Group-Object -Property OwningProcess |
        Select-Object -First 10
        
        $sample.network_connections = @($connections | ForEach-Object {
                $proc = Get-Process -Id $_.Name -ErrorAction SilentlyContinue
                @{
                    pid              = $_.Name
                    process_name     = if ($proc) { $proc.Name } else { "Unknown" }
                    connection_count = $_.Count
                }
            })
        
        if ($Verbose) {
            Write-Host "[Sample $iteration] CPU: $($sample.cpu_percent)%, Mem: $($sample.memory_percent)%, Net: $($sample.network_mbps) Mbps" -ForegroundColor Gray
        }
        
    }
    catch {
        Write-Host "  Warning: Sample $iteration failed: $_" -ForegroundColor Yellow
        $sample.error = $_.Exception.Message
    }
    
    $result.samples += $sample
    
    # 다음 샘플까지 대기
    Start-Sleep -Seconds $interval
}

Write-Progress -Activity "Network Profiling" -Completed

# 통계 계산
Write-Host "`nCalculating summary..." -ForegroundColor Yellow

$validSamples = $result.samples | Where-Object { $null -ne $_.cpu_percent }

if ($validSamples.Count -gt 0) {
    # CPU 통계
    $cpuValues = @($validSamples.cpu_percent)
    $memPercentValues = @($validSamples.memory_percent)
    $memUsedValues = @($validSamples.memory_used_mb)
    $netMbpsValues = @($validSamples.network_mbps)
    $diskMbpsValues = @($validSamples.disk_mbps)
    
    $result.summary = @{
        sample_count = $validSamples.Count
        cpu          = @{
            mean = [Math]::Round(($cpuValues | Measure-Object -Average).Average, 2)
            min  = [Math]::Round(($cpuValues | Measure-Object -Minimum).Minimum, 2)
            max  = [Math]::Round(($cpuValues | Measure-Object -Maximum).Maximum, 2)
        }
        memory       = @{
            mean_percent = [Math]::Round(($memPercentValues | Measure-Object -Average).Average, 2)
            mean_used_mb = [Math]::Round(($memUsedValues | Measure-Object -Average).Average, 0)
        }
        network      = @{
            mean_mbps = [Math]::Round(($netMbpsValues | Measure-Object -Average).Average, 2)
            max_mbps  = [Math]::Round(($netMbpsValues | Measure-Object -Maximum).Maximum, 2)
        }
        disk         = @{
            mean_mbps = [Math]::Round(($diskMbpsValues | Measure-Object -Average).Average, 2)
            max_mbps  = [Math]::Round(($diskMbpsValues | Measure-Object -Maximum).Maximum, 2)
        }
    }
    
    # Top processes 집계
    $allProcesses = @{}
    foreach ($sample in $validSamples) {
        foreach ($proc in $sample.top_processes) {
            if (-not $allProcesses.ContainsKey($proc.name)) {
                $allProcesses[$proc.name] = @{
                    name          = $proc.name
                    appearances   = 0
                    total_cpu     = 0.0
                    max_memory_mb = 0
                }
            }
            $allProcesses[$proc.name].appearances++
            $allProcesses[$proc.name].total_cpu += $proc.cpu_seconds
            if ($proc.memory_mb -gt $allProcesses[$proc.name].max_memory_mb) {
                $allProcesses[$proc.name].max_memory_mb = $proc.memory_mb
            }
        }
    }
    
    $result.summary.frequent_processes = @($allProcesses.Values | 
        Sort-Object -Property appearances -Descending | 
        Select-Object -First 10 |
        ForEach-Object {
            @{
                name              = $_.name
                appearances       = $_.appearances
                frequency_percent = [Math]::Round(($_.appearances / $validSamples.Count) * 100, 1)
                avg_cpu_seconds   = [Math]::Round($_.total_cpu / $_.appearances, 2)
                max_memory_mb     = $_.max_memory_mb
            }
        })
}

# JSON 저장
$outDir = Split-Path -Parent $OutJson
if (-not (Test-Path -LiteralPath $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

$result | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutJson -Encoding utf8 -Force

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Samples collected: $($result.summary.sample_count)" -ForegroundColor White
Write-Host "CPU: avg $($result.summary.cpu.mean)%, max $($result.summary.cpu.max)%" -ForegroundColor White
Write-Host "Memory: avg $($result.summary.memory.mean_percent)%" -ForegroundColor White
Write-Host "Network: avg $($result.summary.network.mean_mbps) Mbps, max $($result.summary.network.max_mbps) Mbps" -ForegroundColor White
Write-Host "Disk: avg $($result.summary.disk.mean_mbps) MB/s, max $($result.summary.disk.max_mbps) MB/s" -ForegroundColor White

if ($result.summary.frequent_processes) {
    Write-Host "`nTop Frequent Processes:" -ForegroundColor Cyan
    foreach ($proc in $result.summary.frequent_processes | Select-Object -First 5) {
        Write-Host "  $($proc.name): $($proc.frequency_percent)% frequency, avg $($proc.avg_cpu_seconds)s CPU" -ForegroundColor Gray
    }
}

Write-Host "`nOutput saved: $OutJson" -ForegroundColor Green
Write-Host "=== Network Profiling Complete ===" -ForegroundColor Cyan

exit 0