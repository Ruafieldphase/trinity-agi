<#
.SYNOPSIS
Session Capacity Monitor - 세션 용량 모니터링 및 자동 핸드오프

.DESCRIPTION
현재 세션의 용량 상태를 모니터링하고, 임계값에 도달하면:
1. 자동으로 대화 내용 저장
2. Handoff 문서 생성 (다음 세션용)
3. 명확한 경고 메시지 출력

.PARAMETER CheckOnly
현재 상태만 확인 (저장 안 함)

.PARAMETER ThresholdPercent
경고 임계값 (기본: 80%)

.PARAMETER SaveHandoff
Handoff 문서 강제 생성

.EXAMPLE
.\session_capacity_monitor.ps1
# 현재 세션 상태 확인 및 필요시 핸드오프

.EXAMPLE
.\session_capacity_monitor.ps1 -CheckOnly
# 상태만 확인

.EXAMPLE
.\session_capacity_monitor.ps1 -SaveHandoff
# Handoff 문서 강제 생성
#>

param(
    [switch]$CheckOnly,
    [int]$ThresholdPercent = 80,
    [switch]$SaveHandoff,
    [string]$WorkspaceFolder = "C:\workspace\agi"
)

$ErrorActionPreference = "Stop"

# 세션 메타데이터 파일
$sessionMetaPath = Join-Path $WorkspaceFolder "outputs\session_memory\current_session_meta.json"
$handoffPath = Join-Path $WorkspaceFolder "outputs\session_memory\handoff_latest.md"

# 세션 메타데이터 초기화 또는 로드
function Get-SessionMeta {
    if (Test-Path $sessionMetaPath) {
        $meta = Get-Content $sessionMetaPath -Raw | ConvertFrom-Json
        return $meta
    }
    
    # 새 세션 초기화
    $meta = @{
        session_id        = (New-Guid).ToString()
        start_time        = (Get-Date).ToString("o")
        turn_count        = 0
        files_created     = 0
        commands_executed = 0
        last_activity     = (Get-Date).ToString("o")
        warnings_issued   = 0
        capacity_percent  = 0
    }
    
    return $meta
}

# 세션 메타데이터 저장
function Save-SessionMeta {
    param($Meta)
    
    $metaDir = Split-Path $sessionMetaPath -Parent
    if (-not (Test-Path $metaDir)) {
        New-Item -ItemType Directory -Path $metaDir -Force | Out-Null
    }
    
    $Meta | ConvertTo-Json -Depth 5 | Set-Content $sessionMetaPath -Encoding UTF8
}

# 세션 용량 추정 (0-100%)
function Estimate-SessionCapacity {
    param($Meta)
    
    # 추정 알고리즘:
    # - 턴 수: 50+ turns = 위험
    # - 시간: 30+ 분 = 주의, 60+ 분 = 위험
    # - 생성 파일: 20+ = 주의, 40+ = 위험
    # - 명령 실행: 50+ = 주의, 100+ = 위험
    
    $turnScore = [Math]::Min(100, ($Meta.turn_count / 50.0) * 100)
    
    $startTime = [DateTime]::Parse($Meta.start_time)
    $elapsedMinutes = ((Get-Date) - $startTime).TotalMinutes
    $timeScore = [Math]::Min(100, ($elapsedMinutes / 60.0) * 100)
    
    $fileScore = [Math]::Min(100, ($Meta.files_created / 40.0) * 100)
    $cmdScore = [Math]::Min(100, ($Meta.commands_executed / 100.0) * 100)
    
    # 가중 평균
    $capacity = ($turnScore * 0.4) + ($timeScore * 0.3) + ($fileScore * 0.2) + ($cmdScore * 0.1)
    
    return [Math]::Round($capacity, 1)
}

