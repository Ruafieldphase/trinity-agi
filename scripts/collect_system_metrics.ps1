#Requires -Version 5.1
<#
.SYNOPSIS
    시스템 메트릭을 수집하여 시계열 데이터로 저장

.DESCRIPTION
    - AI Scheduler, Queue Server, Ops Manager 상태
    - AGI 오케스트레이터 지표 (confidence, quality, 2nd pass)
    - Core 게이트웨이 응답 시간
    - 시스템 리소스 (CPU, Memory)
    - JSON Lines 형식으로 추가 저장

.PARAMETER OutJsonl
    출력 JSONL 파일 경로 (기본: outputs/system_metrics.jsonl)

.EXAMPLE
    .\collect_system_metrics.ps1
    .\collect_system_metrics.ps1 -OutJsonl "metrics.jsonl"
#>

param(
    [string]$OutJsonl = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\system_metrics.jsonl"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

try {
    $timestamp = Get-Date -Format "o"
    
    # 1. Scheduler 상태
    $schedulerHealthy = $false
    try {
        & "$PSScriptRoot\check_scheduler_status.ps1" > $null 2>&1
        $schedulerHealthy = ($LASTEXITCODE -eq 0)
    }
    catch {
        $schedulerHealthy = $false
    }

    # 2. Queue Server 상태
    $queueHealthy = $false
    $queueLatencyMs = $null
    try {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8091/api/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        $sw.Stop()
        $queueHealthy = ($response.StatusCode -eq 200)
        $queueLatencyMs = [math]::Round($sw.ElapsedMilliseconds, 1)
    }
    catch {
        $queueHealthy = $false
    }

    # 3. Ops Manager 상태
    $opsManagerRunning = $false
    $opsManagerLoops = 0
    $opsManagerStatusPath = "$WorkspaceRoot\outputs\ai_ops_manager_status.json"
    if (Test-Path $opsManagerStatusPath) {
        try {
            $opsStatus = Get-Content $opsManagerStatusPath -Raw | ConvertFrom-Json
            $opsManagerLoops = $opsStatus.loops
            # 최근 5분 이내 업데이트 확인
            $lastUpdate = [DateTime]::Parse($opsStatus.ts)
            $opsManagerRunning = ((Get-Date) - $lastUpdate).TotalMinutes -lt 5
        }
        catch {}
    }

    # 4. AGI 오케스트레이터 지표
    $agiConfidence = $null
    $agiQuality = $null
    $agi2ndPass = $null
    $agiStatePath = "$WorkspaceRoot\..\fdo_agi_repo\outputs\orchestrator_state_latest.json"
    if (Test-Path $agiStatePath) {
        try {
            $agiState = Get-Content $agiStatePath -Raw | ConvertFrom-Json
            $agiConfidence = [math]::Round($agiState.confidence, 3)
            $agiQuality = [math]::Round($agiState.quality, 3)
            $agi2ndPass = [math]::Round($agiState.second_pass_rate, 3)
        }
        catch {}
    }

    # 5. Core Gateway 응답 시간
    $CoreLocalMs = $null
    $CoreCloudMs = $null
    $CoreGatewayMs = $null
    
    try {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $null = Invoke-WebRequest -Uri "http://127.0.0.1:8080/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        $sw.Stop()
        $CoreLocalMs = [math]::Round($sw.ElapsedMilliseconds, 1)
    }
    catch {}

    try {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $null = Invoke-WebRequest -Uri "https://ion-api-64076350717.us-central1.run.app/api/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
        $sw.Stop()
        $CoreCloudMs = [math]::Round($sw.ElapsedMilliseconds, 1)
    }
    catch {}

    try {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $null = Invoke-WebRequest -Uri "https://Core-gateway-64076350717.us-central1.run.app/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
        $sw.Stop()
        $CoreGatewayMs = [math]::Round($sw.ElapsedMilliseconds, 1)
    }
    catch {}

    # 6. 시스템 리소스
    $cpuPercent = (Get-Counter '\Processor(_Total)\% Processor Time' -ErrorAction SilentlyContinue).CounterSamples[0].CookedValue
    $cpuPercent = [math]::Round($cpuPercent, 1)
    
    $memoryInfo = Get-CimInstance Win32_OperatingSystem
    $memoryUsedGB = [math]::Round(($memoryInfo.TotalVisibleMemorySize - $memoryInfo.FreePhysicalMemory) / 1MB, 2)
    $memoryTotalGB = [math]::Round($memoryInfo.TotalVisibleMemorySize / 1MB, 2)
    $memoryPercent = [math]::Round(($memoryUsedGB / $memoryTotalGB) * 100, 1)

    # 메트릭 객체 생성
    $metrics = [ordered]@{
        timestamp  = $timestamp
        scheduler  = @{
            healthy = $schedulerHealthy
        }
        queue      = @{
            healthy   = $queueHealthy
            latencyMs = $queueLatencyMs
        }
        opsManager = @{
            running = $opsManagerRunning
            loops   = $opsManagerLoops
        }
        agi        = @{
            confidence     = $agiConfidence
            quality        = $agiQuality
            secondPassRate = $agi2ndPass
        }
        Core      = @{
            localMs   = $CoreLocalMs
            cloudMs   = $CoreCloudMs
            gatewayMs = $CoreGatewayMs
        }
        system     = @{
            cpuPercent    = $cpuPercent
            memoryUsedGB  = $memoryUsedGB
            memoryTotalGB = $memoryTotalGB
            memoryPercent = $memoryPercent
        }
    }

    # JSONL 추가 (시계열 데이터)
    $json = $metrics | ConvertTo-Json -Compress -Depth 10
    Add-Content -Path $OutJsonl -Value $json -Encoding UTF8

    Write-Host "Metrics collected: $OutJsonl" -ForegroundColor Green
    exit 0

}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}