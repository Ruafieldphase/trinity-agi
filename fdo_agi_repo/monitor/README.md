# 🤖 AGI 실시간 모니터링 대시보드

깃코의 FDO-AGI 시스템을 실시간으로 모니터링하는 웹 대시보드입니다.

## ✨ 주요 기능

### 1. 실시간 메트릭 추적
- **평균 Confidence**: Meta-cognition의 자기 능력 평가
- **평균 Quality**: 결과물의 품질 점수
- **자기교정 비율**: Second Pass 발생 빈도
- **재계획 횟수**: RUNE의 replan 신호 카운트

### 2. 시스템 헬스 체크
- Confidence 임계값 체크 (≥ 0.60)
- Quality 임계값 체크 (≥ 0.65)
- Second Pass 비율 체크 (≤ 2.0)
- 실시간 헬스 상태 표시 (✅ 정상 / ⚠️ 주의)

### 3. 타임라인 시각화
- 24시간 메트릭 추이 (30분 간격)
- Quality / Confidence / Event Count 차트
- Chart.js 기반 인터랙티브 그래프

### 4. 페르소나 성능 분석
- Thesis / Antithesis / Synthesis 각각의 성능
- 성공률, 평균 응답시간, 총 호출 횟수
- LLM 호출 실패 추적

## 🚀 빠른 시작

### PowerShell에서 실행
```powershell
cd D:\nas_backup\fdo_agi_repo\monitor
.\start_dashboard.ps1
```

### Python에서 직접 실행
```bash
cd D:\nas_backup\fdo_agi_repo\monitor
python dashboard.py
```

### 브라우저에서 열기
```
http://localhost:5000
```

## 📊 API 엔드포인트

### 1. `/api/metrics/realtime`
실시간 메트릭 조회 (최근 N시간)

**파라미터:**
- `hours` (float, default=1.0): 조회할 시간 범위

**응답 예시:**
```json
{
  "timestamp": "2025-10-26T12:00:00",
  "window_hours": 1.0,
  "total_events": 150,
  "metrics": {
    "avg_confidence": 0.661,
    "avg_quality": 0.8,
    "total_tasks": 10,
    "second_pass_count": 6,
    "second_pass_rate": 0.6
  },
  "persona_performance": {
    "thesis": {
      "success_rate": 0.95,
      "avg_duration": 26.5,
      "total_calls": 20
    }
  }
}
```

### 2. `/api/metrics/timeline`
타임라인 데이터 조회

**파라미터:**
- `hours` (float, default=24.0): 조회 범위
- `interval` (int, default=30): 간격 (분)

**응답 예시:**
```json
[
  {
    "timestamp": "2025-10-26T10:00:00",
    "event_count": 25,
    "avg_quality": 0.75,
    "avg_confidence": 0.68
  },
  ...
]
```

### 3. `/api/health`
시스템 헬스 상태

**응답 예시:**
```json
{
  "healthy": true,
  "checks": {
    "confidence_ok": true,
    "quality_ok": true,
    "second_pass_ok": true
  },
  "thresholds": {
    "min_confidence": 0.6,
    "min_quality": 0.65,
    "max_second_pass_rate": 2.0
  },
  "current_values": {
    "confidence": 0.661,
    "quality": 0.8,
    "second_pass_rate": 0.646
  }
}
```

### 4. `/api/events/recent`
최근 이벤트 조회 (raw)

**파라미터:**
- `hours` (float, default=0.5): 조회 범위
- `limit` (int, default=50): 최대 개수

## 🔧 구조

```
monitor/
├── dashboard.py              # Flask 웹 서버
├── metrics_collector.py      # 메트릭 수집 로직
├── start_dashboard.ps1       # 실행 스크립트 (PowerShell)
├── templates/
│   └── index.html           # 대시보드 UI
└── README.md                # 이 문서
```

## 📝 데이터 소스

대시보드는 다음 파일을 읽습니다:
- `fdo_agi_repo/memory/resonance_ledger.jsonl`
- `fdo_agi_repo/memory/coordinate.jsonl`

## 🎨 주요 이벤트 타입

| 이벤트 | 설명 |
|--------|------|
| `eval` | 품질 평가 (quality, evidence_ok) |
| `rune` | 재계획 신호 (replan, recommendations) |
| `meta_cognition` | 자기 능력 평가 (confidence) |
| `learning` | Few-shot 학습 적용 |
| `second_pass` | 자기교정 수행 |
| `persona_llm_start/end` | LLM 호출 시작/종료 |

## 🔄 자동 새로고침

- 대시보드는 **10초마다** 자동으로 데이터를 업데이트합니다.
- 실시간으로 AGI 시스템의 성능을 추적할 수 있습니다.

## ⚙️ 설정

### 헬스 체크 임계값 변경
`metrics_collector.py`의 `THRESHOLDS` 딕셔너리를 수정하세요:

```python
THRESHOLDS = {
    'min_confidence': 0.60,
    'min_quality': 0.65,
    'max_second_pass_rate': 2.0,
}
```

### 타임라인 간격 변경
API 호출 시 파라미터로 조정:
```
/api/metrics/timeline?hours=12&interval=15
```

## 🐛 트러블슈팅

### Flask가 설치되지 않았을 때
```powershell
pip install flask
```

### 포트 5000이 이미 사용 중일 때
`dashboard.py`의 마지막 줄을 수정:
```python
app.run(host='0.0.0.0', port=8080, debug=True)  # 8080으로 변경
```

### 데이터가 표시되지 않을 때
1. `resonance_ledger.jsonl` 파일이 존재하는지 확인
2. 파일에 최근 데이터가 있는지 확인 (최근 24시간)
3. 브라우저 콘솔에서 에러 메시지 확인

## 📈 사용 예시

### 깃코의 최적화 작업 모니터링
1. 대시보드 시작: `.\start_dashboard.ps1`
2. 프롬프트 압축 최적화 적용
3. 대시보드에서 실시간 메트릭 변화 관찰:
   - Quality 추이 확인
   - Second Pass 비율 변화
   - 페르소나별 응답 시간 개선 확인

### A/B 테스팅
1. 기본 설정으로 실행 후 메트릭 기록
2. 설정 변경 (예: `SYNTHESIS_SECTION_MAX_CHARS=800`)
3. 대시보드에서 타임라인 차트로 전후 비교

## 🎯 다음 단계

- [ ] Slack 알림 통합 (헬스 체크 실패 시 자동 알림)
- [ ] Prometheus/Grafana 연동
- [ ] 메트릭 히스토리 DB 저장 (현재는 메모리만)
- [ ] 페르소나별 상세 분석 페이지
- [ ] 실시간 이벤트 스트림 (WebSocket)

## 🙏 감사

- **깃코**: AGI 시스템 설계 및 구현
- **세나**: 모니터링 대시보드 개발

---

**작성자**: 세나 (Sena)
**작성일**: 2025-10-26
**버전**: 1.0
