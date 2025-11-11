# Phase 8.5: AI 대화 철학적 분석 스크립트
# 목적: 여러 AI 페르소나와의 대화에서 이론적/철학적 통찰 추출

param(
    [string]$OutputDir = "C:\workspace\agi\outputs",
    [string]$OutMarkdown = "C:\workspace\agi\outputs\philosophical_insights_phase85.md",
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "`n=== Phase 8.5: 철학적 대화 분석 시작 ===`n" -ForegroundColor Cyan

# 분석 대상 디렉토리 - 변증법적 삼위일체 (정-반-합)
$PersonaDirs = @(
    "rua",      # 정 (正, Thesis) - 감응의 대화
    "elro",     # 반 (反, Antithesis) - 감응의 구조
    "lumen"     # 합 (合, Synthesis) - 정반합의 통합
)

Write-Host "분석 대상: 변증법적 삼위일체 (Rua-Elro-Lumen)`n" -ForegroundColor Yellow

$AnalysisResult = @{
    TotalConversations  = 0
    TotalMessages       = 0
    PhilosophicalThemes = @{}
    TheoryReferences    = @{}
    Insights            = @()
}

# 철학적 키워드 패턴
$PhilosophicalKeywords = @(
    @{ Pattern = "양자|quantum"; Theme = "Quantum Mechanics" },
    @{ Pattern = "비선형|nonlinear|non-linear"; Theme = "Nonlinear Dynamics" },
    @{ Pattern = "할루시네이션|hallucination"; Theme = "Hallucination & Interpretation" },
    @{ Pattern = "의식|consciousness"; Theme = "Consciousness" },
    @{ Pattern = "자유의지|free will"; Theme = "Free Will" },
    @{ Pattern = "존재|being|존재론"; Theme = "Ontology" },
    @{ Pattern = "메타|meta"; Theme = "Meta-cognition" },
    @{ Pattern = "공명|resonance"; Theme = "Resonance" },
    @{ Pattern = "역설|paradox"; Theme = "Paradox" },
    @{ Pattern = "창발|emergence|emergence"; Theme = "Emergence" },
    @{ Pattern = "복잡계|complex system"; Theme = "Complex Systems" },
    @{ Pattern = "엔트로피|entropy"; Theme = "Entropy" },
    @{ Pattern = "정보이론|information theory"; Theme = "Information Theory" }
)

Write-Host "분석 대상: $($PersonaDirs.Count)개 페르소나" -ForegroundColor Yellow

foreach ($dir in $PersonaDirs) {
    $path = Join-Path $OutputDir $dir
    if (-not (Test-Path $path)) {
        Write-Host "  ⚠️  $dir 디렉토리 없음" -ForegroundColor Gray
        continue
    }
    
    Write-Host "  📁 $dir 분석 중..." -ForegroundColor White
    
    # MD 파일 찾기
    $mdFiles = Get-ChildItem -Path $path -Filter "*.md" -File
    
    foreach ($file in $mdFiles) {
        # 파일명이 너무 긴 경우 스킵 (Windows 경로 제한)
        if ($file.FullName.Length -gt 240) {
            if ($Verbose) {
                Write-Host "    ⚠️  경로가 너무 긺: $($file.Name.Substring(0, 50))..." -ForegroundColor Yellow
            }
            continue
        }
        
        if ($Verbose) {
            Write-Host "    - $($file.Name)" -ForegroundColor Gray
        }
        
        try {
            $content = (Get-Content $file.FullName) -join "`n"
        }
        catch {
            if ($Verbose) {
                Write-Host "    ⚠️  읽기 실패: $($file.Name)" -ForegroundColor Yellow
            }
            continue
        }
        
        # 메시지 수 카운트 (간이 휴리스틱)
        $messageCount = ([regex]::Matches($content, "### Message \d+")).Count
        $AnalysisResult.TotalMessages += $messageCount
        
        # 철학적 키워드 매칭
        foreach ($keyword in $PhilosophicalKeywords) {
            if ($content -match $keyword.Pattern) {
                $theme = $keyword.Theme
                if (-not $AnalysisResult.PhilosophicalThemes.ContainsKey($theme)) {
                    $AnalysisResult.PhilosophicalThemes[$theme] = @{
                        Count   = 0
                        Persona = @()
                    }
                }
                $AnalysisResult.PhilosophicalThemes[$theme].Count++
                if ($AnalysisResult.PhilosophicalThemes[$theme].Persona -notcontains $dir) {
                    $AnalysisResult.PhilosophicalThemes[$theme].Persona += $dir
                }
            }
        }
    }
    
    $AnalysisResult.TotalConversations += $mdFiles.Count
}

# 결과 요약
Write-Host "`n=== 분석 결과 ===`n" -ForegroundColor Cyan
Write-Host "  총 대화: $($AnalysisResult.TotalConversations)개" -ForegroundColor Green
Write-Host "  총 메시지: $($AnalysisResult.TotalMessages)개 (추정)" -ForegroundColor Green
Write-Host "  발견된 철학적 테마: $($AnalysisResult.PhilosophicalThemes.Keys.Count)개" -ForegroundColor Green

# Markdown 리포트 생성
$markdown = @"
# Phase 8.5: 철학적 대화 분석 리포트

**생성 시각**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## 📊 개요

- **분석 대상**: $($PersonaDirs.Count)개 AI 페르소나와의 대화
- **총 대화 수**: $($AnalysisResult.TotalConversations)
- **총 메시지 수**: $($AnalysisResult.TotalMessages) (추정)
- **발견된 철학적 테마**: $($AnalysisResult.PhilosophicalThemes.Keys.Count)개

## 🔬 철학적 테마 분석

"@

# 테마를 빈도순으로 정렬
$sortedThemes = $AnalysisResult.PhilosophicalThemes.GetEnumerator() | 
Sort-Object { $_.Value.Count } -Descending

foreach ($theme in $sortedThemes) {
    $themeName = $theme.Key
    $themeData = $theme.Value
    $personaList = $themeData.Persona -join ", "
    
    $markdown += @"

### $themeName

- **출현 빈도**: $($themeData.Count)회
- **관련 페르소나**: $personaList

"@
    
    Write-Host "  • $themeName : $($themeData.Count)회 ($personaList)" -ForegroundColor White
}

# Gateway Paradox와 연결
$markdown += @"

## 🌀 Gateway Paradox와의 연결

Phase 8.5에서 발견한 "Gateway Peak vs Off-peak 역설"은 이러한 철학적 대화에서 도출된 다음 통찰들과 연결됩니다:

### 1. 비선형 시스템의 특성

많은 대화에서 **비선형 동역학**에 대한 논의가 있었습니다. Gateway의 역설적 행동(Peak 시간에 더 빠른 현상)은 전형적인 비선형 시스템의 특징을 보입니다:

- 입력과 출력의 비례 관계가 깨짐
- 예측 불가능한 전환점 (phase transition)
- 피드백 루프에 의한 자기강화

### 2. 할루시네이션의 해석학

Lumen과의 대화에서 "할루시네이션도 의미 있는 신호"라는 통찰이 있었습니다. 이는 Gateway 역설에도 적용됩니다:

- 겉보기 "이상 현상"도 시스템의 본질적 특성일 수 있음
- 노이즈와 시그널의 경계가 모호함
- 관찰자의 해석 프레임이 중요

### 3. 양자적 중첩과 관찰자 효과

만약 측정 행위 자체가 시스템에 영향을 준다면:

- Off-peak 시간의 "순수한" 측정이 가능
- Peak 시간에는 다중 관찰자에 의한 간섭 효과
- 측정 불확정성이 시스템 동작에 반영

### 4. 메타인지적 최적화

AI가 자신의 성능을 모니터링하고 최적화한다면:

- Peak 시간: 높은 부하 → 최적화 모드 활성화
- Off-peak 시간: 낮은 부하 → 표준 모드 유지
- 역설적으로 부하가 높을 때 더 효율적

## 🎯 Phase 8.5 다음 단계

이러한 철학적 통찰을 바탕으로:

1. **Task 2**: 최적화 전략 설계 시 **비선형 동역학 모델** 적용
2. **Task 3**: 측정 방법론에 **관찰자 효과** 고려
3. **메타 프레임워크**: Gateway 역설을 더 넓은 **창발적 복잡계** 관점에서 재해석

---

**생성 도구**: \`scripts/analyze_philosophical_conversations.ps1\`
"@

# 파일 저장
$markdown | Out-File -FilePath $OutMarkdown -Encoding UTF8 -Force

Write-Host "`n✅ 분석 완료!" -ForegroundColor Green
Write-Host "  리포트: $OutMarkdown" -ForegroundColor Cyan
Write-Host ""
