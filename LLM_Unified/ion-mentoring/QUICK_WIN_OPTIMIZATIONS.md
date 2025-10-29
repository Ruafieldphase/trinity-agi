# 빠른 성능 개선 (Quick Win Optimizations)

배포 후 즉시 적용 가능한 고효율 최적화 목록 (1-2주 내 구현)

**목표**: 응답 시간 5-15% 단축, 운영 부하 50% 감소
**복잡도**: LOW-MEDIUM (각 1-3일 소요)
**위험도**: LOW (기존 기능 변경 없음)

---

## 🎯 Quick Win 최적화 순위

### Priority 1: 응답 캐싱 (3일, 10% 개선)

#### 현재 상태
- 동일 입력: 매번 전체 처리
- Vertex AI 호출: 항상 새로 수행
- 반복 패턴 없음

#### 개선 후
- 동일 입력: 캐시에서 즉시 반환
- 반복 요청 감소: 예상 30-50%
- 메모리 추가: 약 50MB

#### 구현 코드

```python
# app/cache_manager.py (신규)
import hashlib
import time
from typing import Optional, Dict, Any
from functools import wraps

class SimpleCache:
    """응답 캐싱 매니저"""

    def __init__(self, ttl: int = 1800, max_size: int = 500):
        self.cache = {}
        self.ttl = ttl
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def _get_key(self, message: str, persona_filters: Optional[Dict] = None) -> str:
        """캐시 키 생성"""
        cache_data = f"{message}:{str(persona_filters)}"
        return hashlib.md5(cache_data.encode()).hexdigest()

    def get(self, message: str, persona_filters: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """캐시에서 조회"""
        key = self._get_key(message, persona_filters)

        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                self.hits += 1
                return value
            else:
                del self.cache[key]

        self.misses += 1
        return None

    def set(self, message: str, response: Dict[str, Any], persona_filters: Optional[Dict] = None) -> None:
        """캐시에 저장"""
        key = self._get_key(message, persona_filters)

        # 용량 초과 시 가장 오래된 항목 제거
        if len(self.cache) >= self.max_size:
            oldest_key = min(
                self.cache.keys(),
                key=lambda k: self.cache[k][1]
            )
            del self.cache[oldest_key]

        self.cache[key] = (response, time.time())

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "cache_size": len(self.cache),
            "memory_mb": len(self.cache) * 2,  # 대략적 추정
        }

    def clear(self) -> None:
        """캐시 초기화"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

# app/main.py 수정
from app.cache_manager import SimpleCache

cache_manager = SimpleCache(ttl=1800, max_size=500)

@app.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """캐시를 활용한 채팅 엔드포인트"""

    # Step 1: 캐시 확인
    cached_response = cache_manager.get(request.message)
    if cached_response:
        logger.info(f"Cache hit for message: {request.message[:50]}")
        return ChatResponse(**cached_response)

    # Step 2: 캐시 미스 - 전체 처리
    logger.info(f"Cache miss, processing: {request.message[:50]}")

    response = await persona_pipeline.process(request.message)
    response_dict = response.dict()

    # Step 3: 캐시에 저장
    cache_manager.set(request.message, response_dict)

    return ChatResponse(**response_dict)

# 캐시 통계 엔드포인트 (모니터링용)
@app.get("/metrics/cache")
async def get_cache_stats():
    """캐시 통계 조회"""
    return cache_manager.get_stats()
```

#### 배포 전략
1. **개발**: 로컬에서 테스트 (1일)
2. **스테이징**: 스테이징 환경 배포 (1일)
3. **프로덕션**: Feature flag로 점진적 롤아웃
   - Day 1: 10% 트래픽
   - Day 2: 50% 트래픽
   - Day 3: 100% 트래픽

---

### Priority 2: 로깅 최적화 (배치화, 3일, 15% 개선)

#### 현재 상태
- 모든 로그: 즉시 전송
- GCP 호출: 요청당 10+ 회
- 네트워크 대역폭: 높음

#### 개선 후
- 로그: 버퍼링 후 배치 전송
- GCP 호출: 요청당 1회 (배치)
- 네트워크 대역폭: 90% 감소

#### 구현 코드

```python
# app/batch_logger.py (신규)
import queue
import threading
import time
from typing import Dict, Any, List
from datetime import datetime

class BatchedGoogleCloudLogger:
    """배치 로깅 매니저"""

    def __init__(self, batch_size: int = 50, flush_interval: int = 5):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.buffer = []
        self.lock = threading.Lock()

        # 백그라운드 플러시 스레드
        self.flush_thread = threading.Thread(
            target=self._periodic_flush,
            daemon=True
        )
        self.flush_thread.start()

        self.flushed_count = 0
        self.batches_count = 0

    def add_log(self, log_entry: Dict[str, Any]) -> None:
        """로그 추가"""
        with self.lock:
            self.buffer.append({
                **log_entry,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # 배치 크기 도달 시 플러시
            if len(self.buffer) >= self.batch_size:
                self._flush_batch()

    def _flush_batch(self) -> None:
        """배치 플러시"""
        if not self.buffer:
            return

        batch = self.buffer.copy()
        self.buffer.clear()

        # 백그라운드에서 전송
        threading.Thread(
            target=self._send_batch,
            args=(batch,),
            daemon=True
        ).start()

    def _send_batch(self, batch: List[Dict[str, Any]]) -> None:
        """배치 전송"""
        try:
            # Google Cloud Logging에 배치 전송
            from google.cloud import logging as cloud_logging

            client = cloud_logging.Client()
            logger = client.logger("ion-api")

            for entry in batch:
                logger.log_struct(entry)

            self.flushed_count += len(batch)
            self.batches_count += 1

        except Exception as e:
            print(f"Failed to send batch: {e}")

    def _periodic_flush(self) -> None:
        """정기적 플러시"""
        while True:
            time.sleep(self.flush_interval)
            with self.lock:
                if self.buffer:
                    self._flush_batch()

    def get_stats(self) -> Dict[str, Any]:
        """통계"""
        return {
            "total_flushed": self.flushed_count,
            "total_batches": self.batches_count,
            "current_buffer_size": len(self.buffer),
        }

# app/main.py 수정
batch_logger = BatchedGoogleCloudLogger(batch_size=50, flush_interval=5)

# 기존 로깅 대신 배치 로깅 사용
@app.middleware("http")
async def log_request(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    batch_logger.add_log({
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "process_time_ms": process_time * 1000,
    })

    response.headers["X-Process-Time"] = str(process_time)
    return response
```

