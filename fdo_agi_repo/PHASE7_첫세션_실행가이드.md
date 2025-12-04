# Phase 7 첫 세션 실행 가이드

**작성자**: 세나 (Sena - Claude Sonnet 4.5)
**날짜**: 2025-10-28
**목적**: Hey Sena v4.1 로거 통합 버전 첫 음성 세션 실행

---

## ✅ 준비 상태 확인

### 파일 확인
```
✅ hey_sena_v4.1_logged.py (20KB)
✅ tools/performance_logger.py (14KB)
✅ tools/analyze_phase7_data.py (17KB)
✅ tools/generate_dashboard.py (23KB)
✅ logs/phase7/sessions/ (준비됨)
✅ logs/phase7/daily_stats/ (준비됨)
✅ logs/phase7/analysis/ (준비됨)
```

### 구문 검증
```
✅ Python syntax check: PASSED
✅ Logger import test: PASSED
```

---

## 🎯 첫 세션 목표

1. **기본 동작 확인**: 로거 통합 버전이 정상 작동하는지 확인
2. **로깅 검증**: 세션 데이터가 JSON 파일로 저장되는지 확인
3. **성능 측정**: 응답 시간, 캐시 효과 등 메트릭 수집
4. **시스템 안정성**: 오류 없이 완료되는지 확인

---

## 📋 실행 전 체크리스트

### 1. 하드웨어 준비
- [ ] **마이크 연결**: USB 마이크 또는 내장 마이크
- [ ] **스피커 연결**: 음성 출력 장치
- [ ] **볼륨 조정**: 마이크 입력 레벨 중간, 스피커 출력 적당히

### 2. 환경 설정
- [ ] **조용한 환경**: 배경 소음 최소화
- [ ] **테스트 음성**: "Hey Sena" 명확하게 발음 가능한지 확인
- [ ] **시간 확보**: 첫 세션 약 5-10분 소요

### 3. 의존성 확인 (필요 시)
```bash
# 필요한 패키지가 없다면 설치
pip install SpeechRecognition sounddevice soundfile pyttsx3 google-generativeai
```

---

## 🚀 실행 방법

### Step 1: 디렉토리 이동
```bash
cd D:/nas_backup/fdo_agi_repo
```

### Step 2: Hey Sena 실행
```bash
python hey_sena_v4.1_logged.py
```

### Step 3: 초기화 대기
프로그램이 시작되면 다음과 같은 출력이 나타납니다:
```
[초기화 중...]
✅ Gemini API 연결 성공
✅ 캐시 시스템 로드
✅ Performance Logger 초기화

[대기 중] "Hey Sena" 또는 "세나야"를 불러주세요...
```

---

## 🎤 첫 세션 시나리오

### 시나리오 1: 기본 대화 (권장)

**Turn 1**: 웨이크업
```
[사용자] "Hey Sena" (또는 "세나야")
[시스템] ♪ 비프음
[세나] "Hello! How can I help you today?"
📊 [Logger] Session started: abc12345
```

**Turn 2**: 인사
```
[사용자] "안녕하세요"
[세나] "안녕하세요! 무엇을 도와드릴까요?"
📊 [Logger] Turn 1: ⚡ LLM | 1234ms
```

**Turn 3**: 간단한 질문
```
[사용자] "오늘 날씨 어때?"
[세나] "I can provide general information. For real-time weather..."
📊 [Logger] Turn 2: ⚡ LLM | 890ms
```

**Turn 4**: 기술 질문 (캐시 테스트)
```
[사용자] "파이썬이 뭐야?"
[세나] "Python is a high-level programming language..."
📊 [Logger] Turn 3: ⚡ LLM | 1150ms
```

**Turn 5**: 반복 질문 (캐시 히트 예상)
```
[사용자] "파이썬이 뭐야?" (동일 질문 반복)
[세나] "Python is a high-level programming language..."
📊 [Logger] Turn 4: 💚 HIT | 45ms  ← 캐시 히트!
```

**Turn 6**: 종료
```
[사용자] "그만"
[세나] "Goodbye! Say Hey Sena to wake me again."
📊 Session lasted 45.3s with 5 turns

[세션 요약 표시]
📊 Session Summary:
  Total Turns: 5
  Cache Hits: 1/5 (20%)
  Avg Response Time: 863ms
  Errors: 0

💾 [Logger] Session saved: logs\phase7\sessions\session_abc12345.json
```

