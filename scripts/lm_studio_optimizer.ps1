# LM Studio 성능 최적화 및 모니터링 스크립트
# 목적: CPU 점유율 관리, 메모리 누수 감시, 자동 최적화

param(
    [string]$Action = "monitor",  # monitor, stop, start, optimize
    [int]$CPUThreshold = 80,      # CPU 임계값 (%)
    [int]$MemoryThreshold = 2048, # 메모리 임계값 (MB)
    [int]$MonitoringInterval = 30  # 모니터링 간격 (초)
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



# 색상 정의
$colors = @{
    Success = [System.ConsoleColor]::Green
    Warning = [System.ConsoleColor]::Yellow
    Error = [System.ConsoleColor]::Red
    Info = [System.ConsoleColor]::Cyan
}

function Write-Log {
    param([string]$Message, [string]$Level = "Info")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = $colors[$Level]
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
}

function Get-LMStudioStatus {
    $processes = @{
        Studio = Get-Process -Name "LM Studio" -ErrorAction SilentlyContinue
        Support = Get-Process -Name "LM_Support" -ErrorAction SilentlyContinue
    }
    return $processes
}

function Get-SystemMetrics {
    param($ProcessList)

    $metrics = @{
        Timestamp = Get-Date
        LMStudioCount = ($ProcessList.Studio | Measure-Object).Count
        LMSupportCount = ($ProcessList.Support | Measure-Object).Count
        TotalCPU = 0
        TotalMemory = 0
    }

    if ($ProcessList.Studio) {
        $metrics.TotalCPU += ($ProcessList.Studio | Measure-Object -Property CPU -Sum).Sum
        $metrics.TotalMemory += ($ProcessList.Studio | Measure-Object -Property WorkingSet -Sum).Sum / 1MB
    }

    if ($ProcessList.Support) {
        $metrics.TotalCPU += ($ProcessList.Support | Measure-Object -Property CPU -Sum).Sum
        $metrics.TotalMemory += ($ProcessList.Support | Measure-Object -Property WorkingSet -Sum).Sum / 1MB
    }

    return $metrics
}

function Stop-LMStudio {
    Write-Log "LM Studio 프로세스 종료 중..." "Warning"

    try {
        # LM_Support 종료 (우선순위 높음)
        $support = Get-Process -Name "LM_Support" -ErrorAction SilentlyContinue
        if ($support) {
            Write-Log "LM_Support (PID: $($support.Id)) 종료 중..."
            Stop-Process -Name "LM_Support" -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
            Write-Log "LM_Support 종료 완료" "Success"
        }

        # LM Studio 종료
        $studio = Get-Process -Name "LM Studio" -ErrorAction SilentlyContinue
        if ($studio) {
            foreach ($proc in $studio) {
                Write-Log "LM Studio (PID: $($proc.Id)) 종료 중..."
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            }
            Start-Sleep -Seconds 2
            Write-Log "LM Studio 종료 완료" "Success"
        }

        Write-Log "모든 LM Studio 프로세스 종료 완료" "Success"
    }
    catch {
        Write-Log "LM Studio 종료 중 오류 발생: $_" "Error"
    }
}

function Optimize-LMStudio {
    Write-Log "LM Studio 최적화 수행 중..." "Info"

    $processes = Get-LMStudioStatus

    # 1. 다중 인스턴스 감지 및 정리
    if ($processes.Studio.Count -gt 1) {
        Write-Log "다중 LM Studio 인스턴스 감지 ($($processes.Studio.Count)개) - 정리 중..." "Warning"

        # 가장 최근 프로세스만 유지, 나머지는 종료
        $sorted = $processes.Studio | Sort-Object -Property StartTime -Descending
        for ($i = 1; $i -lt $sorted.Count; $i++) {
            Write-Log "추가 인스턴스 종료: PID $($sorted[$i].Id)"
            Stop-Process -Id $sorted[$i].Id -Force -ErrorAction SilentlyContinue
        }
    }

    # 2. CPU 점유율 확인
    $metrics = Get-SystemMetrics $processes
    if ($metrics.TotalCPU -gt $CPUThreshold) {
        Write-Log "CPU 점유율 초과 ($($metrics.TotalCPU)% > $CPUThreshold%) - 재시작 권장" "Warning"
        return $false
    }

    # 3. 메모리 사용량 확인
    if ($metrics.TotalMemory -gt $MemoryThreshold) {
        Write-Log "메모리 사용량 초과 ($([math]::Round($metrics.TotalMemory, 2))MB > ${MemoryThreshold}MB) - 재시작 권장" "Warning"
        return $false
    }

    Write-Log "LM Studio 상태 정상 - CPU: $($metrics.TotalCPU)%, 메모리: $([math]::Round($metrics.TotalMemory, 2))MB" "Success"
    return $true
}

function Monitor-LMStudio {
    Write-Log "LM Studio 모니터링 시작 (간격: ${MonitoringInterval}초, CPU 임계값: ${CPUThreshold}%, 메모리 임계값: ${MemoryThreshold}MB)" "Info"

    $logFile = "$WorkspaceRoot\outputs\lm_studio_monitoring.log"
    $startTime = Get-Date

    while ($true) {
        $processes = Get-LMStudioStatus

        if (!$processes.Studio -and !$processes.Support) {
            Write-Log "LM Studio 프로세스 실행 중 아님" "Warning"
            Start-Sleep -Seconds $MonitoringInterval
            continue
        }

        $metrics = Get-SystemMetrics $processes

        # 로그 파일에 기록
        $logEntry = @{
            Timestamp = $metrics.Timestamp
            LMStudioCount = $metrics.LMStudioCount
            LMSupportCount = $metrics.LMSupportCount
            CPU = [math]::Round($metrics.TotalCPU, 2)
            Memory_MB = [math]::Round($metrics.TotalMemory, 2)
        } | ConvertTo-Json

        Add-Content -Path $logFile -Value $logEntry

        # 콘솔 출력
        Write-Log "Status - LM Studio: $($metrics.LMStudioCount), LM_Support: $($metrics.LMSupportCount), CPU: $([math]::Round($metrics.TotalCPU, 2))%, 메모리: $([math]::Round($metrics.TotalMemory, 2))MB"

        # 경고 조건 확인
        if ($metrics.TotalCPU -gt $CPUThreshold) {
            Write-Log "경고: CPU 점유율 초과 ($([math]::Round($metrics.TotalCPU, 2))% > $CPUThreshold%)" "Warning"
        }

        if ($metrics.TotalMemory -gt $MemoryThreshold) {
            Write-Log "경고: 메모리 사용량 초과 ($([math]::Round($metrics.TotalMemory, 2))MB > ${MemoryThreshold}MB)" "Warning"
        }

        # 다중 인스턴스 감지
        if ($metrics.LMStudioCount -gt 1 -or $metrics.LMSupportCount -gt 1) {
            Write-Log "경고: 다중 인스턴스 감지됨" "Warning"
            Optimize-LMStudio | Out-Null
        }

        Start-Sleep -Seconds $MonitoringInterval
    }
}

# 메인 실행
switch ($Action.ToLower()) {
    "stop" {
        Stop-LMStudio
    }
    "optimize" {
        if (Optimize-LMStudio) {
            Write-Log "LM Studio 최적화 완료" "Success"
        }
        else {
            Write-Log "LM Studio 재시작 필요" "Warning"
            Stop-LMStudio
        }
    }
    "monitor" {
        Monitor-LMStudio
    }
    default {
        Write-Log "사용 방법: .\lm_studio_optimizer.ps1 -Action [stop|optimize|monitor] -CPUThreshold 80 -MemoryThreshold 2048 -MonitoringInterval 30" "Info"
    }
}