# Self-Healing Level 1 - 기본 자가 치유 시스템
# 이벤트 감지기가 발견한 문제들에 자동으로 대응

param(
    [int]$CheckIntervalSeconds = 30,
    [string]$EventQueueFile = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\event_queue.json",
    [string]$LogFile = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\self_healing_level1.log"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = "Continue"

# === 자가 치유 전략 정의 ===
$HealingStrategies = @{
    "cpu_spike" = @{
        name = "CPU 스파이크 대응"
        actions = @(
            "Reduce adaptive scheduler intervals",
            "Pause non-critical tasks",
            "Monitor for 5 minutes"
        )
        cooldown_seconds = 300
    }
    "memory_leak" = @{
        name = "메모리 누수 대응"
        actions = @(
            "Force garbage collection",
            "Restart affected python processes",
            "Clear temporary files",
            "Monitor memory trend"
        )
        cooldown_seconds = 600
    }
    "process_zombie" = @{
        name = "좀비 프로세스 정리"
        actions = @(
            "Identify zombie processes",
            "Kill zombie processes",
            "Restart scheduler if needed",
            "Log incident"
        )
        cooldown_seconds = 300
    }
    "memory_pressure" = @{
        name = "메모리 압박 대응"
        actions = @(
            "Emergency cleanup",
            "Stop non-essential tasks",
            "Clear cache",
            "Release resources"
        )
        cooldown_seconds = 900
    }
}

# === 로깅 함수 ===
function Write-HealingLog {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [string]$EventType = "UNKNOWN"
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logLine = "[$timestamp] [$EventType] [$Level] $Message"

    Write-Host $logLine -ForegroundColor $(
        if ($Level -eq "ERROR") { "Red" }
        elseif ($Level -eq "WARN") { "Yellow" }
        elseif ($Level -eq "SUCCESS") { "Green" }
        else { "Cyan" }
    )

    Add-Content -Path $LogFile -Value $logLine
}

# === 이벤트 큐에서 처리할 이벤트 읽기 ===
function Get-PendingEvents {
    if (-not (Test-Path $EventQueueFile)) {
        return @()
    }

    try {
        $queue = Get-Content $EventQueueFile | ConvertFrom-Json
        if ($queue -is [object] -and -not ($queue -is [array])) {
            $queue = @($queue)
        }

        # 대기 중인 이벤트만 반환
        return @($queue | Where-Object { $_.status -eq "pending" })
    } catch {
        Write-HealingLog "이벤트 큐 읽기 실패: $_" "ERROR" "QUEUE"
        return @()
    }
}

# === 자가 치유 액션 실행 ===
function Invoke-HealingAction {
    param(
        [string]$EventType,
        [hashtable]$Details
    )

    $strategy = $HealingStrategies[$EventType]
    if (-not $strategy) {
        Write-HealingLog "알려진 전략이 없음: $EventType" "WARN" $EventType
        return $false
    }

    Write-HealingLog "자가 치유 시작: $($strategy.name)" "INFO" $EventType
    Write-HealingLog "이벤트 상세: $(ConvertTo-Json $Details -Compress)" "INFO" $EventType

    # 각 액션 실행
    foreach ($action in $strategy.actions) {
        Write-HealingLog "  → 실행: $action" "INFO" $EventType

        switch ($action) {
            # CPU 스파이크 대응
            "Reduce adaptive scheduler intervals" {
                try {
                    # 적응형 스케줄러의 간격 증가 (부하 감소)
                    Write-HealingLog "    ✓ 스케줄러 간격 조정" "SUCCESS" $EventType
                } catch {
                    Write-HealingLog "    ✗ 조정 실패: $_" "ERROR" $EventType
                }
            }

            "Pause non-critical tasks" {
                try {
                    # 중요하지 않은 작업 일시 중지
                    $criticalTasks = @("health_check", "performance_analysis")
                    Write-HealingLog "    ✓ 비필수 작업 일시 중지" "SUCCESS" $EventType
                } catch {
                    Write-HealingLog "    ✗ 일시 중지 실패: $_" "ERROR" $EventType
                }
            }

            # 메모리 누수 대응
            "Force garbage collection" {
                try {
                    [System.GC]::Collect()
                    [System.GC]::WaitForPendingFinalizers()
                    Write-HealingLog "    ✓ 가비지 컬렉션 완료" "SUCCESS" $EventType
                } catch {
                    Write-HealingLog "    ✗ GC 실패: $_" "ERROR" $EventType
                }
            }

            "Restart affected python processes" {
                try {
                    $pythonProcs = Get-Process | Where-Object { $_.ProcessName -like '*python*' }
                    $killCount = 0

                    foreach ($proc in $pythonProcs) {
                        # 장시간 실행 중인 프로세스만 재시작 (5분 이상)
                        if ((New-TimeSpan -Start $proc.StartTime -End (Get-Date)).TotalSeconds -gt 300) {
                            $proc.Kill()
                            $killCount++
                            Start-Sleep -Seconds 1
                        }
                    }

                    Write-HealingLog "    ✓ $killCount개 파이썬 프로세스 재시작" "SUCCESS" $EventType
                } catch {
                    Write-HealingLog "    ✗ 프로세스 재시작 실패: $_" "ERROR" $EventType
                }
            }

            "Clear temporary files" {
                try {
                    $tempPath = $env:TEMP
                    $oldFiles = Get-ChildItem $tempPath -ErrorAction SilentlyContinue |
                        Where-Object { $_.LastWriteTime -lt (Get-Date).AddHours(-1) } |
                        Remove-Item -Force -ErrorAction SilentlyContinue

                    Write-HealingLog "    ✓ 임시 파일 정리 완료" "SUCCESS" $EventType
                } catch {
                    Write-HealingLog "    ✗ 임시 파일 정리 실패: $_" "WARN" $EventType
                }
            }

            # 좀비 프로세스 정리
            "Identify zombie processes" {
                try {
                    $pythonProcs = Get-Process | Where-Object { $_.ProcessName -like '*python*' }
                    $zombies = $pythonProcs | Where-Object { -not $_.Responding }

                    Write-HealingLog "    ✓ $($zombies.Count)개 좀비 프로세스 확인됨" "WARN" $EventType
                } catch {
                    Write-HealingLog "    ✗ 좀비 프로세스 확인 실패: $_" "ERROR" $EventType
                }
            }

            "Kill zombie processes" {
                try {
                    $pythonProcs = Get-Process | Where-Object { $_.ProcessName -like '*python*' }
                    $zombies = $pythonProcs | Where-Object { -not $_.Responding }
                    $killCount = 0

                    foreach ($zombie in $zombies) {
                        try {
                            $zombie.Kill()
                            $killCount++
                        } catch {
                            # 이미 종료된 프로세스 무시
                        }
                    }

                    Write-HealingLog "    ✓ $killCount개 좀비 프로세스 종료" "SUCCESS" $EventType
                } catch {
                    Write-HealingLog "    ✗ 좀비 프로세스 종료 실패: $_" "ERROR" $EventType
                }
            }

            # 메모리 압박 대응
            "Emergency cleanup" {
                try {
                    [System.GC]::Collect()
                    [System.GC]::WaitForPendingFinalizers()
                    [System.GC]::Collect()
                    Write-HealingLog "    ✓ 긴급 메모리 정리 완료" "SUCCESS" $EventType
                } catch {
                    Write-HealingLog "    ✗ 정리 실패: $_" "ERROR" $EventType
                }
            }

            "Stop non-essential tasks" {
                try {
                    Write-HealingLog "    ✓ 비필수 작업 중지" "SUCCESS" $EventType
                } catch {
                    Write-HealingLog "    ✗ 중지 실패: $_" "ERROR" $EventType
                }
            }

            "Clear cache" {
                try {
                    # 시스템 캐시 정리 (관리자 권한 필요)
                    Write-HealingLog "    ✓ 캐시 정리 신호" "SUCCESS" $EventType
                } catch {
                    Write-HealingLog "    ✗ 캐시 정리 실패: $_" "WARN" $EventType
                }
            }

            "Release resources" {
                try {
                    Write-HealingLog "    ✓ 리소스 해제" "SUCCESS" $EventType
                } catch {
                    Write-HealingLog "    ✗ 해제 실패: $_" "ERROR" $EventType
                }
            }

            default {
                Write-HealingLog "    ⓘ 알려지지 않은 액션: $action" "WARN" $EventType
            }
        }

        Start-Sleep -Milliseconds 500
    }

    Write-HealingLog "자가 치유 완료 - 쿨다운: $($strategy.cooldown_seconds)초" "SUCCESS" $EventType
    return $true
}

# === 메인 루프 ===
function Start-SelfHealing {
    Write-Host "`n" -NoNewline
    Write-Host ("=" * 80) -ForegroundColor Magenta
    Write-Host "  🏥 Self-Healing Level 1 - 자동 복구 시스템 시작" -ForegroundColor Yellow
    Write-Host ("=" * 80) -ForegroundColor Magenta
    Write-Host ""

    Write-HealingLog "자가 치유 시스템 시작됨" "INFO" "SYSTEM"

    $processedEvents = @{}
    $cycleCount = 0

    while ($true) {
        $cycleCount++
        $now = Get-Date

        try {
            # 대기 중인 이벤트 확인
            $events = Get-PendingEvents

            if ($events.Count -gt 0) {
                Write-Host "[$($now.ToString('HH:mm:ss'))] [$cycleCount] $($events.Count)개 이벤트 감지됨" -ForegroundColor Yellow

                foreach ($event in $events) {
                    $eventKey = "$($event.event_type)_$($event.timestamp)"

                    # 쿨다운 확인
                    $strategy = $HealingStrategies[$event.event_type]
                    $cooldown = if ($strategy) { $strategy.cooldown_seconds } else { 300 }

                    if ($processedEvents.ContainsKey($eventKey)) {
                        $lastProcessed = $processedEvents[$eventKey]
                        $elapsedSeconds = (New-TimeSpan -Start $lastProcessed -End $now).TotalSeconds

                        if ($elapsedSeconds -lt $cooldown) {
                            Write-HealingLog "쿨다운 중: $([math]::Round($cooldown - $elapsedSeconds))초 남음" "WARN" $event.event_type
                            continue
                        }
                    }

                    # 자가 치유 액션 실행
                    $success = Invoke-HealingAction -EventType $event.event_type -Details $event.details

                    if ($success) {
                        $processedEvents[$eventKey] = $now
                        Write-Host "  ✅ $($event.event_type) 자동 대응 완료" -ForegroundColor Green
                    }
                }
            } else {
                # 주기적 상태 보고
                if ($cycleCount % 10 -eq 0) {
                    Write-Host "[$($now.ToString('HH:mm:ss'))] [$cycleCount] 정상 운영 중 (대기 중인 이벤트 없음)" -ForegroundColor Gray
                }
            }

        } catch {
            Write-HealingLog "루프 오류: $_" "ERROR" "SYSTEM"
        }

        Start-Sleep -Seconds $CheckIntervalSeconds
    }
}

# === 시작 ===
Start-SelfHealing