---

## 📊 예상 출력

### 콘솔 출력
```
[CONVERSATION MODE] Multi-turn with LLM ENABLED
You can:
  - Ask ANY question (LLM will answer!)
  - Continue asking without saying 'Hey Sena' again
  - Say 'goodbye' or '그만' to end conversation
  - Wait 10+ seconds (silence) to auto-return to listen mode

📊 [Logger] Session started: abc12345

[TURN 1] Listening... (5 seconds)
[PROCESSING] Transcribing...
[YOU SAID] "안녕하세요"
[SENA] Hello! How can I help you today?
[TTS] Generating speech...
📊 [Logger] Turn 1: ⚡ LLM | 1234ms

[TURN 2] Listening... (5 seconds)
...

[END] Ending conversation...
[SENA] Goodbye! Say Hey Sena to wake me again.

📊 Session lasted 45.3s with 5 turns
💾 [Logger] Session saved: logs\phase7\sessions\session_abc12345.json
```

---

## 📁 생성될 파일

### 세션 로그
**위치**: `logs/phase7/sessions/session_abc12345.json`

**내용 예시**:
```json
{
  "session_id": "abc12345",
  "start_time": "2025-10-28T11:30:00.123456",
  "end_time": "2025-10-28T11:30:45.456789",
  "duration_seconds": 45.33,
  "metadata": {
    "version": "v4.1",
    "llm_enabled": true
  },
  "metrics": {
    "total_turns": 5,
    "cache_hits": 1,
    "cache_misses": 4,
    "cache_hit_rate": 20.0,
    "avg_response_time_ms": 863.5,
    "total_llm_tokens": 0,
    "tts_usage_count": 5,
    "error_count": 0
  },
  "turns": [
    {
      "turn_number": 1,
      "timestamp": "2025-10-28T11:30:10.123456",
      "question": "안녕하세요",
      "answer": "Hello! How can I help you today?",
      "response_time_ms": 1234.56,
      "cache_hit": false,
      "llm_tokens": 0,
      "tts_used": true,
      "error": null
    },
    ...
  ],
  "topics": [],
  "rating": null,
  "notes": "Normal conversation end"
}
```

---

## 🔍 세션 후 검증

### 1. 로그 파일 확인
```bash
# 세션 로그 목록
ls logs/phase7/sessions/

# 출력 예시:
# session_abc12345.json

# 로그 내용 확인 (첫 100줄)
cat logs/phase7/sessions/session_abc12345.json | head -100
```

### 2. 로그 내용 검증
다음 항목들이 포함되어야 합니다:
- ✅ `session_id`: 고유 ID
- ✅ `start_time`, `end_time`: ISO 8601 타임스탬프
- ✅ `metrics.total_turns`: Turn 수
- ✅ `metrics.cache_hit_rate`: 캐시 적중률 (%)
- ✅ `turns[]`: 각 Turn 데이터 배열

### 3. 데이터 분석 실행
```bash
# Phase 7 데이터 분석
python tools/analyze_phase7_data.py

# 예상 출력:
# ==========================================
# Phase 7 Data Analysis
# ==========================================
#
# Overall Statistics:
#   Total Sessions: 1
#   Total Turns: 5
#   Date Range: 2025-10-28 to 2025-10-28
#
# Cache Performance:
#   Cache Hit Rate: 20.0%
#   Cache Hits: 1
#   Cache Misses: 4
#
# Response Time:
#   Average: 863.5ms
#   Median: 890ms
#   P95: 1234ms
#   P99: 1234ms
# ...
```

### 4. 대시보드 생성
```bash
# HTML + Markdown 대시보드 생성
python tools/generate_dashboard.py

# 생성된 파일:
# reports/PHASE_7_DASHBOARD_20251028_113200.html
# reports/PHASE_7_DASHBOARD_20251028_113200.md

# 브라우저에서 열기
start reports/PHASE_7_DASHBOARD_20251028_113200.html
```

---

## ⚠️ 문제 해결

