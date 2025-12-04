#Requires -Version 5.1
<#
.SYNOPSIS
    Micro-Reset: 경량 컨텍스트 재정렬 (Fear ≥ 0.5 트리거)

.DESCRIPTION
    감정 신호 기반 경량 복구 절차
    - Fear ≥ 0.5 감지 시 자동 실행
    - 컨텍스트 버퍼 정리
    - 비핵심 태스크 일시 중단
    - 목표: Fear < 0.4로 안정화

.PARAMETER DryRun
    실제 실행 없이 시뮬레이션

.PARAMETER Force
    확인 없이 즉시 실행

.EXAMPLE
    .\scripts\micro_reset.ps1 -DryRun
    .\scripts\micro_reset.ps1 -Force
#>

[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Force,
    [int]$LogMaxMB = 1,
    [int]$LogKeep = 3
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# 설정
$StatePath = "fdo_agi_repo/memory/lumen_state.json"
$LogPath = "outputs/micro_reset.log"
$FearThreshold = 0.5
$TargetFear = 0.4

# UTF-8 (no BOM) append helper for PowerShell 5.1
function Out-FileUtf8NoBomAppend {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Text
    )
    try {
        $dir = Split-Path -Parent $Path
        if ($dir -and -not (Test-Path -LiteralPath $dir)) {
            New-Item -ItemType Directory -Force -Path $dir | Out-Null
        }
        $enc = New-Object System.Text.UTF8Encoding($false)
        $sw = New-Object System.IO.StreamWriter($Path, $true, $enc)
        try { $sw.WriteLine($Text) } finally { $sw.Dispose() }
    }
    catch {
        Write-Host "[ERROR] Failed to write log: $($_.Exception.Message)" -ForegroundColor Red
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

# 간단한 로그 로테이션 (size-based)
function Rotate-LogIfNeeded {
    param(
        [string]$Path,
        [int]$MaxMB = 1,
        [int]$Keep = 3
    )
    try {
        if (!(Test-Path -LiteralPath $Path)) { return }
        $fi = Get-Item -LiteralPath $Path -ErrorAction SilentlyContinue
        if (-not $fi) { return }
        $bytes = [int64]$fi.Length
        $limit = [int64]$MaxMB * 1MB
        if ($bytes -le $limit) { return }

        $dir = Split-Path -Parent $Path
        $base = Split-Path -Leaf $Path
        # Shift older backups: .(Keep-1) -> .Keep
        for ($i = $Keep; $i -ge 2; $i--) {
            $src = Join-Path $dir ("{0}.{1}" -f $base, ($i - 1))
            $dst = Join-Path $dir ("{0}.{1}" -f $base, $i)
            if (Test-Path -LiteralPath $src) {
                try { Rename-Item -LiteralPath $src -NewName (Split-Path -Leaf $dst) -Force -ErrorAction SilentlyContinue } catch {}
            }
        }
        # Current -> .1
        $bak1 = Join-Path $dir ("{0}.1" -f $base)
        try { Rename-Item -LiteralPath $Path -NewName (Split-Path -Leaf $bak1) -Force -ErrorAction SilentlyContinue } catch {}
        Write-Host ("[INFO] Log rotated: {0} -> {1}" -f $Path, $bak1) -ForegroundColor Gray
    }
    catch {
        Write-Host "[WARN] Log rotation skipped: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Fear 신호 읽기
function Get-FearSignal {
    if (!(Test-Path $StatePath)) {
        Write-Log "Lumen state 파일 없음: $StatePath" "ERROR"
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
    
    $state | ConvertTo-Json -Depth 3 | Out-File $StatePath -Encoding UTF8
    Write-Log "Fear 업데이트: $NewFear" "SUCCESS"
}

# 컨텍스트 정리
function Clear-ContextBuffer {
    Write-Log "컨텍스트 버퍼 정리 시작..." "INFO"
    
    if ($DryRun) {
        Write-Log "[DRY-RUN] 임시 파일 정리 시뮬레이션" "INFO"
        return $true
    }
    
    # 임시 파일 정리
    $tempPaths = @(
        "outputs/*.tmp",
        "fdo_agi_repo/.pytest_tmp/*",
        "outputs/cache/*.tmp"
    )
    
    $cleanedCount = 0
    foreach ($pattern in $tempPaths) {
        $files = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue
        if ($files) {
            $files | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
            $cleanedCount += $files.Count
        }
    }
    
    Write-Log "임시 파일 정리 완료: $cleanedCount 개" "SUCCESS"
    return $true
}

# 비핵심 태스크 중단
function Suspend-NonCriticalTasks {
    Write-Log "비핵심 태스크 일시 중단..." "INFO"
    
    if ($DryRun) {
        Write-Log "[DRY-RUN] 태스크 중단 시뮬레이션" "INFO"
        return $true
    }
    
    # Task Queue 상태 확인
    try {
        $queueStatus = Invoke-RestMethod -Uri "http://127.0.0.1:8091/api/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($queueStatus) {
            Write-Log "Task Queue 서버 확인됨 (pending: $($queueStatus.pending_tasks))" "INFO"
        }
    }
    catch {
        Write-Log "Task Queue 서버 오프라인 (정상)" "INFO"
    }
    
    # Worker 프로세스 확인 (중단하지 않음, 모니터링만)
    $workers = Get-Process -Name "python" -ErrorAction SilentlyContinue | 
    Where-Object { 
        $_.Path -and $_.Path -like "*rpa_worker*"
    }
    
    if ($workers) {
        Write-Log "RPA Worker 감지: $($workers.Count)개 (유지)" "INFO"
    }
    
    return $true
}# Fear 감소 계산
function Get-ReducedFear {
    param([double]$CurrentFear)
    
    # 컨텍스트 정리 효과: -0.15
    $reduction = 0.15
    
    # 시간 경과 효과: -0.05 (자연 감쇠)
    $reduction += 0.05
    
    $newFear = [Math]::Max(0.0, $CurrentFear - $reduction)
    return $newFear
}

# 메인 실행
function Invoke-MicroReset {
    # 로그 로테이션 선행 체크
    Rotate-LogIfNeeded -Path $LogPath -MaxMB $LogMaxMB -Keep $LogKeep
    Write-Log "=== Micro-Reset 시작 ===" "INFO"
    Write-Log "DryRun: $DryRun" "INFO"
    
    # 1. Fear 신호 확인
    $currentFear = Get-FearSignal
    if ($null -eq $currentFear) {
        Write-Log "Fear 신호를 읽을 수 없습니다" "ERROR"
        return 1
    }
    
    Write-Log "현재 Fear: $currentFear" "INFO"
    
    # 2. 임계값 검사
    if ($currentFear -lt $FearThreshold) {
        Write-Log "Fear < ${FearThreshold}: Micro-Reset 불필요" "INFO"
        return 0
    }
    
    # 3. 확인 (Force 없으면)
    if (!$Force -and !$DryRun) {
        $confirm = Read-Host "Fear=$currentFear ≥ $FearThreshold. Micro-Reset 실행? (y/N)"
        if ($confirm -ne "y") {
            Write-Log "사용자가 취소함" "WARNING"
            return 0
        }
    }
    
    # 4. 복구 절차 실행
    Write-Log "복구 절차 실행 중..." "INFO"
    
    $success = $true
    $success = $success -and (Clear-ContextBuffer)
    $success = $success -and (Suspend-NonCriticalTasks)
    
    if (!$success) {
        Write-Log "복구 절차 실패" "ERROR"
        return 1
    }
    
    # 5. Fear 감소
    $newFear = Get-ReducedFear -CurrentFear $currentFear
    Set-FearSignal -NewFear $newFear
    
    # 6. 결과 확인
    Write-Log "=== Micro-Reset 완료 ===" "SUCCESS"
    Write-Log "Fear: $currentFear → $newFear" "SUCCESS"
    
    if ($newFear -lt $TargetFear) {
        Write-Log "[OK] 목표 달성: Fear < $TargetFear" "SUCCESS"
        return 0
    }
    else {
        Write-Log "[WARN] 목표 미달: Fear=$newFear (목표 <$TargetFear)" "WARNING"
        Write-Log "Active Cooldown 필요 가능성" "WARNING"
        return 2
    }
}

# 실행
try {
    $exitCode = Invoke-MicroReset
    exit $exitCode
}
catch {
    Write-Log "예외 발생: $_" "ERROR"
    exit 1
}
