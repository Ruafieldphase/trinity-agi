# Latency Optimization Design (3-Judge Parallel Execution)

## 🎯 목표

**Binoche 3-Judge System의 순차 실행을 병렬화하여 응답 속도 3배 개선**

---

## 📊 현재 병목 분석

### 병목 지점: `binoche_ensemble.py::get_ensemble_decision()`

```python
# 현재: 순차 실행 (SLOW)
for judge_name in ["logic", "emotion", "rhythm"]:
    decision, confidence = get_judge_decision(...)  # 각 2.3s
    judges[judge_name] = {"decision": decision, "confidence": confidence}

# Total: 2.3s × 3 = 6.9s
```

### 문제점

1. **독립적인 작업이 순차 실행됨** - Logic, Emotion, Rhythm 판사는 서로 의존성 없음
2. **I/O 대기 시간 낭비** - 각 판사의 계산이 끝날 때까지 대기
3. **사용자 체감 레이턴시 증가** - 6.9초는 실시간 대화형 시스템에서 너무 느림

### 예상 개선 효과

- **Before**: 6.9s (순차)
- **After**: 2.3s (병렬) ← **3배 개선** 🚀
- **사용자 대기 시간**: 4.6s 단축

---

## 🏗️ 병렬화 설계

### 1. Asyncio 기반 병렬 실행

```python
import asyncio
from typing import Dict, Tuple

async def get_judge_decision_async(
    judge_name: str,
    bqi_coord: Dict,
    quality: float,
    bqi_decision: str,
    bqi_confidence: float
) -> Tuple[str, float]:
    """Async version of get_judge_decision (non-blocking)."""
    # 동일한 로직, 하지만 async로 래핑
    # CPU-bound 작업이지만 asyncio.to_thread() 사용 가능
    return await asyncio.to_thread(
        get_judge_decision,
        judge_name, bqi_coord, quality, bqi_decision, bqi_confidence
    )

async def get_ensemble_decision_async(
    bqi_coord: Dict,
    quality: float,
    bqi_decision: str,
    bqi_confidence: float
) -> Tuple[str, float, str, Dict]:
    """Parallel 3-Judge evaluation with asyncio.gather()."""
    
    # 병렬 실행 (동시에 3개 판사 실행)
    tasks = [
        get_judge_decision_async("logic", bqi_coord, quality, bqi_decision, bqi_confidence),
        get_judge_decision_async("emotion", bqi_coord, quality, bqi_decision, bqi_confidence),
        get_judge_decision_async("rhythm", bqi_coord, quality, bqi_decision, bqi_confidence)
    ]
    
    # 모든 판사가 끝날 때까지 대기 (병렬)
    results = await asyncio.gather(*tasks)
    
    # 결과 조합
    judges = {
        "logic": {"decision": results[0][0], "confidence": results[0][1]},
        "emotion": {"decision": results[1][0], "confidence": results[1][1]},
        "rhythm": {"decision": results[2][0], "confidence": results[2][1]}
    }
    
    # 기존 weighted voting 로직 재사용
    ...
```

### 2. 호환성 유지 (Sync Wrapper)

```python
def get_ensemble_decision(
    bqi_coord: Dict,
    quality: float,
    bqi_decision: str,
    bqi_confidence: float
) -> Tuple[str, float, str, Dict]:
    """Sync wrapper for backward compatibility."""
    return asyncio.run(
        get_ensemble_decision_async(bqi_coord, quality, bqi_decision, bqi_confidence)
    )
```

---

## 🛠️ 구현 계획

### Phase 1: Async 래퍼 구현 (30분)

1. `get_judge_decision_async()` 작성
2. `get_ensemble_decision_async()` 작성
3. Sync wrapper 유지

### Phase 2: 테스트 및 검증 (45분)

1. 단위 테스트 작성
   - 순차 vs 병렬 결과 동일성 검증
   - 성능 벤치마크 (before/after)
2. 통합 테스트
   - Binoche recommender 통합
   - End-to-end 시나리오

### Phase 3: 프로덕션 배포 (15분)

1. 기존 코드 대체
2. 모니터링 설정
3. 롤백 계획 준비

---

## 📈 예상 성과

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| 응답 시간 | 6.9s | 2.3s | **3x faster** 🚀 |
| CPU 사용률 | 33% (1/3 코어) | 100% (3 코어) | +67% (효율↑) |
| 사용자 대기 | 6.9s | 2.3s | **-4.6s** 😊 |

---

## ⚠️ 리스크 및 대응

### 리스크 1: GIL (Global Interpreter Lock)

- **문제**: Python GIL로 인해 CPU-bound 작업은 병렬화 효과 제한
- **대응**: `asyncio.to_thread()` 사용 (스레드 풀 활용)
- **결과**: I/O 대기 시간 단축 효과는 유지

### 리스크 2: 메모리 사용량 증가

- **문제**: 3개 판사 동시 실행 시 메모리 3배 사용
- **대응**: 판사 로직은 가벼움 (< 1MB/judge), 무시 가능
- **모니터링**: `psutil`로 메모리 사용량 추적

### 리스크 3: 에러 핸들링 복잡도

- **문제**: 하나의 판사 실패 시 전체 실패 가능
- **대응**: `asyncio.gather(return_exceptions=True)` 사용
- **Fallback**: 에러 발생 시 순차 실행으로 폴백

---

## 🎁 추가 이점

1. **코드 구조 개선** - 명확한 async/await 패턴
2. **확장성** - 추가 판사 (4th, 5th) 추가 시 자동 병렬화
3. **디버깅 용이성** - 각 판사의 실행 시간 개별 추적

---

## 📝 다음 단계

1. ✅ 병목 지점 식별 완료
2. ✅ 설계 문서 작성 완료
3. ⏳ Async 구현 시작
4. ⏳ 테스트 및 검증
5. ⏳ 프로덕션 배포

---

**예상 완료 시간**: 1.5시간  
**우선순위**: 🔥 High (사용자 경험 직접 개선)
