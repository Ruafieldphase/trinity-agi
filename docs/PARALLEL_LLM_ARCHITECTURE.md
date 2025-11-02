# LLM 병렬 호출 아키텍처 설계 (v1.0)

날짜: 2025-11-02
목표: Thesis/Antithesis 병렬 실행으로 레이턴시 26-40초 → 15-20초 단축

## 1. 현재 상태 분석

### 순차 실행 타임라인

```
Thesis ─────────►│4.5s
                 Antithesis ─────────────────►│10.8s
                                              Synthesis ──────────────►│14.2s
Total: 29.5s
```

### 병렬 실행 목표

```
Thesis ─────────►│4.5s                         ┐
                 │                              │ 병렬
Antithesis ─────────────────►│10.8s            ┘
                              Synthesis ──────────────►│14.2s
Total: ~18.5s (37% 단축)
```

## 2. 구현 전략

### Phase 1: 안전한 병렬화 (현재 → 3주 내)

**파일**: `fdo_agi_repo/orchestrator/pipeline.py`

**변경 포인트** (라인 195-235):

```python
# 기존 (순차):
out_thesis = run_thesis(...)      # 4.5s
out_anti = run_antithesis(...)    # 10.8s
out_synth = run_synthesis(...)    # 14.2s

# 신규 (병렬):
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    # Thesis/Antithesis 병렬 시작
    thesis_future = executor.submit(run_thesis, task, plan, registry, context_prompt or "")
    anti_future = executor.submit(run_antithesis_standalone, task, plan, registry, context_prompt or "")
    
    # 결과 대기
    out_thesis = thesis_future.result()  # max(4.5s, 10.8s) = 10.8s
    out_anti = anti_future.result()
    
# Synthesis는 기존대로 (thesis + anti 모두 필요)
out_synth = run_synthesis(task, [out_thesis, out_anti], registry, context_prompt or "")
```

### Phase 2: Antithesis 독립 실행 버전 생성

**새 파일**: `fdo_agi_repo/personas/antithesis_standalone.py`

```python
def run_antithesis_standalone(task, plan, registry, conversation_context=""):
    """
    Thesis 결과 없이 실행 가능한 Antithesis 버전
    - 입력: task, plan (thesis 대신)
    - 출력: PersonaOutput (기존과 동일)
    """
    # thesis.summary 대신 task.goal 활용
    # thesis.citations → plan 또는 초기 RAG 호출로 대체
```

**주의사항**:

- Antithesis가 Thesis 결과에 의존하지 않는 경우에만 적용
- 품질 저하 가능성 → A/B 테스트 필요

### Phase 3: Adaptive 병렬화 (6주 내)

**조건부 병렬 실행**:

```python
if task.complexity < 5:  # 단순 태스크
    # 병렬 실행
    parallel_mode = True
else:
    # 순차 실행 (품질 우선)
    parallel_mode = False
```

## 3. 구현 단계

### Week 1-2: 준비 단계

- [ ] Antithesis 의존성 분석 (thesis 결과 사용 여부)
- [ ] `run_antithesis_standalone()` 프로토타입 작성
- [ ] 단위 테스트 작성 (thesis 없이 실행 가능 확인)

### Week 2-3: 병렬화 구현

- [ ] `pipeline.py`에 ThreadPoolExecutor 적용
- [ ] Ledger 이벤트 타이밍 조정 (병렬 실행 반영)
- [ ] 에러 처리 강화 (하나의 persona 실패 시 fallback)

### Week 3-4: 검증 및 최적화

- [ ] A/B 테스트: 순차 vs 병렬 품질 비교
- [ ] 레이턴시 측정: 목표 18초 달성 확인
- [ ] 부하 테스트: 동시 실행 안정성 검증

## 4. 리스크 및 완화 전략

### 리스크 1: 품질 저하

- **원인**: Antithesis가 Thesis 결과 없이 실행 시 맥락 부족
- **완화**:
  1. A/B 테스트로 품질 메트릭 비교 (Evidence Gate 통과율)
  2. 품질 저하 시 순차 실행으로 자동 롤백

### 리스크 2: 동시성 버그

- **원인**: 공유 리소스 (registry, ledger) 동시 접근
- **완화**:
  1. ThreadPoolExecutor 사용 (GIL로 일부 보호)
  2. Ledger 이벤트에 thread_id 추가
  3. 철저한 단위 테스트

### 리스크 3: 복잡도 증가

- **원인**: 병렬/순차 코드 경로 분기
- **완화**:
  1. 단순한 flag 기반 분기 (`parallel_mode`)
  2. 충분한 주석 및 문서화
  3. 레거시 순차 코드는 주석으로 보존

## 5. 측정 지표

### 성공 기준

- **P1 (필수)**: 평균 레이턴시 30.5초 → 20초 이하
- **P2 (중요)**: Evidence Gate 통과율 유지 (현재: 100%)
- **P3 (선택)**: 최대 레이턴시 41초 → 25초 이하

### 모니터링

```python
# Ledger 이벤트 예시
{
    "event": "parallel_execution_start",
    "task_id": "...",
    "mode": "parallel",  # or "sequential"
    "thesis_start_ms": 0,
    "antithesis_start_ms": 0  # 병렬: ~0ms, 순차: ~4500ms
}
```

## 6. 롤아웃 계획

### Stage 1: Canary (1주)

- 전체 태스크의 5% → 병렬 실행
- 레이턴시/품질 메트릭 수집

### Stage 2: Gradual (2주)

- 문제 없으면 25% → 50% → 100%
- 각 단계마다 24시간 모니터링

### Stage 3: Default (3주)

- 병렬 실행이 기본값
- 순차 실행은 fallback 옵션으로 유지

## 7. 다음 액션

### 즉시 (오늘)

1. Antithesis 의존성 코드 리뷰
2. 병렬화 브랜치 생성 (`feature/parallel-llm-calls`)
3. 프로토타입 작성 시작

### 이번 주

1. 단위 테스트 작성
2. pipeline.py 수정 PR 준비
3. 스모크 테스트 실행

### 다음 주

1. A/B 테스트 시작
2. 레이턴시 대시보드 추가
3. 문서 업데이트
