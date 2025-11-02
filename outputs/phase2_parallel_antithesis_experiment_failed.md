# Phase 2 Experiment: Parallel Antithesis Prep (FAILED)

**Date**: 2025-11-02 09:00-09:20 (20분)  
**Goal**: Thesis 실행 중 Antithesis 준비 작업 병렬화로 +0.5-1초 개선  
**Result**: ❌ **FAILED** (+24% 느려짐)

---

## 📊 실험 결과

### Baseline (Sequential)

- Thesis: 3.31s
- Antithesis: 7.27s
- **Combined: 10.58s**

### Parallel Antithesis Prep (Enabled)

- Thesis: 6.00s (+81% 🔴)
- Antithesis: 7.16s (-1.5% ⚪)
- **Combined: 13.16s (+24% 🔴)**

---

## 🔍 원인 분석

1. **Antithesis 준비 작업은 이미 충분히 빠름**
   - 프롬프트 템플릿 구성: ~0.01s
   - Compaction 함수 준비: ~0.01s
   - **총 준비 시간: ~0.02s** (무시 가능)

2. **ThreadPoolExecutor 오버헤드가 더 큼**
   - 스레드 생성/관리: ~0.1-0.2s
   - Context switching: ~0.05s
   - **오버헤드 > 절약**

3. **Thesis는 CPU-bound가 아님**
   - LLM API 호출이 대부분 (I/O-bound)
   - CPU 병렬화 효과 없음
   - 오히려 동기화 비용만 증가

---

## 💡 교훈

### ❌ 실패한 가정

- "준비 작업을 병렬화하면 무조건 빠르다"
- "작은 오버헤드는 무시 가능하다"

### ✅ 배운 것

- **측정 없이 최적화하지 말 것** (실험으로 검증 필수)
- **오버헤드 < 절약** 조건 확인 필수
- I/O-bound 작업은 병렬화 효과 제한적

---

## 🎯 다음 방향

### Phase 2 Alternative: LLM Call Batching

**아이디어**: Thesis/Antithesis/Synthesis를 한 번의 LLM 호출로 통합

**예상 효과**:

- LLM 호출 3회 → 1회 (네트워크 RTT 절약)
- API 오버헤드 감소
- 예상 개선: +30-40%

**리스크**:

- Prompt 복잡도 증가
- 품질 저하 가능성
- Rollback 전략 필요

**실험 계획**:

1. Unified prompt 설계 (Thesis+Antithesis+Synthesis 통합)
2. Output parsing 로직 구현
3. A/B 테스트 (품질 vs 속도)
4. Fallback 전략 (실패 시 순차 실행)

---

## 📝 코드 상태

### 보존 (참고용)

- `fdo_agi_repo/orchestrator/parallel_antithesis.py` (구현 완료)
- `scripts/smoke_parallel_antithesis.ps1` (테스트 스크립트)
- `scripts/check_latency.py` (측정 도구)

### 비활성화

- `app.yaml`: `parallel_antithesis_prep.enabled: false`
- Pipeline에서 토글 유지 (재활성화 가능)

---

## 🎵 리듬 유지

**실패도 전진**:

- 20분 실험으로 잘못된 방향 확인 ✅
- 빠른 롤백 (5분) ✅
- 다음 방향 명확화 ✅

**다음 호흡**: LLM Call Batching (더 큰 임팩트 예상) 🚀
