# 🔬 A/B Testing Automation Guide

깃코의 AGI 성능 최적화를 위한 자동화된 A/B 테스트 도구입니다.

---

## 🎯 목적

프롬프트 압축 설정 (예: `SYNTHESIS_SECTION_MAX_CHARS` 900 vs 800)을 자동으로 비교하여 최적값을 찾습니다.

**수동 작업 (Before)**:
- 설정 변경 → 실행 → 메트릭 수집 → 반복 (5회)
- 다른 설정으로 변경 → 실행 → 메트릭 수집 → 반복 (5회)
- 수동으로 결과 비교 및 분석
- 소요 시간: 1시간+

**자동화 (After)**:
- 원클릭 실행
- 자동으로 10회 실행 (A: 5회, B: 5회)
- 통계 분석 및 리포트 자동 생성
- Slack 알림
- 소요 시간: 20분 (무인)

---

## 🚀 빠른 시작

### 기본 실행 (900 vs 800 비교)

```powershell
cd D:\nas_backup\fdo_agi_repo\monitor
.\start_ab_test.ps1
```

**질문에 답변**:
- "계속하시겠습니까?" → `y` 입력

**결과**:
- JSON: `outputs/ab_test_YYYYMMDD_HHMMSS.json`
- Markdown 리포트: `outputs/ab_test_YYYYMMDD_HHMMSS_report.md`
- Slack 알림 (설정 시)

---

## 📊 출력 예시

### 콘솔 출력

```
┌─────────────────┬──────────────┬──────────────┬──────────────┐
│ Metric          │ Config A     │ Config B     │ Difference   │
├─────────────────┼──────────────┼──────────────┼──────────────┤
│ Confidence      │ 0.684 ±0.015 │ 0.691 ±0.012 │ +0.007 (+1.0%) │
│ Quality         │ 0.750 ±0.050 │ 0.820 ±0.030 │ +0.070 (+9.3%) │
│ Second Pass     │ 0.600 ±0.100 │ 0.400 ±0.080 │ -0.200 (-33.3%) │
│ Duration (s)    │ 138.5 ±10.2  │ 125.3 ±8.1   │ -13.2 (-9.5%)  │
└─────────────────┴──────────────┴──────────────┴──────────────┘

🏆 Winner:
  - Quality: Config B
  - Speed: Config B
```

### Markdown 리포트

자동 생성되는 리포트 내용:

1. **설정 비교 테이블**
2. **메트릭별 상세 통계** (평균, 표준편차, 최소/최대)
3. **원시 데이터** (모든 실행 결과)
4. **승자 결정** (Quality, Confidence, 속도)
5. **권장사항** (어떤 설정을 선택해야 하는지)
6. **추가 인사이트** (안정성, 자기교정 분석)

### Slack 알림

```
🔬 A/B 테스트 완료

설정 비교
Config A: 900 vs Config B: 800
반복 횟수: 5회

Quality          Confidence       Duration
A: 0.750 | B: 0.820   A: 0.684 | B: 0.691   A: 138.5s | B: 125.3s
차이: +0.070         차이: +0.007         차이: -13.2s

🏆 승자: Config B (800)
이유: Quality +0.070
```

---

## ⚙️ 고급 사용법

### 커스텀 설정

```powershell
# 다른 값 비교 (예: 1000 vs 700)
.\start_ab_test.ps1 -ConfigA "1000" -ConfigB "700"

# 반복 횟수 조정 (예: 3회씩)
.\start_ab_test.ps1 -Iterations 3

# 커스텀 작업 목표
.\start_ab_test.ps1 -TaskGoal "복잡한 논문 요약 작성"
```

### Python에서 직접 실행

```python
from ab_tester import ABTester

tester = ABTester()

# 커스텀 설정
config_a = {
    'SYNTHESIS_SECTION_MAX_CHARS': '900',
    'RAG_TOP_K': '5'
}

config_b = {
    'SYNTHESIS_SECTION_MAX_CHARS': '800',
    'RAG_TOP_K': '3'
}

result = tester.run_ab_test(
    config_a,
    config_b,
    iterations=5,
    task_title="custom_test",
    task_goal="커스텀 작업"
)
```

