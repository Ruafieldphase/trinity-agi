# ion-mentoring LLM 기반 요약 Quick Start Guide

**작성자**: 세나 (Sena)
**날짜**: 2025-10-26
**대상**: 루빛 (Lubit)

---

## TL;DR

```python
# 실시간 대화 중: 규칙 기반 (빠름, <1ms)
from persona_system.utils.summary_utils import update_running_summary
summary = update_running_summary(None, messages, max_bullets=6, max_chars=600)

# 세션 종료 후: LLM 기반 (고품질, ~3초)
from persona_system.utils.summary_llm import summarize_with_llm
summary = await summarize_with_llm(messages, max_bullets=8, max_chars=800)
```

---

## 1. 환경 설정

### 1.1 필수 패키지 설치
```bash
# Gemini API 클라이언트
pip install google-genai

# Redis (이미 설치됨)
pip install redis
```

### 1.2 환경 변수 설정
```bash
# Windows PowerShell
$env:GOOGLE_API_KEY = "your-api-key-here"

# Windows CMD
set GOOGLE_API_KEY=your-api-key-here

# Linux/Mac
export GOOGLE_API_KEY=your-api-key-here
```

### 1.3 Redis 서버 실행
```bash
# Docker로 실행 (이미 실행 중)
docker run -d --name ion-redis -p 6379:6379 redis:7-alpine

# 확인
docker ps | findstr ion-redis
```

---

## 2. 사용 방법

### 2.1 규칙 기반 요약 (현재 사용 중)

**장점**: 매우 빠름 (<1ms), 비용 없음, 안정적
**단점**: 품질 낮음, 단순 추출

```python
from persona_system.utils.summary_utils import update_running_summary

# 실시간 대화 요약
messages = [
    {"role": "user", "content": "안녕하세요!"},
    {"role": "assistant", "content": "안녕하세요! 무엇을 도와드릴까요?"},
    # ...
]

summary = update_running_summary(
    running_summary=None,  # 기존 요약 (없으면 None)
    new_messages=messages,
    max_bullets=6,         # 최대 불릿 수
    max_chars=600,         # 최대 글자 수
    per_line_max=120       # 줄당 최대 길이
)

print(summary)
# 출력:
# - U: 안녕하세요!
# - A: 안녕하세요! 무엇을 도와드릴까요?
```

---

### 2.2 LLM 기반 요약 (신규 기능)

**장점**: 고품질, 의미론적 압축, 자연스러운 문장
**단점**: 느림 (~3초), API 비용 (미미)

```python
from persona_system.utils.summary_llm import summarize_with_llm

# 세션 종료 후 백그라운드 요약
messages = [
    {"role": "user", "content": "Vertex AI 설치 방법이 궁금합니다."},
    {"role": "assistant", "content": "pip install google-cloud-aiplatform으로 설치할 수 있습니다."},
    # ... 더 많은 메시지
]

summary = summarize_with_llm(
    messages=messages,
    max_bullets=8,         # 더 상세한 요약 가능
    max_chars=800,
    temperature=0.3        # 낮을수록 일관적
)

print(summary)
# 출력:
# - Vertex AI SDK는 pip install 명령어로 설치합니다.
# - Python 3.11 이상 버전이 필요합니다.
# - 설치 후 기본 연결 테스트를 권장합니다.
```

---

### 2.3 하이브리드 접근법 (권장)

```python
from persona_system.utils.summary_utils import update_running_summary
from persona_system.utils.summary_llm import summarize_with_llm
import asyncio

class ConversationManager:
    def __init__(self):
        self.messages = []

    def on_new_message(self, role: str, content: str):
        """실시간 메시지 처리"""
        self.messages.append({"role": role, "content": content})

        # 규칙 기반 실시간 요약
        realtime_summary = update_running_summary(
            running_summary=None,
            new_messages=self.messages[-5:],  # 최근 5개만
            max_bullets=6,
            max_chars=600
        )

        # UI에 실시간 요약 표시
        self.display_summary(realtime_summary)

    async def on_session_end(self, session_id: str):
        """세션 종료 시 고품질 요약 생성"""
        # LLM 기반 백그라운드 요약
        session_summary = await summarize_with_llm(
            messages=self.messages,
            max_bullets=8,
            max_chars=800,
            temperature=0.3
        )

        # 장기 기억에 저장
        await self.save_to_long_term_memory(session_id, session_summary)

        return session_summary
```


### 2.4 장기 기억 + 임베딩 검색

백그라운드 LLM 요약이 완료되면 `SessionSummaryStorage`가 JSONL과 임베딩 벡터를 동시에 보존합니다.

- 저장 루트: `ion-mentoring/data/session_summaries/` (일자별 JSONL + `embeddings/` 디렉터리)
- 인덱스 파일: `index.json` (세션 메타데이터 + 임베딩 경로)
- 파이프라인 헬퍼: `OptimizedPersonaPipeline.search_session_memory()` / `list_recent_session_memory()`

```python
from persona_system.utils.session_summary_storage import get_session_storage

storage = get_session_storage()

# 수동 저장 (임베딩은 Vertex AI → 해시 순으로 생성)
storage.save(
    session_id="demo-001",
    user_id="planner",
    summary="Vertex AI 마이그레이션 플랜 요약...",
    summary_type="llm",
    message_count=12,
)

# 의미 기반 검색
results = storage.search(
    query_text="마이그레이션 계획",
    min_similarity=0.15,
    limit=5,
    include_embeddings=True,
)

for item in results:
    print(item.session_id, item.metadata.get("similarity"))
```