#### 기대 효과
- 로깅 오버헤드: 50% 감소
- GCP 호출: 90% 감소
- 메모리: +20MB

---

### Priority 3: 데이터베이스 쿼리 최적화 (2일, 8% 개선)

#### 현재 상태
- 쿼리: 최적화 없음
- N+1 문제: 가능성 높음
- 인덱스: 기본만 설정

#### 개선 후
- 쿼리: 조인 최적화
- 쿼리 캐싱: 자주 사용하는 쿼리
- 인덱스: 성능 최적화

#### 구현 코드

```python
# 프로덕션 환경에서 (필요시)
# 쿼리 실행 계획 분석

# Cloud SQL - 느린 쿼리 로그 활성화
"""
ALTER DATABASE {database_name} SET log_min_duration_statement = 1000;
-- 1초 이상 걸리는 쿼리만 로깅
"""

# 인덱스 추가
"""
CREATE INDEX idx_persona_response_time ON responses (persona_id, created_at);
CREATE INDEX idx_session_lookup ON memory_coordinates (session_id);
"""

# SQLAlchemy 쿼리 최적화
from sqlalchemy.orm import joinedload

# 나쁜 예: N+1 쿼리
responses = db.query(Response).all()
for response in responses:
    print(response.persona.name)  # N+1 쿼리 발생

# 좋은 예: eager loading
responses = db.query(Response).options(
    joinedload(Response.persona)
).all()
```

---

## 📊 Performance Regression 검사

### Week 1-2: 모니터링

```python
# 매일 아침 성능 비교 (자동화 가능)
baseline = {
    "p95_latency": 1800,  # ms
    "error_rate": 0.01,   # 1%
    "memory_mb": 280,
}

current = {
    "p95_latency": 1820,  # ms
    "error_rate": 0.009,  # 0.9%
    "memory_mb": 290,
}

# 확인 항목
assert current["p95_latency"] < baseline["p95_latency"] * 1.1  # 110% 이상 증가 금지
assert current["error_rate"] < baseline["error_rate"] * 1.5    # 150% 이상 증가 금지
assert current["memory_mb"] < baseline["memory_mb"] * 1.2      # 120% 이상 증가 금지
```

---

## 🎯 적용 일정

### Week 1 (배포 후 1주일)

**Day 1-3: 응답 캐싱**
```
Day 1: 개발 및 단위 테스트
Day 2: 통합 테스트 및 스테이징 배포
Day 3: 프로덕션 배포 (10% → 50% → 100%)
```

**Day 4-5: 배치 로깅**
```
Day 4: 개발 및 테스트
Day 5: 배포
```

### Week 2

**Day 1-2: 데이터베이스 최적화**
```
Day 1: 쿼리 분석 및 인덱스 계획
Day 2: 배포 및 검증
```

**Day 3-5: 통합 테스트 및 모니터링**
```
성능 메트릭 검증
```

---

## 📈 예상 효과

### 개선 전후 비교

```
메트릭           개선 전    개선 후    개선도
─────────────────────────────────────────
P50 응답 시간    0.8s      0.75s      6% ↓
P95 응답 시간    1.8s      1.55s      14% ↓
P99 응답 시간    4.2s      3.65s      13% ↓
메모리 사용      280MB     310MB      11% ↑
GCP 호출        1,000/h   100/h      90% ↓
로그 오버헤드    10ms      5ms        50% ↓

종합 개선: 약 12% 성능 향상
```

### 비즈니스 영향

```
응답 시간 개선:
  - 사용자 만족도 ↑ 5-10%
  - 포기율 ↓ 2-3%
  - 처리량 ↑ 10%

비용 절감:
  - GCP 호출 비용 ↓ 90%
  - 인스턴스 개수 ↓ 10-20%
  - 네트워크 비용 ↓ 50%
```

---

## 🛡️ 롤백 계획

### 캐싱 롤백
```python
# Feature flag로 즉시 비활성화 가능
ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true") == "true"

if ENABLE_CACHE:
    response = cache_manager.get(message)
    if response:
        return response
```

### 배치 로깅 롤백
```python
# 동기식 로깅으로 복구
if USE_BATCH_LOGGING:
    batch_logger.add_log(entry)
else:
    cloud_logging_client.log_struct(entry)  # 동기식
```

---

## ✅ 최종 체크리스트

- [ ] 캐싱 구현 완료
- [ ] 배치 로깅 구현 완료
- [ ] DB 최적화 완료
- [ ] 단위 테스트 통과
- [ ] 통합 테스트 통과
- [ ] 스테이징 배포 성공
- [ ] 프로덕션 배포 성공
- [ ] 성능 메트릭 확인
- [ ] Regression 없음 확인
- [ ] 팀 교육 완료

---

**빠른 개선을 통한 프로덕션 성능 최적화** ✅
