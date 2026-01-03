# Week 2 패키지 리뷰 및 통합 가이드

**작성일**: 2025-10-12
**작성자**: 세나 (Sena)
**목적**: 루빛의 E2 실험 준비를 위한 Week 2 패키지 사전 검토

---

## 📦 Week 2 패키지 개요

### 패키지 목록
```
Week 2 (4개 패키지, 총 75KB):
├─ fdo_agi_repo_W2_rag.zip  (16KB) - RAG 시스템
├─ fdo_agi_repo_W2_eval.zip (20KB) - 평가 시스템 강화
├─ fdo_agi_repo_W2_exec.zip (22KB) - 실행 도구 확장
└─ fdo_agi_repo_W2_web.zip  (17KB) - 웹 검색 통합
```

### 주요 목표
- **E1 문제 해결**: Verifiability 0.10 → 0.60
- **도구 활성화**: RAG, 웹 검색, 코드 실행
- **평가 강화**: 증거 기반 품질 측정

---

## 🔍 W2_RAG: RAG 시스템

### 파일 구조
```
tools/rag/
├─ embed.py       - 임베딩 생성 (512차원 해시 기반)
├─ indexer.py     - 문서 인덱싱
└─ retriever.py   - 유사도 검색
```

### 코드 분석

#### 1. embed.py - 경량 임베딩
```python
DIM = 512  # 데모용 컴팩트 차원

def embed(text: str, dim: int = DIM) -> np.ndarray:
    """
    해시 기반 임베딩 (MD5):
    1. 텍스트 토큰화 (A-Z, 가-힣, 0-9)
    2. 각 토큰을 MD5 해시 → 512차원 버킷
    3. log-TF 가중치 (1 + log(1 + count))
    4. L2 정규화
    """
    vec = np.zeros(dim, dtype=np.float32)
    counts = {}
    for token in tokenize(text):
        counts[token] = counts.get(token, 0) + 1

    for token, count in counts.items():
        bucket = hash(token) % dim
        vec[bucket] += 1.0 + math.log(1.0 + count)

    vec /= np.linalg.norm(vec)  # L2 normalize
    return vec
```

**특징**:
- ✅ **경량**: 외부 모델 불필요 (GPT/BERT 없음)
- ✅ **빠름**: 해시 기반, CPU만으로 동작
- ✅ **한글 지원**: 유니코드 토큰 패턴
- ❌ **의미론적 한계**: 단순 해시, 문맥 이해 없음
- ❌ **저차원**: 512차원 (일반적으로 768~1536)

**E2 적합성**: ⚠️ 데모용으로는 OK, 프로덕션에서는 업그레이드 필요

---

#### 2. retriever.py - 검색 시스템
```python
def rag_query(query: str, top_k: int = 5,
              index_dir: str = "memory/vectorstore"):
    """
    RAG 쿼리:
    1. 쿼리 임베딩 생성
    2. FAISS 또는 코사인 유사도로 top-k 검색
    3. 메타데이터와 함께 반환
    """
    mat, meta, index = _load_index(index_dir)
    qv = embed(query)

    if index is not None:  # FAISS 사용 가능 시
        D, I = index.search(qv, top_k)
    else:  # Fallback: NumPy 코사인 유사도
        I, D = _cosine_topk(mat, qv, top_k)

    hits = [{"id": meta[i]["id"],
             "source": meta[i]["path"],
             "score": float(D[i]),
             "preview": meta[i].get("preview", "")}
            for i in I]

    return {"ok": True, "hits": hits}
```

**특징**:
- ✅ **FAISS 지원**: 선택적 (없으면 NumPy fallback)
- ✅ **메타데이터**: source, preview 포함
- ✅ **간단한 API**: 1줄로 검색 가능
- ⚠️ **재랭킹 없음**: top-k만 반환, 재정렬 미지원

**E2 통합**:
```python
# Thesis 페르소나에서 사용
from tools.rag.retriever import rag_query

results = rag_query("empathic AI coach for writers", top_k=3)
for hit in results["hits"]:
    print(f"Source: {hit['source']}, Score: {hit['score']:.2f}")
    print(f"Preview: {hit['preview']}\n")
```

---

### RAG 인덱싱 (사전 작업)

Week 2 패키지 사용 전 인덱스 생성 필요:

```bash
# 1. 문서 인덱싱
python scripts/index_docs.py \
  --input docs/ \
  --output memory/vectorstore/

# 2. 인덱스 확인
ls memory/vectorstore/
# vectors.npy     - 임베딩 행렬
# meta.json       - 메타데이터 (path, preview)
# faiss.index     - FAISS 인덱스 (선택)
```

