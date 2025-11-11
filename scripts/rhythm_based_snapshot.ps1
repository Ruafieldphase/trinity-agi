<#
.SYNOPSIS
리듬 기반 스냅샷 시스템 - 해마 학습 시뮬레이션

.DESCRIPTION
인간의 기억 시스템을 모방:
- 평상시: 저빈도 체크포인트 (30분 리듬)
- 신호 감지 시: 고해상도 캡처 (두려움/중요도 기반)
- 단기/장기 메모리 자동 분류

.PARAMETER Mode
- rhythm: 주기적 저빈도 체크포인트
- signal: 즉시 고해상도 캡처 (중요 이벤트)
- novelty: 새로운 패턴 감지 시 자동 캡처

.PARAMETER IntervalMinutes
rhythm 모드에서 체크포인트 간격 (기본 30분)

.PARAMETER Importance
signal 모드에서 중요도 (1-10, 7 이상 장기기억 후보)

.EXAMPLE
# 30분 리듬 백그라운드 실행
.\rhythm_based_snapshot.ps1 -Mode rhythm -IntervalMinutes 30

# 중요 순간 즉시 캡처
.\rhythm_based_snapshot.ps1 -Mode signal -Importance 9 -Reason "Critical error occurred"

# 새로운 패턴 감지기 시작
.\rhythm_based_snapshot.ps1 -Mode novelty
#>

param(
    [ValidateSet('rhythm', 'signal', 'novelty')]
    [string]$Mode = 'rhythm',
    
    [int]$IntervalMinutes = 30,
    
    [ValidateRange(1, 10)]
    [int]$Importance = 5,
    
    [string]$Reason = "",
    
    [int]$DurationHours = 0,  # 0 = 무제한

    # 공명(레조넌스)/멍함/두려움 노이즈를 메타데이터로 기록하기 위한 확장 파라미터
    # 숫자는 0~10 권장(미지정 시 -1로 저장)
    [ValidateRange(-1, 10)]
    [int]$ResonanceLevel = -1,

    [ValidateRange(-1, 10)]
    [int]$FearNoise = -1,

    # 비의미(언어적 해석을 끄고 시각/음성적 형태로만 인지) 상태 플래그
    [switch]$NonSemantic,

    # 추가 태그(예: john2, music, walk, resonance, calm 등)
    [string[]]$Tags
)

$ErrorActionPreference = "Continue"
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 경로 설정
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$ShortTermDir = Join-Path $WorkspaceRoot "outputs\memory\short_term"
$LongTermDir = Join-Path $WorkspaceRoot "outputs\memory\long_term"
$NoveltyDir = Join-Path $WorkspaceRoot "outputs\memory\novelty"

# 디렉토리 생성
@($ShortTermDir, $LongTermDir, $NoveltyDir) | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
    }
}

