#Requires -Version 5.1
<#
.SYNOPSIS
    Active Cooldown: 중강도 안정화 절차 (Fear ≥ 0.7 트리거)

.DESCRIPTION
    감정 신호 기반 중강도 복구 절차
    - Fear ≥ 0.7 감지 시 자동 실행
    - 5-10분 안정화 기간
    - 태스크 일시 중단
    - 지표 모니터링 및 추세 분석
    - 종료 조건: Fear < 0.5 AND 3분 이상 안정 추세

.PARAMETER DryRun
    실제 실행 없이 시뮬레이션

.PARAMETER Force
    확인 없이 즉시 실행

.PARAMETER MaxDurationMinutes
    최대 실행 시간 (기본 10분)

.EXAMPLE
    .\scripts\active_cooldown.ps1 -DryRun
    .\scripts\active_cooldown.ps1 -Force -MaxDurationMinutes 5
#>

[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Force,
    [int]$MaxDurationMinutes = 10,
    [int]$LogMaxMB = 1,
    [int]$LogKeep = 3
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# 설정
$StatePath = "fdo_agi_repo/memory/core_state.json"
$LogPath = "outputs/active_cooldown.log"
$FearThreshold = 0.7
$TargetFear = 0.5
$StabilityWindowMinutes = 3
$CheckIntervalSeconds = 30

# UTF-8 (no BOM) append helper
function Out-FileUtf8NoBomAppend {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Text
    )
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    $encoding = New-Object System.Text.UTF8Encoding($false)
    $stream = New-Object System.IO.StreamWriter($Path, $true, $encoding)
    try {
        $stream.WriteLine($Text)
    }
    finally {
        $stream.Dispose()
    }
}

function Rotate-LogIfNeeded {
    param(
        [string]$Path,
        [int]$MaxMB = 1,
        [int]$Keep = 3
    )
    if (-not (Test-Path -LiteralPath $Path)) { return }
    try {
        $info = Get-Item -LiteralPath $Path -ErrorAction Stop
        $limit = [int64]$MaxMB * 1MB
        if ($info.Length -le $limit) { return }

        $dir = Split-Path -Parent $Path
        $base = Split-Path -Leaf $Path
        for ($i = $Keep; $i -ge 2; $i--) {
            $src = Join-Path $dir ("{0}.{1}" -f $base, $i - 1)
            $dst = Join-Path $dir ("{0}.{1}" -f $base, $i)
            if (Test-Path -LiteralPath $src) {
                Rename-Item -LiteralPath $src -NewName (Split-Path -Leaf $dst) -Force -ErrorAction SilentlyContinue
            }
        }
        Rename-Item -LiteralPath $Path -NewName ("{0}.1" -f $base) -Force -ErrorAction SilentlyContinue
    }
    catch {
        Write-Host "[WARN] Log rotation skipped: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# 로그 함수
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logLine = "[$timestamp] [$Level] $Message"
    Out-FileUtf8NoBomAppend -Path $LogPath -Text $logLine
    
    switch ($Level) {
        "ERROR" { Write-Host $logLine -ForegroundColor Red }
        "WARNING" { Write-Host $logLine -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logLine -ForegroundColor Green }
        default { Write-Host $logLine -ForegroundColor Cyan }
    }
}

# Fear 신호 읽기
function Get-FearSignal {
    if (!(Test-Path $StatePath)) {
        Write-Log "Core state 파일 없음: $StatePath" "ERROR"
        return $null
    }
    
    $state = Get-Content $StatePath -Raw | ConvertFrom-Json
    return $state.emotion.fear
}

# Fear 신호 업데이트
function Set-FearSignal {
    param([double]$NewFear)
    
    if ($DryRun) {
        Write-Log "[DRY-RUN] Fear 업데이트: $NewFear" "INFO"
        return
    }
    
    $state = Get-Content $StatePath -Raw | ConvertFrom-Json
    $state.emotion.fear = $NewFear
    $state.timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    
    $json = $state | ConvertTo-Json -Depth 3
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText((Resolve-Path $StatePath), $json, $encoding)
    Write-Log "Fear 업데이트: $NewFear" "INFO"
}

# 태스크 일시 중단
function Suspend-ActiveTasks {
    Write-Log "활성 태스크 일시 중단..." "INFO"
    
    if ($DryRun) {
        Write-Log "[DRY-RUN] 태스크 중단 시뮬레이션" "INFO"
        return $true
    }
    
    # Task Queue 서버 확인
    try {
        $queueStatus = Invoke-RestMethod -Uri "http://127.0.0.1:8091/api/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($queueStatus) {
            Write-Log "Task Queue 확인: pending=$($queueStatus.pending_tasks)" "INFO"
        }
    }
    catch {
        Write-Log "Task Queue 오프라인" "INFO"
    }
    
    # 백그라운드 작업 확인 (중단하지 않음)
    $jobs = Get-Job -State Running -ErrorAction SilentlyContinue
    if ($jobs) {
        Write-Log "백그라운드 작업: $($jobs.Count)개 (유지)" "INFO"
    }
    
    return $true
}

# 안정 추세 확인
function Test-StabilityTrend {
    param([System.Collections.ArrayList]$FearHistory)
    
    if ($FearHistory.Count -lt 3) {
        return $false
    }
    
    # 최근 3개 샘플이 모두 TargetFear 미만이어야 함
    $recentSamples = @($FearHistory | Select-Object -Last 3)
    $allBelowTarget = @($recentSamples | Where-Object { $_ -lt $TargetFear })
    
    if ($allBelowTarget.Count -eq 3) {
        # 추세가 안정적인지 확인 (변동 < 0.1)
        $variance = ($recentSamples | Measure-Object -Maximum -Minimum)
        $range = $variance.Maximum - $variance.Minimum
        
        if ($range -lt 0.1) {
            return $true
        }
    }
    
    return $false
}