**인덱싱 대상**:
- `docs/` 디렉토리의 Markdown 파일
- Week 1 스캐폴드 문서
- 기존 AGI 설계 문서 (Sena, Core)

---

## 🔍 W2_EVAL: 평가 시스템 강화

### 파일 구조
```
orchestrator/
├─ evaluator.py         - 품질 평가 (증거 기반)
└─ self_correction.py   - RUNE 자동 생성
```

### 코드 분석

#### 1. evaluator.py - 증거 기반 평가
```python
def evaluate(outputs: List[PersonaOutput],
             cfg: Dict[str, Any] | None = None) -> EvalReport:
    """
    품질 평가 (4가지 메트릭):
    1. Evidence (45%): 인용 개수, 다양성, 신뢰도
    2. Readability (25%): 단어 수, 문장 수 휴리스틱
    3. Logic (15%): 논리 표지어 존재 여부
    4. Trust (15%): 화이트리스트 도메인 비율

    품질 = weighted_sum - redundancy_penalty
    """
    # 1. Evidence 메트릭
    total_cites, diversity, trust = _evidence_metrics(outputs, whitelist)
    evidence_score = 0.4 + 0.2*min(total, 4) + 0.4*diversity

    # 2. Readability (30-200 단어, 2-8 문장 선호)
    readability = _readability(summaries)

    # 3. Logic hints (논리 표지어)
    logic = _logic_hint(summaries)

    # 4. Trust (화이트리스트 도메인)
    trust_score = sum(1.0 if whitelisted else 0.6) / total_cites

    # 5. Redundancy penalty
    redundancy = _redundancy_penalty(outputs)  # 0~0.3

    # 종합 품질
    quality = (0.45*evidence_score + 0.25*readability
               + 0.15*logic + 0.15*trust_score - redundancy)

    # 증거 OK 조건: >=2 인용, trust >=0.7
    evidence_ok = total_cites >= 2 and trust_score >= 0.7

    return EvalReport(quality=quality, evidence_ok=evidence_ok, ...)
```

**E1 문제 해결**:
- ❌ **E1**: Verifiability 0.10 (1/10 facts checked)
- ✅ **W2**: 증거 기반 평가, 최소 2개 인용 강제
- ✅ **W2**: 화이트리스트로 신뢰도 측정

**개선 포인트**:
- ✅ **Evidence-first**: 45% 가중치 (가장 높음)
- ✅ **Redundancy penalty**: 중복 인용 페널티
- ✅ **Trust score**: 도메인 화이트리스트
- ⚠️ **Logic hints**: 간단한 키워드 매칭 (개선 여지)

---

#### 2. self_correction.py - 자동 RUNE

```python
def rune_from_eval(eval_report: EvalReport) -> RUNEReport:
    """
    Eval 결과 → RUNE 자동 생성:
    - quality < 0.7 또는 evidence_ok == False → replan
    - 구체적 권장 사항 생성
    """
    q = eval_report.quality
    replan = (not eval_report.evidence_ok) or q < 0.7

    recs = []
    if not eval_report.evidence_ok:
        recs.append("근거 2개 이상 확보(화이트리스트 포함)")
    if q < 0.7:
        recs.append("가독성/논리 표지어 보강 및 중복 근거 제거")
    if not recs:
        recs.append("다음 단계 진행")

    return RUNEReport(
        impact=max(0.2, q),
        transparency=0.75 if eval_report.evidence_ok else 0.55,
        confidence=0.55 if q >= 0.7 else 0.4,
        recommendations=recs,
        replan=replan
    )
```

**E1 vs W2 비교**:

| 항목 | E1 Baseline | W2 Eval |
|------|-------------|---------|
| **Verifiability** | 0.10 (1/10) | 강제 ≥2 인용 |
| **Trust** | 측정 안 함 | 화이트리스트 기반 |
| **Redundancy** | 체크 안 함 | 페널티 0~0.3 |
| **RUNE 생성** | 수동 | 자동 (quality < 0.7 → replan) |
| **권장 사항** | 일반적 | 구체적 (예: "근거 2개 확보") |

---

### 화이트리스트 설정

`configs/phase_controller_e2.yaml`에 추가:

```yaml
evaluation:
  whitelist:
    - "arxiv.org"
    - "scholar.google.com"
    - "github.com"
    - "wikipedia.org"
    - "openai.com"
    - "anthropic.com"
    # 프로젝트별 신뢰 도메인 추가

  weights:
    evidence: 0.45
    readability: 0.25
    logic: 0.15
    trust: 0.15

  thresholds:
    min_citations: 2
    min_trust: 0.7
    replan_quality: 0.7
```