### 문제 1: 마이크 인식 안 됨
**증상**: "No clear input detected" 반복
**해결**:
1. 마이크 볼륨 확인
2. Windows 설정 → 소리 → 입력 장치 선택
3. 마이크 테스트 (말하면서 레벨 확인)

### 문제 2: 음성 출력 안 됨
**증상**: TTS 오류 또는 무음
**해결**:
1. 스피커 연결 확인
2. 볼륨 설정 확인
3. pyttsx3 재설치: `pip install --upgrade pyttsx3`

### 문제 3: "Hey Sena" 인식 안 됨
**증상**: 웨이크 워드 반응 없음
**해결**:
1. 명확한 발음: "헤이 세나" 또는 "세나야"
2. 마이크와 거리 조절 (30-50cm)
3. 배경 소음 제거

### 문제 4: Gemini API 오류
**증상**: "API key not found" 또는 "Invalid API key"
**해결**:
1. `.env` 파일 확인:
   ```
   GEMINI_API_KEY=your_actual_key_here
   ```
2. API 키 유효성 확인
3. 네트워크 연결 확인

### 문제 5: 로그 파일 생성 안 됨
**증상**: `logs/phase7/sessions/` 디렉토리에 파일 없음
**해결**:
1. 디렉토리 권한 확인
2. 세션이 정상 종료되었는지 확인 ("그만" 명령)
3. 콘솔 출력에서 에러 메시지 확인

---

## 📈 성공 기준

첫 세션이 성공적이려면:

- ✅ **세션 완료**: 시작부터 종료까지 오류 없이 진행
- ✅ **로그 생성**: JSON 파일이 `logs/phase7/sessions/`에 생성
- ✅ **Turn 수**: 최소 3개 이상의 Turn 기록
- ✅ **응답 시간**: 평균 2초 이하
- ✅ **캐시 동작**: 반복 질문 시 캐시 히트 확인 (선택)

---

## 🎓 첫 세션 이후 할 일

### 1. 즉시 실행
```bash
# 로그 확인
cat logs/phase7/sessions/session_*.json

# 분석 실행
python tools/analyze_phase7_data.py

# 대시보드 생성
python tools/generate_dashboard.py
```

### 2. 다음 세션 계획
**목표**: Day 2-3까지 총 10회 세션 완료

**권장 시나리오**:
- 세션 2-3: 일상 대화 (날씨, 시간, 일정)
- 세션 4-5: 기술 질문 (프로그래밍, 과학)
- 세션 6-7: 창의적 질문 (이야기, 농담)
- 세션 8-9: 캐시 테스트 (반복 질문)
- 세션 10: 종합 테스트

### 3. 데이터 검토
첫 세션 후 다음을 확인:
- 응답 품질: LLM 답변이 적절한가?
- 응답 속도: 사용자 경험이 만족스러운가?
- 캐시 효과: 반복 질문 시 속도 향상이 있는가?
- 오류 발생: 예상치 못한 문제가 있는가?

---

## 🎯 Phase 7 로드맵 (참고)

```
Week 1 (2025-10-28 ~ 2025-11-03)
├── Day 1-2: LLM_Unified PR 완결 ✅
├── Day 2: 첫 세션 ← 현재 단계
├── Day 2-3: 10회 세션 목표
├── Day 4-5: 60회 세션 달성
├── Day 6: 데이터 분석 및 최적화
└── Day 7: 최종 보고서
```

**현재 진행도**: Week 1 Day 2 (40%)

---

## 📞 도움이 필요하면

- **로그 확인**: `logs/phase7/sessions/` 디렉토리
- **에러 메시지**: 콘솔 출력 캡처
- **분석 도구**: `tools/analyze_phase7_data.py`
- **대시보드**: `reports/PHASE_7_DASHBOARD_*.html`

---

**준비 완료!** 이제 첫 음성 세션을 시작하세요! 🎤✨

**명령어 요약**:
```bash
cd D:/nas_backup/fdo_agi_repo
python hey_sena_v4.1_logged.py
```

**세션 후**:
```bash
python tools/analyze_phase7_data.py
python tools/generate_dashboard.py
```

---

**"첫 세션이 가장 중요합니다. 천천히, 명확하게!"** 🚀
