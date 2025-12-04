# AI 시스템 통합 시작 스크립트
# 목적: 모든 구성 요소를 올바른 순서로 시작하고 헬스 체크 수행

param(
    [switch]$SkipLMStudio = $false,  # LM Studio 시작 건너뛰기
    [switch]$SkipDocker = $false,     # Docker 시작 건너뛰기
    [int]$StartupTimeout = 120        # 시작 타임아웃 (초)
)

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

function Start-Component {
    param(
        [string]$ComponentName,
        [scriptblock]$StartAction,
        [scriptblock]$HealthCheck
    )

    Write-Log "[$ComponentName] 시작 중..." "Info"
    $startTime = Get-Date

    try {
        & $StartAction

        # 헬스 체크
        $healthy = $false
        $elapsed = 0

        while ($elapsed -lt $StartupTimeout) {
            Start-Sleep -Seconds 2
            $elapsed = ((Get-Date) - $startTime).TotalSeconds

            try {
                if (& $HealthCheck) {
                    $healthy = $true
                    break
                }
            }
            catch {
                # 아직 준비 중
            }
        }

        if ($healthy) {
            $duration = [math]::Round($elapsed, 2)
            Write-Log "[$ComponentName] 시작 완료 (소요시간: ${duration}초)" "Success"
            return $true
        }
        else {
            Write-Log "[$ComponentName] 시작 타임아웃 (${StartupTimeout}초)" "Error"
            return $false
        }
    }
    catch {
        Write-Log "[$ComponentName] 시작 중 오류: $_" "Error"
        return $false
    }
}

function Start-Docker {
    Write-Log "Docker 시작 수행 중..." "Info"

    # Docker Desktop 실행 상태 확인
    $docker = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
    if ($docker) {
        Write-Log "Docker Desktop이 이미 실행 중입니다" "Info"
        return
    }

    # Docker Desktop 시작
    Write-Log "Docker Desktop 시작 중..."
    try {
        & "C:\Program Files\Docker\Docker\Docker.exe"
        Start-Sleep -Seconds 5
    }
    catch {
        Write-Log "Docker Desktop 시작 실패, 다른 경로 시도 중..."
        try {
            Start-Process -FilePath "Docker Desktop" -ErrorAction Stop
            Start-Sleep -Seconds 5
        }
        catch {
            Write-Log "Docker Desktop을 찾을 수 없습니다" "Error"
            throw
        }
    }
}

function Check-DockerRunning {
    $running = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
    return $null -ne $running
}

function Start-DockerServices {
    Write-Log "Docker Compose 서비스 시작 중..." "Info"

    $composeFile = "C:\workspace\agi\session_memory\docker-compose.yml"

    if (!(Test-Path $composeFile)) {
        Write-Log "docker-compose.yml 파일을 찾을 수 없습니다: $composeFile" "Error"
        throw
    }

    Push-Location (Split-Path -Parent $composeFile)
    try {
        # 필수 서비스만 시작 (postgres, redis, agent-api)
        docker-compose up -d postgres redis agent-api 2>$null
    }
    finally {
        Pop-Location
    }
}

function Check-PostgreSQL {
    try {
        $result = docker exec agent-system-postgres pg_isready -U agent_user -d agent_system 2>$null
        return $null -ne $result
    }
    catch {
        return $false
    }
}

function Check-Redis {
    try {
        $result = docker exec agent-system-redis redis-cli ping 2>$null
        return $result -like "*PONG*"
    }
    catch {
        return $false
    }
}