---

## 🔄 E1 → E2 통합 계획

### Phase 1: RAG 인덱싱 (사전 작업)
```bash
# 1. 기존 문서 수집
mkdir -p memory/vectorstore_source
cp docs/*.md memory/vectorstore_source/
cp outputs/E1_*.md memory/vectorstore_source/

# 2. 인덱스 생성
python scripts/index_docs.py \
  --input memory/vectorstore_source/ \
  --output memory/vectorstore/

# 3. 검증
python -c "
from tools.rag.retriever import rag_query
results = rag_query('AGI design', top_k=3)
for hit in results['hits']:
    print(f\"{hit['source']}: {hit['score']:.2f}\")
"
```

**예상 출력**:
```
docs/AGI_INTEGRATION_SENA_CORE_v1.0.md: 0.85
docs/LUBIT_CORE_FDO_AGI_INTEGRATION_v1.0.md: 0.78
outputs/E1_HIGH_RESIDUAL_QUALITATIVE_ANALYSIS.md: 0.72
```

---

### Phase 2: Evaluator 통합

**현재 (E1)**:
```python
# orchestration/persona_orchestrator.py
evaluation = {
    "quality": 0.8,
    "evidence_ok": True,  # 더미
    "risks": []
}
```

**업그레이드 (E2)**:
```python
from orchestrator.evaluator import evaluate

# PersonaOutput 수집
outputs = [thesis_output, antithesis_output, synthesis_output]

# 평가 실행
eval_report = evaluate(outputs, cfg={
    "whitelist": ["arxiv.org", "github.com", ...],
    "weights": {"evidence": 0.45, ...}
})

# RUNE 자동 생성
from orchestrator.self_correction import rune_from_eval
rune_report = rune_from_eval(eval_report)

# 재계획 결정
if rune_report.replan:
    print("Quality too low, replanning...")
    # 루프 재실행 로직
```

---

### Phase 3: Persona 도구 활성화

**Thesis 페르소나에 RAG 추가**:

```python
# personas/thesis.py (기존)
class ThesisPersona:
    def generate_response(self, prompt):
        # 현재: LLM 직접 호출
        return self.backend.call(prompt)

# personas/thesis.py (E2 업그레이드)
class ThesisPersona:
    def generate_response(self, prompt):
        # 1. RAG로 배경 조사
        rag_results = rag_query(prompt, top_k=3)
        context = "\n".join([
            f"[{hit['source']}] {hit['preview']}"
            for hit in rag_results['hits']
        ])

        # 2. Context-enriched 프롬프트
        enriched_prompt = f"""
        Background research:
        {context}

        Based on the above context, {prompt}

        Requirements:
        - Cite at least 2 sources from the research
        - Provide concrete examples
        """

        return self.backend.call(enriched_prompt)
```

**예상 효과**:
- Verifiability: 0.10 → 0.60 (+500%)
- 인용 개수: 0~1개 → 2~3개
- Quality 점수: 0.67 → 0.80

---

## 📊 E2 실험 예상 결과

### Before (E1 Baseline)
```
Total turns: 48
Tool calls: 0
Average quality: 0.67
Verifiability: 0.10 (1/10 facts checked)
Evidence: 0~1 citations per turn
Risks: ["근거 없음", "근거 부족(1개)"] (85%)
```

### After (E2 with W2 packages)
```
Total turns: 48
Tool calls: 12~18 (RAG 주로)
  ├─ Thesis: 4~6 RAG calls
  ├─ Antithesis: 3~5 RAG calls
  └─ Synthesis: 2~3 RAG calls
Average quality: 0.80 (+19%)
Verifiability: 0.60 (+500%)
Evidence: 2~3 citations per turn
Risks: ["중복 근거 과다"] (15%) ← 대폭 감소
```

### Metrics 비교

| 메트릭 | E1 | E2 목표 | 개선율 |
|--------|-----|---------|--------|
| **Quality** | 0.67 | 0.80 | +19% |
| **Verifiability** | 0.10 | 0.60 | +500% |
| **Evidence OK** | 10% | 80% | +700% |
| **Citations/turn** | 0.5 | 2.5 | +400% |
| **Replan rate** | 15% | 10% | -33% |

---

## 🛠️ 통합 체크리스트

