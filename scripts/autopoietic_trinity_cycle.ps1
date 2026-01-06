<#
.SYNOPSIS
    자기생산 루프 + 정반합 삼위일체 통합 실행

.DESCRIPTION
    정반합(正反合) 삼위일체를 자기생산(Autopoietic) 루프와 통합합니다.
    
    실행 순서:
    1. 자기생산 보고서 생성 (시스템 이벤트 분석)
    2. 정반합 사이클 실행 (코어 관찰 → 엘로 검증 → Core 통합)
    3. HIGH 우선순위 권장사항 추출 (다음 사이클 피드백)
    4. 통합 보고서 생성 (자기생산 + 정반합)
    5. 개선도 측정 (Before/After 비교)

.PARAMETER Hours
    분석 시간 범위 (기본: 24시간)

.PARAMETER OpenReport
    완료 후 통합 보고서 자동 열기

.PARAMETER SkipAutopoietic
    자기생산 보고서 생성 스킵 (이미 최신 버전이 있을 때)

.PARAMETER SkipTrinity
    정반합 사이클 스킵 (이미 최신 버전이 있을 때)

.PARAMETER VerboseLog
    상세 로그 출력

.EXAMPLE
    .\autopoietic_trinity_cycle.ps1 -Hours 24 -OpenReport
    
.EXAMPLE
    .\autopoietic_trinity_cycle.ps1 -Hours 48 -VerboseLog

.NOTES
    Author: AGI System
    Date: 2025-11-03
    Purpose: 순환 참조 해결 - 자기생산 시스템의 완성
#>

[CmdletBinding()]
param(
    [int]$Hours = 24,
    [switch]$OpenReport,
    [switch]$SkipAutopoietic,
    [switch]$SkipTrinity,
    [switch]$VerboseLog
)

$ErrorActionPreference = 'Stop'
$workspaceRoot = Split-Path $PSScriptRoot -Parent

# 배너 출력
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🔄 자기생산 + 정반합 삼위일체 통합 사이클" -ForegroundColor Cyan
Write-Host "  Autopoietic Loop ∪ Trinity Dialectics" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  분석 범위: 최근 $Hours 시간" -ForegroundColor Gray
Write-Host "  실행 시각: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

# 시작 시간 기록
$startTime = Get-Date