function Check-AgentAPI {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/api/health" `
                                      -TimeoutSec 5 `
                                      -ErrorAction SilentlyContinue
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

function Start-LMStudio {
    Write-Log "LM Studio 시작 중..." "Info"

    # LM Studio 설치 경로 확인
    $lmStudioPath = @(
        "C:\Users\$env:USERNAME\AppData\Local\Programs\LM Studio\LM Studio.exe",
        "${env:ProgramFiles}\LM Studio\LM Studio.exe",
        "${env:ProgramFiles(x86)}\LM Studio\LM Studio.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1

    if (!$lmStudioPath) {
        Write-Log "LM Studio 설치 경로를 찾을 수 없습니다" "Error"
        throw
    }

    try {
        Start-Process -FilePath $lmStudioPath -WindowStyle Minimized
        Start-Sleep -Seconds 3
    }
    catch {
        Write-Log "LM Studio 시작 실패: $_" "Error"
        throw
    }
}

function Check-LMStudioReady {
    # LM Studio 포트 연결 시도
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/v1/models" `
                                      -TimeoutSec 5 `
                                      -ErrorAction SilentlyContinue
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

# 메인 실행
Write-Log "================== AI 시스템 시작 ==================" "Info"
Write-Log "설정: SkipLMStudio=$SkipLMStudio, SkipDocker=$SkipDocker, Timeout=${StartupTimeout}초" "Info"

$results = @{}
$startTime = Get-Date

# 1. Docker 시작
if (!$SkipDocker) {
    $result = Start-Component `
        -ComponentName "Docker" `
        -StartAction { Start-Docker } `
        -HealthCheck { Check-DockerRunning }
    $results["Docker"] = $result

    if (!$result) {
        Write-Log "Docker 시작 실패 - 중단" "Error"
        exit 1
    }

    # 2. Docker Compose 서비스 시작
    $result = Start-Component `
        -ComponentName "PostgreSQL" `
        -StartAction { Start-DockerServices } `
        -HealthCheck { Check-PostgreSQL }
    $results["PostgreSQL"] = $result

    # 3. Redis 확인
    Write-Log "Redis 상태 확인 중..." "Info"
    Start-Sleep -Seconds 3
    if (Check-Redis) {
        Write-Log "Redis 준비 완료" "Success"
        $results["Redis"] = $true
    }
    else {
        Write-Log "Redis 준비 중..." "Warning"
        $results["Redis"] = $false
    }

    # 4. Agent API 확인
    Write-Log "Agent API 상태 확인 중..." "Info"
    Start-Sleep -Seconds 3
    if (Check-AgentAPI) {
        Write-Log "Agent API 준비 완료" "Success"
        $results["AgentAPI"] = $true
    }
    else {
        Write-Log "Agent API 준비 중..." "Warning"
        $results["AgentAPI"] = $false
    }
}

# 3. LM Studio 시작 (비동기)
if (!$SkipLMStudio) {
    $result = Start-Component `
        -ComponentName "LM Studio" `
        -StartAction { Start-LMStudio } `
        -HealthCheck { Check-LMStudioReady }
    $results["LMStudio"] = $result
}

# 최종 요약
Write-Log "================== 시작 결과 요약 ==================" "Info"
$totalTime = ((Get-Date) - $startTime).TotalSeconds

foreach ($component in $results.Keys) {
    $status = if ($results[$component]) { "✓ 준비 완료" } else { "⚠ 준비 중" }
    $color = if ($results[$component]) { "Success" } else { "Warning" }
    Write-Log "$component: $status" $color
}

Write-Log "총 소요시간: $([math]::Round($totalTime, 2))초" "Info"

# 최종 상태 확인
$allReady = $results.Values | Where-Object { $_ -eq $true } | Measure-Object | Select-Object -ExpandProperty Count -eq $results.Count

if ($allReady) {
    Write-Log "모든 시스템 준비 완료!" "Success"
    Write-Log "접근 가능한 엔드포인트:" "Info"
    Write-Log "  - Agent API: http://localhost:5000" "Info"
    Write-Log "  - LM Studio: http://localhost:8080" "Info"
    Write-Log "  - PostgreSQL: localhost:5432" "Info"
    Write-Log "  - Redis: localhost:6379" "Info"
}
else {
    Write-Log "일부 시스템이 준비 중입니다 - 잠시 후 다시 확인해주세요" "Warning"
}

Write-Log "====================================================" "Info"