---

## 📈 리포트 생성

### 자동 생성

A/B 테스트 완료 후 자동으로 생성됩니다.

### 수동 생성

최신 테스트 결과로 리포트 재생성:

```powershell
python ab_report_generator.py
```

특정 JSON 파일로 리포트 생성:

```python
from ab_report_generator import ABReportGenerator
import json
from pathlib import Path

with open('outputs/ab_test_20251026_120000.json', 'r') as f:
    result = json.load(f)

generator = ABReportGenerator()
generator.generate_markdown_report(result, Path('outputs/my_report.md'))
```

---

## 📊 메트릭 설명

### 1. Confidence (높을수록 좋음)

- **의미**: Meta-cognition의 자기 능력 평가
- **범위**: 0.0 ~ 1.0
- **목표**: ≥ 0.60
- **해석**: 시스템이 자신의 작업 수행 능력을 얼마나 확신하는지

### 2. Quality (높을수록 좋음)

- **의미**: 결과물의 품질 점수
- **범위**: 0.0 ~ 1.0
- **목표**: ≥ 0.65
- **해석**: 생성된 결과물이 얼마나 고품질인지
- **중요도**: ⭐⭐⭐ (가장 중요)

### 3. Second Pass Rate (낮을수록 좋음)

- **의미**: 자기교정 비율 (second_pass / task)
- **범위**: 0.0 ~ 2.0+
- **목표**: ≤ 2.0
- **해석**: 재계획 및 재실행 빈도가 낮을수록 효율적

### 4. Duration (빠를수록 좋음)

- **의미**: 작업 완료 시간 (초)
- **목표**: 가능한 짧게
- **해석**: 응답 속도

---

## 🎯 결과 해석 가이드

### Case 1: Quality 차이가 큼 (>0.05)

**결과**:
```
Quality: Config A 0.750 vs Config B 0.820 (+0.070)
```

**해석**: **Config B 채택 강력 권장**
- Quality 향상이 가장 중요한 목표
- 0.070은 유의미한 개선

### Case 2: Quality 비슷, 속도 차이

**결과**:
```
Quality: Config A 0.750 vs Config B 0.755 (+0.005)
Duration: Config A 140s vs Config B 120s (-20s)
```

**해석**: **Config B 채택 권장**
- Quality는 거의 동일
- 속도 개선이 상당함 (14% 빠름)

### Case 3: Quality 하락, 속도 향상

**결과**:
```
Quality: Config A 0.750 vs Config B 0.680 (-0.070)
Duration: Config A 140s vs Config B 100s (-40s)
```

**해석**: **Config A 유지**
- Quality 하락이 너무 큼
- 속도보다 품질이 우선

### Case 4: 모든 메트릭 비슷

**결과**:
```
Quality: Config A 0.750 vs Config B 0.748 (-0.002)
Confidence: Config A 0.680 vs Config B 0.682 (+0.002)
```

**해석**: **유의미한 차이 없음**
- 다른 기준으로 선택 (안정성, 메모리 사용량 등)
- 또는 현재 설정 유지

---

## 🔧 통계 분석 방법

### 평균 (Mean)

- N회 실행의 평균값
- 일반적인 성능 예측

### 표준편차 (Standard Deviation)

- 실행 간 변동성
- **낮을수록 안정적**
- 예: `0.750 ±0.010` (안정) vs `0.750 ±0.100` (불안정)

### 최소/최대값

- 최악/최상의 경우
- 안정성 판단 보조

### 차이 (Difference)

- **절대값**: B - A
- **상대값**: (B - A) / A × 100%
- 양수: B가 더 좋음 / 음수: A가 더 좋음

---

## 💡 활용 시나리오