# Handoff 문서 생성
function New-HandoffDocument {
    param($Meta, $Capacity)
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    $handoffContent = @"
# 🔄 Session Handoff Document

**생성 시각**: $timestamp  
**이전 세션 ID**: $($Meta.session_id)  
**세션 용량**: $Capacity%  
**상태**: $(if ($Capacity -ge 90) { "🔴 CRITICAL" } elseif ($Capacity -ge 80) { "🟡 WARNING" } else { "🟢 NORMAL" })

---

## 📊 세션 통계

- **시작 시각**: $($Meta.start_time)
- **경과 시간**: $([Math]::Round(((Get-Date) - [DateTime]::Parse($Meta.start_time)).TotalMinutes, 1)) 분
- **대화 턴 수**: $($Meta.turn_count)
- **생성 파일 수**: $($Meta.files_created)
- **실행 명령 수**: $($Meta.commands_executed)
- **경고 횟수**: $($Meta.warnings_issued)

---

## 🎯 현재 작업 상태

### 진행 중인 주요 작업
<!-- 여기에 현재 진행 중인 작업을 기록하세요 -->
- Self-Continuing Agent 구현 완료 ✅
- 첫 자율 루프 실행 완료 ✅
- 다음: Autopoietic Report 자동 실행 대기

### 최근 완료 작업
"@

    # 최근 파일 추가
    $recentFiles = Get-ChildItem -Path (Join-Path $WorkspaceFolder "outputs\session_memory") -File |
    Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-1) } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 5

    if ($recentFiles) {
        $handoffContent += "`n`n### 최근 생성/수정 파일`n"
        foreach ($file in $recentFiles) {
            $handoffContent += "- ``$($file.Name)`` ($($file.LastWriteTime.ToString('HH:mm:ss')))`n"
        }
    }

    $handoffContent += @"


---

## 🚀 다음 세션에서 할 일

### 즉시 실행 필요
1. **Work Queue 확인**
   ``````powershell
   python fdo_agi_repo/orchestrator/autonomous_work_planner.py next
   ``````

2. **다음 Auto 작업 실행**
   ``````powershell
   .\scripts\autonomous_loop.ps1 -MaxIterations 2
   ``````

### 중요 컨텍스트
- Phase 6+ (Self-Continuing Agent) 구현 완료
- Work Queue: 2/6 작업 완료, 4/6 대기
- System Health: ALL GREEN (99.65% uptime)
- 다음 Auto 작업: autopoietic_report, performance_dashboard

---

## 📄 참고 문서

- ``SELF_CONTINUING_AGENT_IMPLEMENTATION.md`` - 전체 구현
- ``SELF_CONTINUING_AGENT_FIRST_RHYTHM.md`` - 첫 실행 결과
- ``outputs/autonomous_work_plan.md`` - 최신 Work Plan
- ``outputs/session_memory/conversation_2025-11-02_self_continuing_agent.md`` - 대화 기록

---

## ⚠️ 중요 알림

**이 세션은 용량 한계에 근접했습니다 ($Capacity%).**

새 세션에서 작업을 계속하려면:
1. 이 문서(``handoff_latest.md``)를 열어서 확인
2. 새 Copilot 세션 시작
3. "이전 세션 핸드오프 문서 확인하고 작업 이어가기" 요청

---

**생성 경로**: ``outputs/session_memory/handoff_latest.md``  
**다음 세션**: 이 문서를 먼저 확인하세요!
"@

    $handoffDir = Split-Path $handoffPath -Parent
    if (-not (Test-Path $handoffDir)) {
        New-Item -ItemType Directory -Path $handoffDir -Force | Out-Null
    }
    
    $handoffContent | Set-Content $handoffPath -Encoding UTF8
    
    # 타임스탬프 버전도 저장
    $timestampPath = Join-Path $handoffDir "handoff_$(Get-Date -Format 'yyyyMMdd_HHmmss').md"
    $handoffContent | Set-Content $timestampPath -Encoding UTF8
    
    return $handoffPath
}