# Fear 감소 계산 (시간 기반)
function Get-ReducedFear {
    param(
        [double]$CurrentFear,
        [int]$ElapsedSeconds
    )
    
    # 시간당 감쇠율: 0.1/분 (10분이면 최대 1.0 감소)
    $decayRate = 0.1 / 60  # per second
    $reduction = $decayRate * $ElapsedSeconds
    
    # 현재 Fear가 높을수록 감소율 증가 (비선형)
    $amplifier = 1.0 + ($CurrentFear - 0.5)
    $reduction *= $amplifier
    
    $newFear = [Math]::Max(0.0, $CurrentFear - $reduction)
    return $newFear
}

# 메인 실행
function Invoke-ActiveCooldown {
    Rotate-LogIfNeeded -Path $LogPath -MaxMB $LogMaxMB -Keep $LogKeep
    Write-Log "=== Active Cooldown 시작 ===" "INFO"
    Write-Log "DryRun: $DryRun, MaxDuration: ${MaxDurationMinutes}분" "INFO"
    
    # 1. Fear 신호 확인
    $currentFear = Get-FearSignal
    if ($null -eq $currentFear) {
        Write-Log "Fear 신호를 읽을 수 없습니다" "ERROR"
        return 1
    }
    
    Write-Log "현재 Fear: $currentFear" "INFO"
    
    # 2. 임계값 검사
    if ($currentFear -lt $FearThreshold) {
        Write-Log "Fear < ${FearThreshold}: Active Cooldown 불필요" "INFO"
        return 0
    }
    
    # 3. 확인 (Force 없으면)
    if (!$Force -and !$DryRun) {
        $confirm = Read-Host "Fear=$currentFear ≥ $FearThreshold. Active Cooldown 실행? (y/N)"
        if ($confirm -ne "y") {
            Write-Log "사용자가 취소함" "WARNING"
            return 0
        }
    }
    
    # 4. 태스크 중단
    $success = Suspend-ActiveTasks
    if (!$success) {
        Write-Log "태스크 중단 실패" "ERROR"
        return 1
    }
    
    # 5. 안정화 루프
    Write-Log "안정화 루프 시작 (최대 ${MaxDurationMinutes}분)..." "INFO"
    
    $startTime = Get-Date
    $maxDuration = New-TimeSpan -Minutes $MaxDurationMinutes
    $fearHistory = New-Object System.Collections.ArrayList
    [void]$fearHistory.Add($currentFear)
    $lastCheckTime = $startTime
    
    while ((Get-Date) - $startTime -lt $maxDuration) {
        # CheckInterval마다 확인
        $elapsed = (Get-Date) - $lastCheckTime
        if ($elapsed.TotalSeconds -lt $CheckIntervalSeconds) {
            Start-Sleep -Seconds 5
            continue
        }
        
        # Fear 감소 계산
        $elapsedTotal = ((Get-Date) - $startTime).TotalSeconds
        $newFear = Get-ReducedFear -CurrentFear $currentFear -ElapsedSeconds $elapsedTotal
        Set-FearSignal -NewFear $newFear
        
        [void]$fearHistory.Add($newFear)
        $currentFear = $newFear
        $lastCheckTime = Get-Date
        
        Write-Log "Fear 체크: $newFear (경과: $([int]$elapsedTotal)초)" "INFO"
        
        # 안정 추세 확인
        if (Test-StabilityTrend -FearHistory $fearHistory) {
            Write-Log "안정 추세 확인됨 (3분+ 안정)" "SUCCESS"
            break
        }
        
        # 목표 달성 확인
        if ($newFear -lt $TargetFear) {
            Write-Log "Fear < ${TargetFear} (경과: $([int]$elapsedTotal)초)" "INFO"
        }
    }
    
    # 6. 최종 결과
    $finalFear = Get-FearSignal
    $totalElapsed = ((Get-Date) - $startTime).TotalMinutes
    
    Write-Log "=== Active Cooldown 완료 ===" "SUCCESS"
    Write-Log "Fear: $($fearHistory[0]) → $finalFear" "SUCCESS"
    Write-Log "소요 시간: $([Math]::Round($totalElapsed, 1))분" "SUCCESS"
    
    if ($finalFear -lt $TargetFear -and (Test-StabilityTrend -FearHistory $fearHistory)) {
        Write-Log "✅ 목표 달성: Fear < ${TargetFear} + 안정 추세" "SUCCESS"
        return 0
    }
    elseif ($finalFear -lt $TargetFear) {
        Write-Log "⚠️  Fear < ${TargetFear} 달성, 안정 추세 확인 필요" "WARNING"
        return 2
    }
    else {
        Write-Log "⚠️  목표 미달: Fear=$finalFear (목표 <${TargetFear})" "WARNING"
        Write-Log "Deep Maintenance 필요 가능성" "WARNING"
        return 3
    }
}

# 실행
try {
    $exitCode = Invoke-ActiveCooldown
    exit $exitCode
}
catch {
    Write-Log "예외 발생: $_" "ERROR"
    Write-Log $_.ScriptStackTrace "ERROR"
    exit 1
}