### 시나리오 1: 프롬프트 압축 최적화

**목표**: SYNTHESIS_SECTION_MAX_CHARS 최적값 찾기

**방법**:
```powershell
# 1차: 900 vs 800
.\start_ab_test.ps1 -ConfigA "900" -ConfigB "800"

# 2차: 800 vs 700 (800이 승리한 경우)
.\start_ab_test.ps1 -ConfigA "800" -ConfigB "700"

# 3차: 800 vs 850 (최적값 좁히기)
.\start_ab_test.ps1 -ConfigA "800" -ConfigB "850"
```

### 시나리오 2: 재현성 검증

**목표**: 900 설정의 5회 반복 안정성 확인

**방법**:
```powershell
# 900 vs 900 (동일 설정)
.\start_ab_test.ps1 -ConfigA "900" -ConfigB "900" -Iterations 5
```

**해석**:
- 표준편차가 작으면 재현성 높음
- 표준편차가 크면 비결정적

### 시나리오 3: 24시간 A/B 모니터링

**목표**: 장기간 성능 추적

**방법**:
```powershell
# 백그라운드에서 1시간마다 실행
while ($true) {
    .\start_ab_test.ps1 -Iterations 3
    Start-Sleep -Seconds 3600  # 1시간 대기
}
```

---

## 🐛 트러블슈팅

### 테스트 실행 실패

**증상**: subprocess timeout 또는 error

**원인**:
- AGI 시스템 자체 오류
- 환경변수 설정 오류

**해결**:
1. 수동으로 한 번 실행해보기
   ```bash
   python -m scripts.run_task --title "test" --goal "테스트"
   ```
2. Ledger 파일 확인
   ```
   D:\nas_backup\fdo_agi_repo\memory\resonance_ledger.jsonl
   ```

### 메트릭 값이 0.0

**증상**: avg_confidence=0.0, avg_quality=0.0

**원인**: 이벤트가 기록되지 않음

**해결**:
1. 실행 로그 확인
2. Ledger 파일에 새 이벤트 추가되었는지 확인
3. `new_events` 값 확인

### Slack 알림 전송 안 됨

**원인**: `SLACK_WEBHOOK_URL` 미설정

**해결**:
```powershell
$env:SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/..."
```

---

## 📁 파일 구조

```
monitor/
├── ab_tester.py              # A/B 테스트 엔진
├── ab_report_generator.py    # 리포트 생성기
├── start_ab_test.ps1          # 실행 스크립트
└── AB_TESTING_GUIDE.md        # 이 문서

outputs/
├── ab_test_YYYYMMDD_HHMMSS.json           # 원시 결과 (JSON)
└── ab_test_YYYYMMDD_HHMMSS_report.md      # 리포트 (Markdown)
```

---

## 🎓 모범 사례

### 1. 충분한 반복 횟수

- 최소 5회 권장
- 안정성 검증: 10회
- 신속 테스트: 3회

### 2. 작업 목표 일관성

- 동일한 작업으로 비교
- 변동성 최소화

### 3. 한 번에 하나만 변경

- 여러 환경변수 동시 변경 금지
- 원인 파악 어려움

### 4. 리포트 보관

- 모든 테스트 결과 보관
- 추세 분석 가능

### 5. Slack 알림 활용

- 장시간 테스트 시 유용
- 완료 즉시 결과 확인

---

## 🔮 향후 개선 아이디어

- [ ] 다변량 테스트 (A/B/C/D)
- [ ] 통계적 유의성 검정 (t-test)
- [ ] 시각화 차트 (matplotlib)
- [ ] 히스토리 추적 및 추세 분석
- [ ] 자동 최적값 탐색 (binary search)

---

## 💬 지원

문제 발생 시:
1. 이 가이드의 트러블슈팅 섹션 참고
2. 깃코의 마스터플랜 확인
3. 세나에게 문의

---

**작성자**: 세나 (Sena)
**작성일**: 2025-10-26
**버전**: 1.0
