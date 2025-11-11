<#
    Rhythm Mode Manager - Adaptive System Load Control
    리듬 기반 시스템 부하 조절 관리자

    사용법:
      - 상태 확인:  .\rhythm_mode_manager.ps1 -Mode status
      - 작업 모드:  .\rhythm_mode_manager.ps1 -Mode work
      - 휴식 모드:  .\rhythm_mode_manager.ps1 -Mode rest
      - 자동 모드:  .\rhythm_mode_manager.ps1 -Mode auto
      - 드라이런:    -DryRun 스위치 추가
      - 강제실행:    -Force 스위치 추가

    주의: 이 스크립트는 최소 의존성으로 동작하도록 설계되어
          별도의 JSON 없이도 음악 데몬을 안전하게 시작/중지합니다.
          추가 리소스 제어가 필요하면 scripts/rhythm_manager_config.json 을 확장하세요.
#>

param(
    [Parameter(Mandatory = $false)]
    [ValidateSet("work", "rest", "auto", "status")]
    [string]$Mode = "status",

    [Parameter(Mandatory = $false)]
    [switch]$DryRun,

    [Parameter(Mandatory = $false)]
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

function Write-Info([string]$msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Ok([string]$msg) { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn([string]$msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err([string]$msg) { Write-Host "[ERR]  $msg" -ForegroundColor Red }

function Get-WorkspaceRoot {
    if ($PSScriptRoot) { return (Resolve-Path (Join-Path $PSScriptRoot '..')).Path }
    return (Resolve-Path '.').Path
}

function Get-PythonPath {
    param([string]$WorkspaceRoot)
    $candidates = @(
        (Join-Path $WorkspaceRoot 'fdo_agi_repo\.venv\Scripts\python.exe'),
        (Join-Path $WorkspaceRoot 'LLM_Unified\.venv\Scripts\python.exe'),
        'python'
    )
    foreach ($p in $candidates) {
        if ($p -eq 'python') { return $p }
        if (Test-Path -LiteralPath $p) { return $p }
    }
    return 'python'
}

function Get-ProcessesByCommandPattern {
    param([Parameter(Mandatory = $true)][string]$Pattern)
    try {
        $procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*${Pattern}*" }
        return $procs
    }
    catch {
        # 폴백: python 프로세스만으로 제한 (일부 환경에서 CommandLine 접근 제한)
        $py = Get-Process -Name 'python' -ErrorAction SilentlyContinue
        return $py
    }
}

function Stop-MusicDaemon {
    param([switch]$DryRun, [switch]$Force)
    $procs = Get-ProcessesByCommandPattern -Pattern 'music_daemon.py'
    if (-not $procs) {
        Write-Info 'Music Daemon process not found.'
        return $true
    }
    foreach ($p in $procs) {
        Write-Info "Stopping PID=$($p.ProcessId) Name=$($p.Name)"
        if (-not $DryRun) {
            try {
                Stop-Process -Id $p.ProcessId -Force:$Force.IsPresent -ErrorAction Stop
            }
            catch {
                # CIM -> Stop-Process 매핑 실패 시 WMI 사용
                try { Invoke-CimMethod -InputObject $p -MethodName Terminate | Out-Null } catch { }
            }
        }
    }
    return $true
}

function Start-MusicDaemon {
    param([string]$WorkspaceRoot, [switch]$DryRun, [switch]$Force)

    $python = Get-PythonPath -WorkspaceRoot $WorkspaceRoot
    $script = Join-Path $WorkspaceRoot 'scripts\music_daemon.py'

    if (-not (Test-Path -LiteralPath $script)) {
        Write-Err "music_daemon.py not found: $script"
        return $false
    }

    # 중복 실행 방지 (Force면 선정지)
    $existing = Get-ProcessesByCommandPattern -Pattern 'music_daemon.py'
    if ($existing) {
        if ($Force) {
            Write-Warn 'Existing music daemon found. Forcing stop before restart.'
            if (-not (Stop-MusicDaemon -DryRun:$DryRun -Force)) { return $false }
            Start-Sleep -Milliseconds 300
        }
        else {
            Write-Ok 'Music Daemon already running.'
            return $true
        }
    }

    $cmdArgs = @("$script")
    Write-Info "Starting music daemon: $python $($cmdArgs -join ' ')"
    if (-not $DryRun) {
        try {
            Start-Process -FilePath $python -ArgumentList $cmdArgs -WindowStyle Hidden | Out-Null
            Start-Sleep -Milliseconds 400
        }
        catch {
            Write-Err "Failed to start daemon: $($_.Exception.Message)"
            return $false
        }
    }

    # 확인
    $chk = Get-ProcessesByCommandPattern -Pattern 'music_daemon.py'
    if ($chk) { Write-Ok 'Music Daemon started.'; return $true }
    Write-Err 'Music Daemon failed to start.'
    return $false
}

function Show-Status {
    $procs = Get-ProcessesByCommandPattern -Pattern 'music_daemon.py'
    if ($procs) {
        Write-Ok 'Music Daemon is running.'
        try {
            $procs | Select-Object ProcessId, Name, CommandLine | Format-Table -AutoSize
        }
        catch {
            $procs | Select-Object ProcessId, Name | Format-Table -AutoSize
        }
        return 0
    }
    else {
        Write-Warn 'Music Daemon is NOT running.'
        return 1
    }
}

# 메인 로직
$ws = Get-WorkspaceRoot
Write-Info "Workspace: $ws"

switch ($Mode) {
    'status' {
        $code = Show-Status
        exit $code
    }
    'rest' {
        Write-Info 'Applying REST mode: stopping music daemon.'
        $ok = Stop-MusicDaemon -DryRun:$DryRun -Force:$Force
        if ($ok) { Write-Ok 'REST mode applied.'; exit 0 } else { exit 1 }
    }
    'work' {
        Write-Info 'Applying WORK mode: starting music daemon.'
        $ok = Start-MusicDaemon -WorkspaceRoot $ws -DryRun:$DryRun -Force:$Force
        if ($ok) { Write-Ok 'WORK mode applied.'; exit 0 } else { exit 1 }
    }
    'auto' {
        # 단순 휴리스틱: 오전 8시~저녁 9시 WORK, 그 외 REST
        $hour = (Get-Date).Hour
        if ($hour -ge 8 -and $hour -lt 21) {
            Write-Info 'AUTO → WORK (time-based)'
            $ok = Start-MusicDaemon -WorkspaceRoot $ws -DryRun:$DryRun -Force:$Force
        }
        else {
            Write-Info 'AUTO → REST (time-based)'
            $ok = Stop-MusicDaemon -DryRun:$DryRun -Force:$Force
        }
        if ($ok) { Write-Ok 'AUTO mode applied.'; exit 0 } else { exit 1 }
    }
    default {
        Write-Err "Unknown mode: $Mode"
        exit 2
    }
}

function Get-MusicDaemon {
    return Get-ProcessesByCommandPattern -Pattern 'music_daemon.py'
}

function Start-MusicDaemon {
    param(
        [string]$WorkspaceRoot,
        [switch]$DryRunLocal
    )
    $python = Get-PythonPath -WorkspaceRoot $WorkspaceRoot
    $scriptPath = Join-Path $WorkspaceRoot 'scripts\music_daemon.py'
    if (-not (Test-Path -LiteralPath $scriptPath)) {
        Write-Err "음악 데몬 스크립트를 찾을 수 없습니다: $scriptPath"
        return $false
    }
    $already = Get-MusicDaemon
    if ($already) {
        Write-Ok "Music Daemon 이미 실행 중 (PIDs: $((($already | Select-Object -ExpandProperty ProcessId) -join ', ')))"
        return $true
    }
    $args = '"{0}"' -f $scriptPath
    if ($DryRunLocal) { Write-Info "DRYRUN: Start-Process -FilePath '$python' -ArgumentList $args -WindowStyle Hidden"; return $true }
    try {
        $p = Start-Process -FilePath $python -ArgumentList $args -WindowStyle Hidden -PassThru
        Start-Sleep -Milliseconds 200
        if (Get-MusicDaemon) { Write-Ok "Music Daemon 시작됨 (PID: $($p.Id))"; return $true }
        Write-Warn "Music Daemon 시작 시도 후 감지 실패"
        return $false
    }
    catch {
        Write-Err "Music Daemon 시작 실패: $($_.Exception.Message)"
        return $false
    }
}

function Stop-MusicDaemon {
    param(
        [switch]$DryRunLocal,
        [switch]$ForceLocal
    )
    $procs = Get-MusicDaemon
    if (-not $procs) {
        Write-Ok 'Music Daemon 미실행 (이미 정지 상태)'
        return $true
    }
    $pids = @()
    foreach ($p in $procs) { $pids += $p.ProcessId }
    if ($DryRunLocal) { Write-Info "DRYRUN: Stop-Process -Id $($pids -join ',') -Force:$ForceLocal"; return $true }
    try {
        Stop-Process -Id $pids -Force:$ForceLocal -ErrorAction Stop
        Start-Sleep -Milliseconds 150
        if (-not (Get-MusicDaemon)) { Write-Ok 'Music Daemon 중지 완료'; return $true }
        Write-Warn 'Music Daemon 일부가 여전히 실행 중'
        return $false
    }
    catch {
        Write-Err "Music Daemon 중지 실패: $($_.Exception.Message)"
        return $false
    }
}

function Get-Status {
    $music = Get-MusicDaemon
    @{ 
        MusicDaemonRunning = [bool]($music)
        MusicDaemonPids    = if ($music) { ($music | Select-Object -ExpandProperty ProcessId) } else { @() }
    }
}

try {
    $ws = Get-WorkspaceRoot
    Write-Info "Workspace: $ws"

    switch ($Mode) {
        'status' {
            $st = Get-Status
            if ($st.MusicDaemonRunning) {
                Write-Ok "Music Daemon 실행 중 (PIDs: $((@($st.MusicDaemonPids) -join ',')))"
                exit 0
            }
            else {
                Write-Warn 'Music Daemon 정지 상태'
                exit 0
            }
        }
        'rest' {
            Write-Info '휴식 모드로 전환: 리듬 관련 데몬 정지'
            $ok1 = Stop-MusicDaemon -DryRunLocal:$DryRun -ForceLocal:$Force
            if ($ok1) { exit 0 } else { exit 1 }
        }
        'work' {
            Write-Info '작업 모드로 전환: 필요한 데몬 시작'
            $ok1 = Start-MusicDaemon -WorkspaceRoot $ws -DryRunLocal:$DryRun
            if ($ok1) { exit 0 } else { exit 1 }
        }
        'auto' {
            # 간단한 휴리스틱: 야간(22~07시)엔 rest, 그 외 work. (필요시 고도화)
            $hour = (Get-Date).Hour
            $autoMode = if ($hour -ge 22 -or $hour -lt 7) { 'rest' } else { 'work' }
            Write-Info "AUTO 모드 결정: $autoMode"
            if ($autoMode -eq 'rest') {
                $ok1 = Stop-MusicDaemon -DryRunLocal:$DryRun -ForceLocal:$Force
                if ($ok1) { exit 0 } else { exit 1 }
            }
            else {
                $ok1 = Start-MusicDaemon -WorkspaceRoot $ws -DryRunLocal:$DryRun
                if ($ok1) { exit 0 } else { exit 1 }
            }
        }
        default {
            Write-Err "알 수 없는 모드: $Mode"
            exit 2
        }
    }
}
catch {
    Write-Err "예상치 못한 오류: $($_.Exception.Message)"
    exit 1
}

function Write-ColorHost {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Get-ProcessByPattern {
    param([string]$Pattern)
    Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like $Pattern
    }
}

function Stop-ProcessByPattern {
    param([string]$Pattern, [string]$Name, [int]$TimeoutSec = 15, [string]$JobName = "")
    
    # Job 중지 (JobName이 있으면)
    if ($JobName) {
        $jobs = Get-Job -Name $JobName -ErrorAction SilentlyContinue
        if ($jobs) {
            Write-ColorHost "  → Job 중지: $JobName ($($jobs.Count)개)" "Yellow"
            if (-not $DryRun) {
                $jobs | ForEach-Object {
                    try {
                        Stop-Job -Id $_.Id -ErrorAction Stop
                        Remove-Job -Id $_.Id -Force -ErrorAction Stop
                        Write-ColorHost "    ✅ Job 중지: ID $($_.Id)" "Green"
                    }
                    catch {
                        Write-ColorHost "    ⚠️ Job 중지 실패: ID $($_.Id)" "Red"
                    }
                }
            }
        }
        else {
            Write-ColorHost "  → Job 없음: $JobName (skip)" "Gray"
        }
        return
    }
    
    # 프로세스 중지
    $procs = Get-ProcessByPattern -Pattern $Pattern
    if ($procs) {
        Write-ColorHost "  → 중지: $Name ($($procs.Count)개 프로세스)" "Yellow"
        if (-not $DryRun) {
            $procs | Stop-Process -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
            
            # 확인
            $remaining = Get-ProcessByPattern -Pattern $Pattern
            if ($remaining) {
                Write-ColorHost "    ⚠️ 일부 프로세스 종료 실패" "Red"
            }
            else {
                Write-ColorHost "    ✅ 완전 종료" "Green"
            }
        }
    }
    else {
        Write-ColorHost "  → $Name 실행 중이 아님 (skip)" "Gray"
    }
}

function Start-ProcessFromConfig {
    param($Item, [int]$TimeoutSec = 30)
    
    $pattern = $Item.processPattern
    $existing = Get-ProcessByPattern -Pattern $pattern
    
    if ($existing -and -not $Force) {
        Write-ColorHost "  → 시작: $($Item.name) (이미 실행 중, skip)" "Gray"
        return
    }
    
    if ($existing -and $Force) {
        Write-ColorHost "  → 재시작: $($Item.name) (기존 종료 후)" "Yellow"
        Stop-ProcessByPattern -Pattern $pattern -Name $Item.name
    }
    
    Write-ColorHost "  → 시작: $($Item.name)" "Cyan"
    if (-not $DryRun) {
        $scriptPath = Join-Path $Script:WorkspaceRoot $Item.script
        $argList = $Item.args -join " "
        
        try {
            # Job 타입 처리
            if ($Item.type -eq "job") {
                $jobName = if ($Item.jobName) { $Item.jobName } else { $Item.name -replace '\s+', '' }
                
                # 기존 Job 확인
                $existingJob = Get-Job -Name $jobName -ErrorAction SilentlyContinue
                if ($existingJob) {
                    Write-ColorHost "    ⚠️ Job이 이미 실행 중입니다 (skip)" "Gray"
                    return
                }
                
                # Job으로 시작
                Start-Job -Name $jobName -ScriptBlock {
                    param($ScriptPath, $Args)
                    & $ScriptPath @Args
                } -ArgumentList $scriptPath, $Item.args | Out-Null
                
                Write-ColorHost "    ✅ Job 시작: $jobName" "Green"
                return
            }
            
            # 기존 프로세스 시작 로직
            if ($Item.script -like "*.ps1") {
                Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" $argList" -WindowStyle Hidden
            }
            elseif ($Item.script -like "*python.exe") {
                $pyArgs = $Item.args | ForEach-Object {
                    if ($_ -like "*.py") {
                        Join-Path $Script:WorkspaceRoot $_
                    }
                    else {
                        $_
                    }
                }
                Start-Process -FilePath $scriptPath -ArgumentList $pyArgs -WindowStyle Hidden
            }
            else {
                Write-ColorHost "    ⚠️ 지원하지 않는 스크립트 타입" "Red"
                return
            }
            
            Start-Sleep -Seconds 3
            $check = Get-ProcessByPattern -Pattern $pattern
            if ($check) {
                Write-ColorHost "    ✅ 시작 확인됨" "Green"
            }
            else {
                Write-ColorHost "    ⚠️ 시작 확인 실패 (타임아웃 또는 오류)" "Red"
            }
        }
        catch {
            Write-ColorHost "    ❌ 시작 실패: $_" "Red"
        }
    }
}

function Get-CurrentRhythmStatus {
    $rhythmFile = Join-Path $Script:WorkspaceRoot "outputs\RHYTHM_SYSTEM_STATUS_REPORT.md"
    if (-not (Test-Path $rhythmFile)) {
        return @{ Status = "UNKNOWN"; Reason = "파일 없음" }
    }
    
    $content = Get-Content $rhythmFile -Raw
    if ($content -match "Overall Status:\s*\*\*(\w+)\*\*") {
        return @{ Status = $matches[1]; Reason = "파싱 성공" }
    }
    
    return @{ Status = "UNKNOWN"; Reason = "파싱 실패" }
}

function Get-RecommendedMode {
    $now = Get-Date
    $hour = $now.Hour
    
    $config = Get-Content $ConfigFile -Raw | ConvertFrom-Json
    $autoConfig = $config.auto_switch
    
    $workStart = [datetime]::ParseExact($autoConfig.work_hours.start, "HH:mm", $null).Hour
    $workEnd = [datetime]::ParseExact($autoConfig.work_hours.end, "HH:mm", $null).Hour
    
    $isWorkHours = ($hour -ge $workStart) -and ($hour -lt $workEnd)
    
    $rhythm = Get-CurrentRhythmStatus
    $isWorkRhythm = $rhythm.Status -in $autoConfig.rhythm_triggers.work
    $isRestRhythm = $rhythm.Status -in $autoConfig.rhythm_triggers.rest
    
    if ($isRestRhythm) {
        return @{ Mode = "rest"; Reason = "리듬 상태: $($rhythm.Status)" }
    }
    
    if ($isWorkHours -and $isWorkRhythm) {
        return @{ Mode = "work"; Reason = "업무시간 + 양호 리듬" }
    }
    
    if (-not $isWorkHours) {
        return @{ Mode = "rest"; Reason = "휴식 시간대 ($hour시)" }
    }
    
    return @{ Mode = "work"; Reason = "업무시간 (기본)" }
}

function Show-CurrentStatus {
    Write-ColorHost "`n📊 현재 리듬 상태" "Cyan"
    Write-ColorHost ("=" * 60) "Gray"
    
    # 시간
    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-ColorHost "⏰ 현재 시각: $now" "White"
    
    # 리듬 상태
    $rhythm = Get-CurrentRhythmStatus
    Write-ColorHost "🌊 리듬 상태: $($rhythm.Status) ($($rhythm.Reason))" "Yellow"
    
    # 추천 모드
    $recommended = Get-RecommendedMode
    Write-ColorHost "💡 추천 모드: $($recommended.Mode) - $($recommended.Reason)" "Green"
    
    # 주요 프로세스 확인
    Write-ColorHost "`n🔍 주요 프로세스 상태:" "Cyan"
    
    $checks = @(
        @{ Name = "Task Queue Server"; Pattern = "*task_queue_server*" },
        @{ Name = "RPA Worker"; Pattern = "*rpa_worker.py*" },
        @{ Name = "Task Watchdog"; Pattern = "*task_watchdog.py*" },
        @{ Name = "Worker Monitor"; Pattern = "*worker_monitor*" },
        @{ Name = "Flow Observer"; Pattern = "*flow_observer*" },
        @{ Name = "Music Daemon"; Pattern = "*music_daemon.py*" },
        @{ Name = "Observer Telemetry"; Pattern = "*observe_desktop_telemetry.ps1*" }
    )
    
    foreach ($check in $checks) {
        $proc = Get-ProcessByPattern -Pattern $check.Pattern
        if ($proc) {
            Write-ColorHost "  ✅ $($check.Name): 실행 중 ($($proc.Count)개)" "Green"
        }
        else {
            Write-ColorHost "  ⭕ $($check.Name): 중지" "Gray"
        }
    }
    
    Write-ColorHost "`n" "White"
}

function Apply-Mode {
    param([string]$TargetMode)
    
    Write-ColorHost "`n🎯 모드 전환: $TargetMode" "Cyan"
    Write-ColorHost ("=" * 60) "Gray"
    
    if ($DryRun) {
        Write-ColorHost "⚠️ DRY RUN MODE - 실제 변경 없음" "Yellow"
    }
    
    $config = Get-Content $ConfigFile -Raw | ConvertFrom-Json
    $modeConfig = $config.modes.$TargetMode
    
    if (-not $modeConfig) {
        Write-ColorHost "❌ 알 수 없는 모드: $TargetMode" "Red"
        exit 1
    }
    
    Write-ColorHost "`n📝 모드 설명: $($modeConfig.description)" "White"
    
    # Stop processes
    if ($modeConfig.stop.Count -gt 0) {
        Write-ColorHost "`n🛑 프로세스 중지:" "Yellow"
        foreach ($item in $modeConfig.stop) {
            Stop-ProcessByPattern -Pattern $item.processPattern -Name $item.name
        }
    }
    
    # Start processes
    if ($modeConfig.start.Count -gt 0) {
        Write-ColorHost "`n🚀 프로세스 시작:" "Green"
        foreach ($item in $modeConfig.start) {
            Start-ProcessFromConfig -Item $item
        }
    }
    
    # Adjust processes
    if ($modeConfig.adjust.Count -gt 0) {
        Write-ColorHost "`n⚙️ 프로세스 조정:" "Cyan"
        foreach ($item in $modeConfig.adjust) {
            if ($item.restart) {
                Stop-ProcessByPattern -Pattern $item.processPattern -Name $item.name
                Start-Sleep -Seconds 2
                Start-ProcessFromConfig -Item $item
            }
            else {
                Write-ColorHost "  → $($item.name): $($item.description)" "Gray"
            }
        }
    }
    
    Write-ColorHost "`n✅ 모드 전환 완료: $TargetMode" "Green"
    
    # 모드 저장 (다음 실행 시 참조)
    if (-not $DryRun) {
        $stateFile = Join-Path $Script:WorkspaceRoot "outputs\rhythm_mode_current.txt"
        "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')|$TargetMode" | Out-File -FilePath $stateFile -Encoding UTF8
    }
}

# ============================================================
# Main Execution
# ============================================================

Write-ColorHost "`n🌊 Rhythm Mode Manager" "Cyan"
Write-ColorHost ("=" * 60) "Gray"

switch ($Mode) {
    "status" {
        Show-CurrentStatus
    }
    "auto" {
        $recommended = Get-RecommendedMode
        Write-ColorHost "💡 자동 모드 선택: $($recommended.Mode)" "Green"
        Write-ColorHost "   이유: $($recommended.Reason)" "Gray"
        Apply-Mode -TargetMode $recommended.Mode
    }
    default {
        Apply-Mode -TargetMode $Mode
    }
}

Write-ColorHost ("=" * 60) "Gray"
Write-ColorHost "완료." "White"
