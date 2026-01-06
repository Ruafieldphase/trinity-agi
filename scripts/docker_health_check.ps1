# Docker 백엔드 상태 모니터링 및 최적화 스크립트
# 목적: 컨테이너 상태 확인, 리소스 사용량 추적, 비정상 서비스 자동 재시작

param(
    [string]$Action = "check",  # check, restart, prune, health
    [int]$MonitoringInterval = 60  # 모니터링 간격 (초)
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

function Check-Docker {
    Write-Log "Docker 상태 확인 중..." "Info"

    # Docker Desktop 실행 여부 확인
    $docker = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
    if (!$docker) {
        Write-Log "Docker Desktop이 실행 중이 아님" "Error"
        return $false
    }

    Write-Log "Docker Desktop 실행 중 (PID: $($docker.Id))" "Success"
    return $true
}

function Get-ContainerStatus {
    Write-Log "컨테이너 상태 확인 중..." "Info"

    try {
        # 필수 컨테이너
        $requiredContainers = @("agent-system-postgres", "agent-system-redis", "agent-system-api")

        # 현재 실행 중인 컨테이너 목록
        $runningContainers = docker ps --format "table {{.Names}}" 2>$null | Select-Object -Skip 1

        $status = @{}
        foreach ($container in $requiredContainers) {
            if ($runningContainers -contains $container) {
                Write-Log "✓ $container: 실행 중" "Success"
                $status[$container] = "Running"
            }
            else {
                Write-Log "✗ $container: 중지됨" "Warning"
                $status[$container] = "Stopped"
            }
        }

        return $status
    }
    catch {
        Write-Log "컨테이너 상태 확인 중 오류: $_" "Error"
        return $null
    }
}

function Get-ContainerMetrics {
    Write-Log "컨테이너 리소스 사용량 확인 중..." "Info"

    try {
        $metrics = docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>$null | Select-Object -Skip 1

        if ($metrics) {
            foreach ($metric in $metrics) {
                if ($metric) {
                    $parts = $metric -split '\s+' | Where-Object { $_ }
                    if ($parts.Count -ge 3) {
                        $container = $parts[0]
                        $cpu = $parts[1]
                        $mem = $parts[2..3] -join ' '
                        Write-Log "$container - CPU: $cpu, 메모리: $mem" "Info"
                    }
                }
            }
        }
    }
    catch {
        Write-Log "리소스 사용량 조회 중 오류: $_" "Error"
    }
}

function Restart-Container {
    param([string]$ContainerName)

    Write-Log "$ContainerName 재시작 중..." "Warning"

    try {
        docker restart $ContainerName 2>$null
        Start-Sleep -Seconds 10

        # 재시작 후 상태 확인
        $running = docker ps --format "table {{.Names}}" 2>$null | Select-Object -Skip 1 | Where-Object { $_ -eq $ContainerName }

        if ($running) {
            Write-Log "$ContainerName 재시작 완료" "Success"
            return $true
        }
        else {
            Write-Log "$ContainerName 재시작 실패" "Error"
            return $false
        }
    }
    catch {
        Write-Log "$ContainerName 재시작 중 오류: $_" "Error"
        return $false
    }
}

function Health-Check {
    Write-Log "전체 헬스 체크 수행 중..." "Info"

    # 1. Docker 상태 확인
    if (!(Check-Docker)) {
        Write-Log "Docker Desktop을 시작해주세요" "Error"
        return $false
    }

    # 2. 컨테이너 상태 확인
    $containerStatus = Get-ContainerStatus
    if (!$containerStatus) {
        Write-Log "컨테이너 상태를 확인할 수 없습니다" "Error"
        return $false
    }

    # 3. 리소스 사용량 확인
    Get-ContainerMetrics

    # 4. PostgreSQL 연결 확인
    Write-Log "PostgreSQL 연결 확인 중..." "Info"
    try {
        $result = docker exec agent-system-postgres pg_isready -U agent_user -d agent_system 2>$null
        if ($result) {
            Write-Log "PostgreSQL 연결 성공" "Success"
        }
    }
    catch {
        Write-Log "PostgreSQL 연결 실패" "Error"
    }

    # 5. Redis 연결 확인
    Write-Log "Redis 연결 확인 중..." "Info"
    try {
        $result = docker exec agent-system-redis redis-cli ping 2>$null
        if ($result -like "*PONG*") {
            Write-Log "Redis 연결 성공" "Success"
        }
    }
    catch {
        Write-Log "Redis 연결 실패" "Error"
    }

    # 6. API 헬스 체크
    Write-Log "Agent API 헬스 체크 중..." "Info"
    try {
        $health = Invoke-WebRequest -Uri "http://localhost:5000/api/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($health.StatusCode -eq 200) {
            Write-Log "Agent API 정상" "Success"
        }
    }
    catch {
        Write-Log "Agent API 응답 없음 또는 오류" "Warning"
    }

    Write-Log "헬스 체크 완료" "Success"
    return $true
}

function Cleanup-Docker {
    Write-Log "Docker 정크 정리 수행 중..." "Warning"

    try {
        # 1. 정지된 컨테이너 제거
        Write-Log "정지된 컨테이너 제거 중..."
        docker container prune -f 2>$null

        # 2. 사용되지 않는 이미지 제거
        Write-Log "사용되지 않는 이미지 제거 중..."
        docker image prune -a -f 2>$null

        # 3. 정크 볼륨 제거
        Write-Log "정크 볼륨 제거 중..."
        docker volume prune -f 2>$null

        Write-Log "Docker 정크 정리 완료" "Success"
    }
    catch {
        Write-Log "Docker 정크 정리 중 오류: $_" "Error"
    }
}

function Monitor-Docker {
    Write-Log "Docker 모니터링 시작 (간격: ${MonitoringInterval}초)" "Info"

    $logFile = "$WorkspaceRoot\outputs\docker_monitoring.log"

    while ($true) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

        # 헬스 체크 수행
        $healthy = Health-Check

        # 로그 파일에 기록
        $logEntry = @{
            Timestamp = $timestamp
            Status = if ($healthy) { "Healthy" } else { "Unhealthy" }
        } | ConvertTo-Json

        Add-Content -Path $logFile -Value $logEntry

        Write-Log "모니터링 대기 중..." "Info"
        Start-Sleep -Seconds $MonitoringInterval
    }
}

# 메인 실행
switch ($Action.ToLower()) {
    "check" {
        if (Health-Check) {
            Write-Log "모든 서비스 정상" "Success"
        }
        else {
            Write-Log "일부 서비스 비정상" "Error"
        }
    }
    "restart" {
        Write-Log "모든 컨테이너 재시작 중..." "Warning"
        $containers = @("agent-system-api", "agent-system-redis", "agent-system-postgres")
        foreach ($container in $containers) {
            Restart-Container $container
        }
    }
    "prune" {
        Cleanup-Docker
    }
    "health" {
        Health-Check
    }
    "monitor" {
        Monitor-Docker -MonitoringInterval $MonitoringInterval
    }
    default {
        Write-Log "사용 방법: .\docker_health_check.ps1 -Action [check|restart|prune|health|monitor] -MonitoringInterval 60" "Info"
    }
}