> **모니터링 팁**  
> `scripts/generate_monitoring_report.ps1` 실행 시 `SessionSummaries` 블록이 JSON/HTML 대시보드에 포함되어
> 총 세션 수, 임베딩 커버리지, 최근 저장본 미리보기를 한눈에 파악할 수 있습니다.

---

## 3. 테스트 실행

### 3.1 캐시 통합 테스트
```bash
cd D:\nas_backup\LLM_Unified\ion-mentoring
python monitor/test_cache_integration.py
```

**예상 출력**:
```
[OK] Basic operations work!
[OK] Redis L2 cache is working!
[OK] Cache hit is working!
[RESULT] Speedup: 229.6x faster
[SUCCESS] All tests passed!
```

---

### 3.2 LLM vs 규칙 기반 비교 테스트
```bash
python monitor/test_llm_summary.py
```

**예상 출력**:
```
[Time Comparison]:
  Rule-Based: 0.04ms
  LLM-Based:  3166.62ms
  LLM is 83533.1x slower (expected)

[Recommendation]:
  [WARNING] LLM response time is slow (>1s)
  [RECOMMEND] Consider hybrid approach
```

---

### 3.3 대시보드 실행
```powershell
# PowerShell
.\monitor\start_dashboard.ps1

# 또는 직접 실행
python monitor/cache_dashboard.py
```

**접속**: http://localhost:5001

**대시보드 기능**:
- 실시간 캐시 히트율 모니터링
- L1/L2 캐시 통계
- Redis 상태 확인
- 성능 그래프 (Chart.js)

---

## 4. 성능 비교 요약

| 항목 | 규칙 기반 | LLM 기반 | 차이 |
|------|-----------|----------|------|
| 응답 시간 | **0.04ms** | 3,166ms | 83,533x |
| 품질 | 낮음 | **높음** | LLM 우수 |
| 비용 | **무료** | ~$0.05/1000요약 | 무시 가능 |
| 안정성 | **매우 높음** | 네트워크 의존 | 규칙 우수 |
| 사용 사례 | **실시간 대화** | **세션 요약** | 각각 최적 |

---

## 5. 자주 묻는 질문 (FAQ)

### Q1: LLM을 실시간 대화에 사용할 수 없나요?
**A**: 3초 응답 시간은 실시간 대화에 부적합합니다. 캐시를 사용해도 436ms로 50ms 목표를 초과합니다.

### Q2: API 비용은 얼마나 나올까요?
**A**: Gemini 2.0 Flash 기준:
- 요약 1회: $0.000053
- 100 세션/일 × 30일 = **$0.16/월**
- 결론: 무시할 수 있는 수준

### Q3: LLM 품질이 정말 더 좋나요?
**A**: 네! 테스트 결과:
- 28% 더 간결 (371자 → 267자)
- 의미론적 압축 (Q&A 형태 → 자연스러운 문장)
- 맥락 통합 (전체 흐름 이해)

### Q4: 규칙 기반 요약을 완전히 대체해야 하나요?
**A**: 아니요! 하이브리드 접근법 권장:
- 실시간: 규칙 기반 (<1ms)
- 백그라운드: LLM 기반 (~3초)

### Q5: Redis가 없으면 어떻게 되나요?
**A**: L1 캐시만 사용 (문제없음):
- L1: 로컬 메모리 캐시 (빠름)
- L2: Redis (선택사항, 분산 캐싱)

---

## 6. 트러블슈팅

### 문제 1: GOOGLE_API_KEY not set
```python
# 증상
WARNING - GOOGLE_API_KEY not set. LLM summarization unavailable.

# 해결
import os
os.environ['GOOGLE_API_KEY'] = 'your-api-key-here'
```

### 문제 2: Redis connection refused
```python
# 증상
ConnectionError: Error 10061 connecting to localhost:6379

# 해결
docker run -d --name ion-redis -p 6379:6379 redis:7-alpine
```

### 문제 3: LLM 응답이 너무 느림
```python
# 증상
LLM response time: 10,000ms

# 원인: 네트워크 지연, API 서버 부하

# 해결: 타임아웃 설정
from persona_system.utils.summary_llm import LLMSummarizer
summarizer = LLMSummarizer()
summarizer.timeout = 30  # 30초 타임아웃
```

### 문제 4: 한글 인코딩 깨짐
```python
# 증상
UnicodeEncodeError: 'cp949' codec can't encode character

# 해결: UTF-8 설정
import sys
sys.stdout.reconfigure(encoding='utf-8')
```

---

## 7. 다음 단계

### Phase 1: 프로토타입 검증 (1주)
- [x] LLM 기반 요약 구현
- [x] 규칙 기반과 비교 테스트
- [x] 성능 및 품질 분석

### Phase 2: 백그라운드 작업 구현 (1-2주)
- [ ] 비동기 세션 요약 생성
- [ ] 작업 큐 시스템 구축
- [ ] 재시도 로직 추가

### Phase 3: A/B 테스트 (2-3주)
- [ ] 사용자 피드백 수집
- [ ] 품질 점수 측정
- [ ] 최적 파라미터 찾기

### Phase 4: 프로덕션 배포 (4일)
- [x] 장기 기억 저장소 + 임베딩 탐색 통합
- [ ] 모니터링 자동화 보강
- [ ] 비용 최적화



---

## 8. 연락처

**문의**: 세나 (Sena)
**이메일**: sena@ion-mentoring
**문서 위치**: D:\nas_backup\outputs\ion_mentoring_LLM요약_최종_분석_20251026.md

**참고 자료**:
- Gemini API Docs: https://ai.google.dev/docs
- Redis Docs: https://redis.io/docs
- ion-mentoring Cache Dashboard: http://localhost:5001

---

**마지막 업데이트**: 2025-10-26
**버전**: 1.0.0