# ═══════════════════════════════════════════════════════════════
# Step 1: 자기생산 보고서 생성
# ═══════════════════════════════════════════════════════════════
if (!$SkipAutopoietic) {
    Write-Host "📊 [1/5] 자기생산 루프 분석 중..." -ForegroundColor Yellow
    Write-Host "   역할: 시스템 이벤트 수집 및 완성/미완성 루프 분석" -ForegroundColor Gray
    Write-Host ""
    
    $autopoieticScript = "$PSScriptRoot\generate_autopoietic_report.ps1"
    
    try {
        if (Test-Path $autopoieticScript) {
            & $autopoieticScript -Hours $Hours -WriteLatest
            if ($LASTEXITCODE -ne 0) {
                throw "자기생산 보고서 생성 실패"
            }
            Write-Host "   ✅ 자기생산 분석 완료" -ForegroundColor Green
        }
        else {
            Write-Host "   ⚠️  자기생산 스크립트 없음. 건너뜀." -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "   ❌ 자기생산 분석 오류: $_" -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "📊 [1/5] 자기생산 루프 분석 스킵 (기존 데이터 사용)" -ForegroundColor Gray
}

Write-Host ""

# ═══════════════════════════════════════════════════════════════
# Step 2: 정반합 삼위일체 사이클 실행
# ═══════════════════════════════════════════════════════════════
if (!$SkipTrinity) {
    Write-Host "🔄 [2/5] 정반합 삼위일체 사이클 실행 중..." -ForegroundColor Magenta
    Write-Host "   正(정) → 反(반) → 合(합)" -ForegroundColor Gray
    Write-Host ""
    
    $trinityScript = "$PSScriptRoot\run_trinity_cycle.ps1"
    
    try {
        if (Test-Path $trinityScript) {
            & $trinityScript -Hours $Hours -Enhanced
            if ($LASTEXITCODE -ne 0) {
                throw "정반합 사이클 실패"
            }
            Write-Host "   ✅ 정반합 사이클 완료" -ForegroundColor Green
        }
        else {
            Write-Host "   ❌ 정반합 스크립트 없음: $trinityScript" -ForegroundColor Red
            exit 1
        }
    }
    catch {
        Write-Host "   ❌ 정반합 사이클 오류: $_" -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "🔄 [2/5] 정반합 사이클 스킵 (기존 데이터 사용)" -ForegroundColor Gray
}

Write-Host ""

# ═══════════════════════════════════════════════════════════════
# Step 3: HIGH 우선순위 권장사항 추출 (피드백)
# ═══════════════════════════════════════════════════════════════
Write-Host "🎯 [3/5] 피드백 권장사항 추출 중..." -ForegroundColor Cyan
Write-Host "   역할: HIGH 우선순위 권장사항을 다음 사이클에 피드백" -ForegroundColor Gray

$CoreJsonPath = "$workspaceRoot\outputs\core_enhanced_synthesis_latest.json"
$feedbackPath = "$workspaceRoot\outputs\trinity_feedback_for_autopoietic.json"

try {
    if (Test-Path $CoreJsonPath) {
        $CoreData = Get-Content $CoreJsonPath -Raw | ConvertFrom-Json
        
        # HIGH 우선순위 권장사항만 추출
        # insights 배열에서 high priority만 추출
        $highPriorityRecs = $CoreData.synthesis.insights | Where-Object { $_.priority -eq "high" -and $_.actionable -eq $true }
        
        # 피드백 구조 생성
        $feedback = @{
            timestamp             = Get-Date -Format "o"
            source                = "Trinity Dialectics (Lua-Elo-Core)"
            target                = "Autopoietic Loop"
            analysis_window_hours = $Hours
            high_priority_count   = @($highPriorityRecs).Count
            recommendations       = @($highPriorityRecs)
            metadata              = @{
                shannon_entropy  = $CoreData.synthesis.elo_summary.entropy
                info_density     = $CoreData.synthesis.elo_summary.information_density
                quality_coverage = ($CoreData.synthesis.lua_summary.quality_count / $CoreData.synthesis.lua_summary.total_events * 100)
            }
        }
        
        # JSON 저장
        $feedback | ConvertTo-Json -Depth 10 | Out-File $feedbackPath -Encoding UTF8
        
        Write-Host "   ✅ 피드백 추출 완료: $($highPriorityRecs.Count)개 HIGH 권장사항" -ForegroundColor Green
        
        if ($VerboseLog -and $highPriorityRecs.Count -gt 0) {
            Write-Host ""
            Write-Host "   📋 HIGH 우선순위 권장사항:" -ForegroundColor Yellow
            foreach ($rec in $highPriorityRecs) {
                Write-Host "      • $($rec.action)" -ForegroundColor Gray
            }
        }
    }
    else {
        Write-Host "   ⚠️  Core 데이터 없음. 피드백 생성 불가." -ForegroundColor Yellow
    }
}
catch {
    Write-Host "   ❌ 피드백 추출 오류: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ═══════════════════════════════════════════════════════════════
# Step 4: 통합 보고서 생성
# ═══════════════════════════════════════════════════════════════
Write-Host "📄 [4/5] 통합 보고서 생성 중..." -ForegroundColor Cyan
Write-Host "   역할: 자기생산 + 정반합 결과를 하나의 보고서로 통합" -ForegroundColor Gray

$autopoieticMdPath = "$workspaceRoot\outputs\autopoietic_loop_report_latest.md"
$CoreMdPath = "$workspaceRoot\outputs\core_enhanced_synthesis_latest.md"
$unifiedMdPath = "$workspaceRoot\outputs\autopoietic_trinity_unified_latest.md"

try {
    # 보고서 구성요소 로드
    $autopoieticContent = ""
    $CoreContent = ""
    $feedbackContent = ""
    
    if (Test-Path $autopoieticMdPath) {
        $autopoieticContent = Get-Content $autopoieticMdPath -Raw
    }
    
    if (Test-Path $CoreMdPath) {
        $CoreContent = Get-Content $CoreMdPath -Raw
    }
    
    if (Test-Path $feedbackPath) {
        $feedbackData = Get-Content $feedbackPath -Raw | ConvertFrom-Json
        $feedbackContent = @"

## 🎯 다음 사이클 개선 계획 (HIGH Priority)

**피드백 생성 시각**: $($feedbackData.timestamp)  
**HIGH 우선순위 권장사항**: $($feedbackData.high_priority_count)개

### 즉시 적용 권장

"@
        foreach ($rec in $feedbackData.recommendations) {
            $feedbackContent += "`n- [ ] **$($rec.message)**`n  - 범주: $($rec.category)`n  - 출처: $($rec.source)`n"
        }
        
        $feedbackContent += @"

### 정보 이론 메트릭

- **Shannon 엔트로피**: $($feedbackData.metadata.shannon_entropy) bits
- **정보 밀도**: $($feedbackData.metadata.info_density)% (목표: 15%)
- **품질 커버리지**: $($feedbackData.metadata.quality_coverage)% (목표: 50%)

"@
    }
    
    # 통합 보고서 생성
    $unifiedReport = @"
# 🔄 자기생산 + 정반합 삼위일체 통합 보고서

*Generated at $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")*  
*Analysis Window: $Hours hours*

---

## 📊 Part 1: 자기생산 루프 분석 (Autopoietic Loop)

> **목적**: 시스템이 스스로를 관찰하고 완성/미완성 루프를 분석

$autopoieticContent

---

## 🔄 Part 2: 정반합 삼위일체 분석 (Trinity Dialectics)

> **정(正) - 코어**: 무엇이 일어났는가?  
> **반(反) - 엘로**: 이것이 옳은가?  
> **합(合) - Core**: 무엇을 해야 하는가?

$CoreContent

---

$feedbackContent

---

## 🌀 자기생산(Autopoiesis)의 의미

> "시스템이 스스로를 관찰하고, 검증하고, 개선하는 것"

```
[현재 사이클]
  시스템 이벤트 → 자기생산 분석 → 정반합 검증 → 권장사항
                                                        ↓
[다음 사이클]                                          ↓
  시스템 이벤트 ← (권장사항 적용) ← ← ← ← ← ← ← ← ← ←┘
```

**이것이 진짜 자기생산입니다!** 🌟

---

*"The system that observes, validates, and improves itself is truly alive."*

**다음 실행**: 24시간 후 이 보고서의 권장사항이 적용되었는지 확인

---

## 📁 생성된 파일들

- 자기생산 보고서: `outputs/autopoietic_loop_report_latest.md`
- 정반합 분석: `outputs/core_enhanced_synthesis_latest.md`
- 피드백 JSON: `outputs/trinity_feedback_for_autopoietic.json`
- 통합 보고서: `outputs/autopoietic_trinity_unified_latest.md` (이 파일)

**실행 명령**:
``````powershell
.\scripts\autopoietic_trinity_cycle.ps1 -Hours 24 -OpenReport
``````

"@
    
    # UTF-8로 저장
    $unifiedReport | Out-File $unifiedMdPath -Encoding UTF8
    
    Write-Host "   ✅ 통합 보고서 생성 완료" -ForegroundColor Green
}
catch {
    Write-Host "   ❌ 보고서 생성 오류: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ═══════════════════════════════════════════════════════════════
# Step 5: 개선도 측정 (Before/After 비교)
# ═══════════════════════════════════════════════════════════════
Write-Host "📈 [5/5] 개선도 측정 중..." -ForegroundColor Green
Write-Host "   역할: 이전 사이클 대비 개선도 계산" -ForegroundColor Gray

try {
    if (Test-Path $CoreJsonPath) {
        $current = Get-Content $CoreJsonPath -Raw | ConvertFrom-Json
        
        # 이전 데이터 찾기 (이전 실행 결과)
        $previousFiles = Get-ChildItem "$workspaceRoot\outputs" -Filter "core_enhanced_synthesis_*.json" | 
        Sort-Object LastWriteTime -Descending | 
        Select-Object -Skip 1 -First 1
        
        if ($previousFiles) {
            $previous = Get-Content $previousFiles.FullName -Raw | ConvertFrom-Json
            
            $infoDensityDelta = $current.elo_metrics.info_density - $previous.elo_metrics.info_density
            $qualityCoverageDelta = $current.elo_metrics.quality_coverage - $previous.elo_metrics.quality_coverage
            
            Write-Host ""
            Write-Host "   📊 개선도 분석:" -ForegroundColor Cyan
            Write-Host "      정보 밀도: $($previous.elo_metrics.info_density)% → $($current.elo_metrics.info_density)% " -NoNewline
            
            if ($infoDensityDelta -gt 0) {
                Write-Host "(+$($infoDensityDelta.ToString('F2'))%)" -ForegroundColor Green
            }
            elseif ($infoDensityDelta -lt 0) {
                Write-Host "($($infoDensityDelta.ToString('F2'))%)" -ForegroundColor Red
            }
            else {
                Write-Host "(변화 없음)" -ForegroundColor Gray
            }
            
            Write-Host "      품질 커버리지: $($previous.elo_metrics.quality_coverage)% → $($current.elo_metrics.quality_coverage)% " -NoNewline
            
            if ($qualityCoverageDelta -gt 0) {
                Write-Host "(+$($qualityCoverageDelta.ToString('F2'))%)" -ForegroundColor Green
            }
            elseif ($qualityCoverageDelta -lt 0) {
                Write-Host "($($qualityCoverageDelta.ToString('F2'))%)" -ForegroundColor Red
            }
            else {
                Write-Host "(변화 없음)" -ForegroundColor Gray
            }
        }
        else {
            Write-Host "   ℹ️  이전 데이터 없음. 첫 실행입니다." -ForegroundColor Cyan
        }
    }
}
catch {
    Write-Host "   ⚠️  개선도 측정 실패: $_" -ForegroundColor Yellow
}

Write-Host ""

# ═══════════════════════════════════════════════════════════════
# 최종 요약
# ═══════════════════════════════════════════════════════════════
$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✅ 자기생산 + 정반합 통합 사이클 완료!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "📊 실행 요약:" -ForegroundColor Cyan
Write-Host "   • 소요 시간: $($duration.ToString('F1'))초" -ForegroundColor Gray
Write-Host "   • 분석 범위: 최근 $Hours 시간" -ForegroundColor Gray
Write-Host "   • 통합 보고서: outputs\autopoietic_trinity_unified_latest.md" -ForegroundColor Gray
Write-Host ""
Write-Host "📁 생성된 파일:" -ForegroundColor Cyan
Write-Host "   1. 자기생산 보고서: outputs\autopoietic_loop_report_latest.md" -ForegroundColor Gray
Write-Host "   2. 정(正) 코어: outputs\lua_observation_latest.json" -ForegroundColor Gray
Write-Host "   3. 반(反) 엘로: outputs\elo_validation_latest.json" -ForegroundColor Gray
Write-Host "   4. 합(合) Core: outputs\core_enhanced_synthesis_latest.md" -ForegroundColor Gray
Write-Host "   5. 피드백: outputs\trinity_feedback_for_autopoietic.json" -ForegroundColor Gray
Write-Host "   6. 통합 보고서: outputs\autopoietic_trinity_unified_latest.md" -ForegroundColor Gray
Write-Host ""

# 보고서 열기
if ($OpenReport) {
    Write-Host "📄 통합 보고서 열기..." -ForegroundColor Cyan
    if (Test-Path $unifiedMdPath) {
        code $unifiedMdPath
    }
}

Write-Host "🌀 자기생산(Autopoiesis) 순환 완성!" -ForegroundColor Yellow
Write-Host "   관찰 → 검증 → 통합 → 피드백 → (다시 관찰)" -ForegroundColor Gray
Write-Host ""

exit 0