function Capture-Snapshot {
    param(
        [string]$TargetDir,
        [int]$ImportanceLevel,
        [string]$EventReason
    )
    
    $Timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
    $OutputFile = Join-Path $TargetDir "snapshot_$Timestamp.json"
    
    try {
        # 현재 활성 윈도우
        Add-Type @"
            using System;
            using System.Runtime.InteropServices;
            using System.Text;
            public class WindowHelper {
                [DllImport("user32.dll")]
                public static extern IntPtr GetForegroundWindow();
                [DllImport("user32.dll")]
                public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
                [DllImport("user32.dll")]
                public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
            }
"@ -ErrorAction SilentlyContinue
        
        $hwnd = [WindowHelper]::GetForegroundWindow()
        $processId = 0
        [WindowHelper]::GetWindowThreadProcessId($hwnd, [ref]$processId) | Out-Null
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        
        $title = New-Object System.Text.StringBuilder 256
        [WindowHelper]::GetWindowText($hwnd, $title, 256) | Out-Null
        
        # 태그 정규화(쉼표 포함 단일 문자열로 들어온 경우 배열로 변환)
        $tagsNormalized = @()
        if ($null -ne $Tags) {
            if (($Tags.Count -eq 1) -and ($Tags[0] -match ",")) {
                $tagsNormalized = ($Tags[0] -split ",") | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
            }
            else {
                $tagsNormalized = $Tags
            }
        }

        # 파생 상태 레이블 계산
        $stateLabel = 'normal'
        if (($ResonanceLevel -ge 7) -and ($FearNoise -ge 0) -and ($FearNoise -le 3)) { $stateLabel = 'john2_like' }

        # 스냅샷 데이터
        $snapshot = @{
            timestamp     = (Get-Date).ToString("o")
            importance    = $ImportanceLevel
            reason        = $EventReason
            mode          = $Mode
            mental_state  = @{
                resonance_level   = $ResonanceLevel
                fear_noise_level  = $FearNoise
                non_semantic_mode = [bool]$NonSemantic
                tags              = $tagsNormalized
                state_label       = $stateLabel
            }
            active_window = @{
                title   = $title.ToString()
                process = if ($process) { $process.Name } else { "Unknown" }
                pid     = $processId
            }
            system_state  = @{
                cpu_percent = [math]::Round((Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples[0].CookedValue, 2)
                memory_mb   = [math]::Round((Get-Process | Measure-Object WorkingSet64 -Sum).Sum / 1MB, 2)
            }
        }
        
        # JSON 저장
        $snapshot | ConvertTo-Json -Depth 5 | Out-File -FilePath $OutputFile -Encoding UTF8
        Write-Host "✓ Snapshot captured: $OutputFile (Importance: $ImportanceLevel)" -ForegroundColor Green
        
        return $snapshot
        
    }
    catch {
        Write-Host "✗ Snapshot failed: $_" -ForegroundColor Red
        return $null
    }
}

function Analyze-Novelty {
    param([hashtable]$CurrentSnapshot)
    
    # 최근 10개 스냅샷과 비교
    $recentSnapshots = Get-ChildItem -Path $ShortTermDir -Filter "snapshot_*.json" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 10
    
    if ($recentSnapshots.Count -lt 3) {
        Write-Host "  [Novelty] Not enough history, assuming normal" -ForegroundColor Yellow
        return $false
    }
    
    # 간단한 novelty 판단: 프로세스 이름이 최근 10개에 없으면 새로움
    $recentProcesses = $recentSnapshots | ForEach-Object {
        $content = Get-Content $_.FullName | ConvertFrom-Json
        $content.active_window.process
    } | Select-Object -Unique
    
    $currentProcess = $CurrentSnapshot.active_window.process
    $isNovel = $currentProcess -notin $recentProcesses
    
    if ($isNovel) {
        Write-Host "  [Novelty] New process detected: $currentProcess" -ForegroundColor Cyan
    }
    
    return $isNovel
}

function Promote-ToLongTerm {
    param([string]$SnapshotPath)
    
    $fileName = Split-Path $SnapshotPath -Leaf
    $longTermPath = Join-Path $LongTermDir $fileName
    
    Copy-Item -Path $SnapshotPath -Destination $longTermPath -Force
    Write-Host "  ⬆️ Promoted to long-term memory: $fileName" -ForegroundColor Magenta
}

# 메인 루프
Write-Host "`n═══ Rhythm-Based Snapshot System ═══" -ForegroundColor Cyan
Write-Host "Mode: $Mode | Interval: $IntervalMinutes min | Duration: $DurationHours hr" -ForegroundColor Gray
Write-Host ("Meta: Resonance={0}, FearNoise={1}, NonSemantic={2}, Tags=[{3}]`n" -f $ResonanceLevel, $FearNoise, [bool]$NonSemantic, ($Tags -join ', ')) -ForegroundColor DarkGray

$startTime = Get-Date
$iteration = 0

try {
    switch ($Mode) {
        'rhythm' {
            Write-Host "[Rhythm Mode] Starting low-frequency checkpoints..." -ForegroundColor Green
            
            while ($true) {
                $iteration++
                Write-Host "`n--- Checkpoint $iteration ---" -ForegroundColor Cyan
                
                # 저빈도 캡처 (중요도 2-4)
                $snapshot = Capture-Snapshot -TargetDir $ShortTermDir -ImportanceLevel 3 -EventReason "Periodic checkpoint"
                
                # 시간 체크
                if ($DurationHours -gt 0) {
                    $elapsed = (Get-Date) - $startTime
                    if ($elapsed.TotalHours -ge $DurationHours) {
                        Write-Host "`nDuration limit reached. Stopping." -ForegroundColor Yellow
                        break
                    }
                }
                
                # 대기
                Write-Host "Next checkpoint in $IntervalMinutes minutes..." -ForegroundColor Gray
                Start-Sleep -Seconds ($IntervalMinutes * 60)
            }
        }
        
        'signal' {
            Write-Host "[Signal Mode] High-resolution capture for important event..." -ForegroundColor Yellow
            
            $targetDir = if ($Importance -ge 7) { $LongTermDir } else { $ShortTermDir }

            # 레조넌스(공명) 기반 보강 규칙:
            # - 공명 >= 7 & 중요도 >= 5 이면 통찰성 높은 순간으로 간주하여 장기 기억으로 저장
            if (($ResonanceLevel -ge 7) -and ($Importance -ge 5)) {
                $targetDir = $LongTermDir
                Write-Host "⚡ HIGH RESONANCE - Auto-promoted to long-term memory (Resonance=$ResonanceLevel, Importance=$Importance)" -ForegroundColor Magenta
            }
            $snapshot = Capture-Snapshot -TargetDir $targetDir -ImportanceLevel $Importance -EventReason $Reason
            
            if ($Importance -ge 7) {
                Write-Host "⚡ HIGH IMPORTANCE - Auto-promoted to long-term memory" -ForegroundColor Magenta
            }
        }
        
        'novelty' {
            Write-Host "[Novelty Mode] Monitoring for new patterns..." -ForegroundColor Cyan
            
            while ($true) {
                $iteration++
                Write-Host "`n--- Check $iteration ---" -ForegroundColor Gray
                
                # 빠른 체크 (10초)
                $snapshot = Capture-Snapshot -TargetDir $ShortTermDir -ImportanceLevel 4 -EventReason "Novelty scan"
                
                # Novelty 분석
                if ($snapshot) {
                    $isNovel = Analyze-Novelty -CurrentSnapshot $snapshot
                    
                    if ($isNovel) {
                        # 새로운 패턴 발견 → 중요도 상승
                        Write-Host "🔔 NOVELTY DETECTED - Promoting importance" -ForegroundColor Magenta
                        $noveltyFile = Join-Path $NoveltyDir ("novelty_" + (Split-Path $snapshot -Leaf))
                        Copy-Item -Path (Join-Path $ShortTermDir (Split-Path $snapshot -Leaf)) -Destination $noveltyFile -Force
                    }
                }
                
                # 시간 체크
                if ($DurationHours -gt 0) {
                    $elapsed = (Get-Date) - $startTime
                    if ($elapsed.TotalHours -ge $DurationHours) {
                        Write-Host "`nDuration limit reached. Stopping." -ForegroundColor Yellow
                        break
                    }
                }
                
                # 짧은 대기 (novelty는 더 자주 체크)
                Start-Sleep -Seconds 10
            }
        }
    }
    
}
catch {
    Write-Host "`n✗ Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n✓ Snapshot system completed" -ForegroundColor Green
exit 0