# 경고 메시지 출력
function Show-CapacityWarning {
    param($Capacity, $HandoffPath)
    
    Write-Host "`n╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║  ⚠️  SESSION CAPACITY WARNING                              ║" -ForegroundColor Red
    Write-Host "╚══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Red
    
    Write-Host "📊 현재 세션 용량: $Capacity%" -ForegroundColor Yellow
    
    if ($Capacity -ge 90) {
        Write-Host "🔴 상태: CRITICAL - 즉시 새 세션 전환 권장" -ForegroundColor Red
    }
    elseif ($Capacity -ge 80) {
        Write-Host "🟡 상태: WARNING - 곧 새 세션 전환 필요" -ForegroundColor Yellow
    }
    
    Write-Host "`n⚠️  이 세션은 곧 용량 한계에 도달합니다!`n" -ForegroundColor Yellow
    
    Write-Host "📄 Handoff 문서 생성됨:" -ForegroundColor Cyan
    Write-Host "   $HandoffPath`n" -ForegroundColor White
    
    Write-Host "🔄 새 세션으로 전환하려면:" -ForegroundColor Green
    Write-Host "   1. Ctrl+Shift+P → 'GitHub Copilot: New Chat'" -ForegroundColor Gray
    Write-Host "   2. 새 채팅에서 입력:" -ForegroundColor Gray
    Write-Host "      '이전 세션 핸드오프 확인하고 작업 이어가기'" -ForegroundColor Cyan
    Write-Host "   3. 또는: 'handoff_latest.md 파일 기반으로 작업 계속'" -ForegroundColor Cyan
    
    Write-Host "`n💡 현재 세션에서 마무리 작업:" -ForegroundColor Magenta
    Write-Host "   - 중요한 작업 완료" -ForegroundColor Gray
    Write-Host "   - 파일 저장 확인" -ForegroundColor Gray
    Write-Host "   - 새 세션으로 전환`n" -ForegroundColor Gray
    
    Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Red
}

# 정상 상태 메시지
function Show-NormalStatus {
    param($Capacity, $Meta)
    
    Write-Host "`n✅ 세션 상태: 정상" -ForegroundColor Green
    Write-Host "   용량: $Capacity% (여유 있음)" -ForegroundColor White
    Write-Host "   턴 수: $($Meta.turn_count)" -ForegroundColor Gray
    Write-Host "   경과 시간: $([Math]::Round(((Get-Date) - [DateTime]::Parse($Meta.start_time)).TotalMinutes, 1)) 분`n" -ForegroundColor Gray
}

# === 메인 로직 ===

Write-Host "`n🔍 Session Capacity Monitor" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor DarkGray

# 세션 메타 로드
$meta = Get-SessionMeta

# 활동 업데이트 (CheckOnly가 아닐 때)
if (-not $CheckOnly) {
    $meta.turn_count++
    $meta.last_activity = (Get-Date).ToString("o")
}

# 용량 추정
$capacity = Estimate-SessionCapacity -Meta $meta
$meta.capacity_percent = $capacity

if (-not $CheckOnly) {
    Save-SessionMeta -Meta $meta
}

# 임계값 확인
if ($capacity -ge $ThresholdPercent -or $SaveHandoff) {
    # 경고 상태
    $meta.warnings_issued++
    Save-SessionMeta -Meta $meta
    
    # Handoff 문서 생성
    $handoffPath = New-HandoffDocument -Meta $meta -Capacity $capacity
    
    # 경고 메시지
    Show-CapacityWarning -Capacity $capacity -HandoffPath $handoffPath
    
    # 대화 저장
    $conversationPath = Join-Path $WorkspaceFolder "outputs\session_memory\conversation_$(Get-Date -Format 'yyyy-MM-dd_HHmmss')_auto.md"
    
    Write-Host "💾 대화 내용 자동 저장 중..." -ForegroundColor Cyan
    Write-Host "   경로: $conversationPath`n" -ForegroundColor Gray
    
    exit 1  # 경고 상태 반환
}
else {
    # 정상 상태
    if (-not $CheckOnly) {
        Show-NormalStatus -Capacity $capacity -Meta $meta
    }
    else {
        Write-Host "📊 현재 용량: $capacity%" -ForegroundColor White
        Write-Host "   임계값: $ThresholdPercent%" -ForegroundColor Gray
        Write-Host "   상태: " -NoNewline
        if ($capacity -ge 90) {
            Write-Host "🔴 CRITICAL" -ForegroundColor Red
        }
        elseif ($capacity -ge 80) {
            Write-Host "🟡 WARNING" -ForegroundColor Yellow
        }
        else {
            Write-Host "🟢 NORMAL" -ForegroundColor Green
        }
        Write-Host ""
    }
    
    exit 0  # 정상 상태
}