### 사전 준비 (Phase 0)
- [ ] Week 2 패키지 4개 압축 해제 완료
- [ ] `memory/vectorstore/` 디렉토리 생성
- [ ] 인덱싱할 문서 수집 (`docs/`, 기존 리포트)

### RAG 설정 (Phase 1)
- [ ] `python scripts/index_docs.py` 실행
- [ ] `vectors.npy`, `meta.json` 생성 확인
- [ ] RAG 쿼리 테스트 (`rag_query("test")`)
- [ ] (선택) FAISS 설치 및 인덱스 생성

### Evaluator 통합 (Phase 2)
- [ ] `orchestrator/evaluator.py` 복사
- [ ] 화이트리스트 설정 (`configs/`)
- [ ] `evaluate()` 함수 통합
- [ ] `rune_from_eval()` 자동화
- [ ] 재계획 로직 연결

### Persona 업그레이드 (Phase 3)
- [ ] Thesis에 RAG 호출 추가
- [ ] Antithesis에 RAG 호출 추가
- [ ] Synthesis에 RAG 호출 추가 (선택)
- [ ] 도구 호출 로깅 활성화

### 실험 실행 (Phase 4)
- [ ] `phase_controller_e2.yaml` 적용
- [ ] E2 실험 실행 (동일 태스크로 E1과 비교)
- [ ] 메트릭 수집 (`outputs/persona_metrics/E2/`)
- [ ] E1 vs E2 비교 리포트 생성

---

## 🚨 주의 사항

### 1. 임베딩 모델 한계
**문제**: 해시 기반 임베딩은 의미론적 이해 부족
```python
embed("empathic AI")  # 해시: bucket_3452, bucket_8791
embed("caring AI")    # 해시: bucket_7261, bucket_8791
# 유사도 낮음 (의미는 유사하지만 단어가 다름)
```

**해결책 (E3 고려)**:
- OpenAI `text-embedding-ada-002` 통합
- Sentence-BERT 로컬 모델
- 현재는 키워드 매칭 수준으로 충분

---

### 2. 인덱스 업데이트
**문제**: 새 문서 추가 시 재인덱싱 필요

**해결책**:
```bash
# 증분 인덱싱 (간단한 방법)
python scripts/index_docs.py \
  --input docs/new/ \
  --output memory/vectorstore/ \
  --append  # 기존 인덱스에 추가
```

---

### 3. 화이트리스트 관리
**문제**: 도메인 화이트리스트가 고정되어 있음

**해결책**:
```yaml
# configs/whitelist.yaml
trusted_domains:
  academic:
    - "arxiv.org"
    - "scholar.google.com"
  tech:
    - "github.com"
    - "stackoverflow.com"
  company:
    - "openai.com"
    - "anthropic.com"
  project_specific:
    - "your-internal-docs.com"
```

---

## 📈 예상 타임라인

### Week 2 통합 (E2 실험)
```
Day 1: RAG 인덱싱 (2시간)
  ├─ 문서 수집
  ├─ 인덱스 생성
  └─ 테스트

Day 1: Evaluator 통합 (2시간)
  ├─ evaluator.py 복사
  ├─ 화이트리스트 설정
  └─ 자동 RUNE 연결

Day 2: Persona 업그레이드 (3시간)
  ├─ RAG 호출 코드 추가
  ├─ 프롬프트 수정
  └─ 테스트

Day 2: E2 실험 실행 (2시간)
  ├─ E2 실행 (1시간)
  ├─ 메트릭 수집 (30분)
  └─ E1 vs E2 비교 (30분)
```

**총 소요 시간**: 2일 (9시간)

---

## 🎯 핵심 요약

### Week 2가 해결하는 E1 문제
1. ✅ **Verifiability 0.10 → 0.60**: 증거 기반 평가
2. ✅ **도구 미사용 → RAG 활성화**: 배경 지식 통합
3. ✅ **자동 RUNE 생성**: quality < 0.7 → 재계획
4. ✅ **화이트리스트**: 신뢰도 측정

### 통합 우선순위
1. 🔴 **High**: RAG 인덱싱, Evaluator 통합
2. 🟡 **Medium**: Persona RAG 호출
3. 🟢 **Low**: FAISS 최적화, 임베딩 업그레이드 (E3)

### 다음 단계
- **루빛**: E2 실험 실행 (phase_controller_e2.yaml)
- **세나**: Week 3 패키지 사전 검토 (준비)

---

**작성자**: 세나 (Sena)
**버전**: 1.0
**상태**: 루빛 E2 실험 대기 중
**토큰 사용**: 85K / 200K (42%)
