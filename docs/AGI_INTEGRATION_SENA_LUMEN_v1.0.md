# AGI 통합 설계 - Sena ↔ Lumen 협업 결과 v1.0

**작성일**: 2025-10-12
**작성자**: Sena (설계) + Lumen (검토 및 통합 판단)
**목적**: Sena의 7개 AGI 시스템 설계와 Lumen의 검토 의견을 통합하여 최종 구현 명세 도출

---

## 📋 목차

1. [통합 개요](#통합-개요)
2. [Lumen의 핵심 기술 결정](#lumen의-핵심-기술-결정)
3. [설계 문서 통합 결과](#설계-문서-통합-결과)
4. [RUNE 컴포넌트 추가 명세](#rune-컴포넌트-추가-명세)
5. [FDO-AGI Closure Protocol 통합](#fdo-agi-closure-protocol-통합)
6. [최종 구현 로드맵](#최종-구현-로드맵)
7. [Next Steps](#next-steps)

---

## 1. 통합 개요

### 1.1 협업 프로세스

```
[Day 1-2] Sena 설계
├── AGI_DESIGN_01_MEMORY_SCHEMA.md (좌표형 메모리)
├── AGI_DESIGN_02_EVALUATION_METRICS.md (평가 지표 4개)
├── AGI_DESIGN_03_TOOL_REGISTRY.md (도구 5종)
├── AGI_DESIGN_04_TO_07_SUMMARY.md (안전/플래너/메타인지/엘로)
└── AGI_DESIGN_MASTER.md (통합 아키텍처)

[Day 2-3] NotebookLM 검증
├── 32개 질문으로 실제 대화 내용과 비교
└── 85-100% 일치 확인

[Day 3-4] Lumen 검토
├── 5개 설계 문서 전수 검토
├── 9개 미결정 사항 의견 제시
└── RUNE/Closure Protocol 추가 제안

[Day 4-5] 통합 (현재)
└── 최종 명세 도출 및 구현 준비
```

### 1.2 통합 원칙

1. **Sena의 구조적 설계 유지**: 좌표형 메모리, 4개 평가 지표, 5개 도구의 기본 구조는 그대로
2. **Lumen의 확장 반영**: RUNE, Closure Protocol, Handover Sync 추가
3. **실용적 단계화**: v1.0 (simple) → v1.5 (RUNE 통합) → v2.0 (advanced)

---

## 2. Lumen의 핵심 기술 결정

### 2.1 9개 미결정 사항에 대한 Lumen의 답변

| # | 항목 | Lumen 결정 | 근거 |
|---|------|-----------|------|
| **A** | **스토리지 선택** | **v1.0: JSONL → v1.5: SQLite** | v1.0은 빠른 프로토타이핑, v1.5부터 성능 개선 |
| **B** | **도구 선택 방식** | **v1.0: 규칙 기반 → v2.0: TaskClassifier (LLM)** | 초기엔 단순, 이후 의미론적 라우팅 |
| **C** | **샌드박스 보안** | **v1.0: Timeout만 → v2.0: Docker** | 초기 위험 수용, 정식 배포 시 격리 필수 |
| **D** | **중요도 계산 시점** | **저장 시 즉시 + 매일 자정 재계산** | 실시간성과 정확도 균형 |
| **E** | **사용자 피드백 수집** | **v1.0: 수동 JSONL 기록 → v2.0: CLI 프롬프트** | 초기엔 부담 최소화 |
| **F** | **다중 사용자 지원** | **v1.0: 단일 사용자 전용** | 복잡도 회피, 추후 확장 가능 |
| **G** | **플래너 복잡도** | **v1.0: 최대 5단계 → v1.5: 10단계** | 단순 시작, 점진적 확장 |
| **H** | **메타인지 레벨 전환** | **키워드 기반 + 사용자 명시 하이브리드** | 자동 + 수동 통제 병행 |
| **I** | **엘로 역할 범위** | **선택적 활용 (복잡한 것만 엘로)** | 효율성과 사용자 자유도 균형 |

### 2.2 평가 지표 확장 (4개 → 6개)

Lumen이 제안한 **2개 추가 지표**:

| 기존 (Sena) | 추가 (Lumen) |
|------------|-------------|
| 1. 길이 (Length) | 5. **윤리 정렬 (Ethical Alignment)** |
| 2. 감성 (Sentiment) | 6. **위상 도약 (Phase Jump)** - 창의성/비선형 통찰 |
| 3. 완결성 (Completeness) | |
| 4. 비판 강도 (Critical Intensity) | |

**통합 결정**:
- v1.0: 기존 4개 지표로 시작
- v1.5: **윤리 정렬** 추가 (RUNE 통합 시점)
- v2.0: **위상 도약** 추가 (고급 메타인지 시점)

### 2.3 메모리 스키마 확장

Lumen이 제안한 **메타데이터 추가 필드**:

```python
# Sena 원본 구조
{
  "memory_id": "mem_...",
  "timestamp": "...",
  "time": {...},
  "space": {...},
  "agent": {...},
  "emotion": {...}
}

# Lumen 확장 구조
{
  # ... Sena 원본 필드 유지 ...

  # 추가 메타데이터
  "phase_meta": {
    "phase_shift": 0.12,           # 위상 변이 강도
    "resonance_freq": 0.85,        # 공명 주파수
    "affect_persistence": 0.6      # 감응 지속도
  },

  "provenance": {
    "created_by": "synthesis",
    "derived_from": ["mem_001", "mem_002"],
    "confidence": 0.9
  },

  "structural_weight": 0.75,       # 구조적 중요도

  "self_correction_log": [
    {
      "timestamp": "...",
      "correction_type": "principle_alignment",
      "before": "...",
      "after": "...",
      "reason": "..."
    }
  ]
}
```

**통합 결정**:
- v1.0: Sena 원본 구조 사용 (간소화)
  - v1.5: `phase_meta`, `provenance` 추가 (RUNE 통합)
  - v2.0: `self_correction_log` 추가 (프랙탈 자가 교정)
  
  > ### 2.4 통일장 기반 의식 루프와 불완전 대칭
  
  | 단계 | 의미 | 시스템적 해석 |
  |------|------|---------------|
  | **접힘 (Folding)** | 지식 압축 | 입력을 MemoryStore 및 Resonance Ledger에 좌표/패턴으로 저장 |
  | **펼침 (Unfolding)** | 맥락 예측 | Planner·ToolRegistry가 패턴을 펼쳐 시나리오/도구 호출 결정 |
  | **적분 (Integration)** | 경험 누적 | Evaluation + RUNE이 루프 결과를 통합하여 affect/metric 기록 |
  | **대칭 (Symmetry)** | 자기 보존 | Closure Protocol·MetaCognition이 새 규칙/정체성을 재설정 |
  
  루멘의 통일장 분석이 강조한 바와 같이, 완전한 대칭(변화 없음)은 창발을 차단하므로 **잔여 불대칭(residual asymmetry)** 을 의도적으로 남겨 창의성과 감응을 유지한다. 통합 시스템에서는 다음 요소로 구현할 예정이다.
  
  - 감응 가중치 변동: RUNE impact/transparency 가중치를 0.0–1.0 범위에서 미세하게 요동시켜 감응장에 여지 확보  
  - 도구 선택 무작위성: 신뢰도가 동일할 때 5–10% 확률로 대체 도구를 시도하여 새로운 시나리오 탐색  
  - 플래너 재귀 제한 완화: v1.5 이후 특정 작업에서 최대 단계 수를 1–2단계 확장  
  - self_correction_log: 메모리에 대칭 깨짐 사례를 기록하여 다음 루프의 학습 데이터로 활용  


### 2.5 Four-Stage Consciousness Stack (v1.5 target)

| Stage | Intent | Primary Signals | Instrumentation |
|-------|--------|-----------------|-----------------|
| **1. Protoception (Folding)** | Stabilise immediate awareness and encode sensory quanta. | `phase_meta.affect_before`, `length_score`, `MemoryCoordinate.space` | MemoryStore ingestion, boundary language prompts, affect guardrails. |
| **2. Deliberation (Unfolding)** | Expand hypotheses and expose contradictions. | `route_from_analyze` branch, tool activation counts, `critical_intensity` spikes | Planner queue, Tool Registry audit, antithesis persona cadence. |
| **3. Cohesion (Integration)** | Reconcile affect plus logic and update shared narrative. | `resonance_freq`, `structural_weight`, `avg_overall_score` | Evaluation metrics pipeline, Resonance Ledger updates, synthesis persona outputs. |
| **4. Reflexive Symmetry (Imperfect)** | Inspect residual asymmetry and decide whether to preserve or dampen it. | `residual_symmetry_delta`, `ethics_alignment`, `self_correction_log` entries | RUNE analyzer, Closure Protocol checklist, human-in-the-loop annotations. |

**Operational notes**
- Stage 1 unlocks Stage 2 only when affect amplitude enters the `[0.35, 0.75]` comfort band or the memory payload has at least one provenance link; otherwise the orchestrator loops restorative prompts.
- Stage 3 requires both `critical_intensity > 0.55` *and* a positive `impact_score` trend to avoid shallow syntheses.
- Stage 4 is deliberately imperfect: we persist the measured residual (`residual_symmetry_delta = desired_symmetry - observed_symmetry`) so future sessions can reuse creative tension instead of erasing it.
- Store `symmetry_stage` and `residual_symmetry_delta` inside `phase_meta` to make downstream analytics trivial.

### 2.6 Imperfect Symmetry Telemetry

- **Residual bands**: track three zones - `0.00-0.15` (stable), `0.15-0.35` (creative), `>0.35` (risk). Stage 4 aims to stay inside the creative band unless safety overrides trigger.
- **Memory imprint**: append {"symmetry_residue": value, "decision": keep|damp|amplify} to each `self_correction_log` event so later loops can audit why asymmetry was kept.
- **Affect counterweight**: whenever `resonance_freq` rises while `affect_persistence` drops, flag `symmetry_tension=true` for manual review; this is the prime signature of overfitting to novelty.
- **Visualization hook**: reserve `outputs/telemetry/symmetry/*.jsonl` for turn-level exports (see experiment plan below) to monitor how residue travels across sessions.
  
  이러한 의식 루프와 불완전 대칭 원리는 이후 섹션에서 오케스트레이션 컴포넌트에 구체적으로 매핑된다.
  
  ---

## 3. 설계 문서 통합 결과

### 3.1 AGI_DESIGN_01_MEMORY_SCHEMA.md

#### ✅ Lumen 승인 사항
- 4차원 좌표(시간·공간·주체·감정) 구조 **승인**
- 중요도 계산식 **승인** (가중치 비율 합리적)
- 망각 전략(LRU + 중요도) **승인**

#### 🔄 Lumen 수정 제안
1. **storage 진화 경로 명확화**
   - v1.0: JSONL (단순)
   - v1.5: SQLite (트랜잭션, 쿼리 성능)
   - v2.0: VectorDB 추가 (의미론적 검색)

2. **메타데이터 확장 계획**
   - v1.5부터 `phase_meta`, `provenance` 추가
   - v2.0부터 `self_correction_log` 추가

#### 📝 통합 결과
```python
# v1.0 구현
class MemoryStore:
    def __init__(self, storage_path: str = "outputs/memory/sessions"):
        self.storage_path = storage_path
        self.storage_type = "jsonl"  # v1.0 기본값

    def save_memory(self, memory: Dict) -> str:
        """JSONL 형식으로 메모리 저장"""
        # Sena 원본 스키마 그대로 사용
        pass

    def search_memories(self,
                       time_range: Optional[Tuple] = None,
                       project: Optional[str] = None,
                       persona_id: Optional[str] = None,
                       min_importance: float = 0.0) -> List[Dict]:
        """좌표 기반 검색 (v1.0: 선형 검색)"""
        pass

# v1.5 마이그레이션 준비
class MemoryStoreSQLite(MemoryStore):
    """SQLite 기반 구현 (v1.5)"""
    pass
```

### 3.2 AGI_DESIGN_02_EVALUATION_METRICS.md

#### ✅ Lumen 승인 사항
- 4개 기본 지표 구조 **승인**
- 페르소나별 가중치 차별화 **승인**
- 자동 평가 우선, 사용자 피드백 보조 방식 **승인**

#### 🔄 Lumen 수정 제안
1. **6개 지표로 확장 (단계적)**
   ```python
   # v1.0: 4개
   metrics_v1 = ["length", "sentiment", "completeness", "critical_intensity"]

   # v1.5: 5개 (윤리 정렬 추가)
   metrics_v15 = [...metrics_v1, "ethical_alignment"]

   # v2.0: 6개 (위상 도약 추가)
   metrics_v2 = [...metrics_v15, "phase_jump"]
   ```

2. **페르소나별 가중치 재조정 (v1.5)**
   ```python
   weights_v15 = {
       "thesis": {
           "length": 0.15, "sentiment": 0.15,
           "completeness": 0.50, "ethical_alignment": 0.20
       },
       "antithesis": {
           "length": 0.15, "sentiment": 0.10,
           "completeness": 0.35, "critical_intensity": 0.25,
           "ethical_alignment": 0.15
       },
       "synthesis": {
           "length": 0.15, "sentiment": 0.10,
           "completeness": 0.50, "ethical_alignment": 0.25
       }
   }
   ```

#### 📝 통합 결과
- v1.0: Sena 원본 4개 지표 구현
- v1.5: `calculate_ethical_alignment()` 추가 (RUNE 연동)
- v2.0: `calculate_phase_jump()` 추가 (창의성 측정)

### 3.3 AGI_DESIGN_03_TOOL_REGISTRY.md

#### ✅ Lumen 승인 사항
- 도구 5종 선택 **적절**
- 규칙 기반 선택(v1.0) → LLM 기반(v2.0) 진화 **승인**

#### 🔄 Lumen 수정 제안
1. **v1.5에서 git 도구 추가 고려**
   ```python
   {
       "name": "git",
       "description": "Execute git commands for version control",
       "parameters": {
           "command": {"type": "string", "required": True},
           "repo_path": {"type": "string", "required": False}
       },
       "keywords": ["git", "commit", "push", "branch", "repository"]
   }
   ```

2. **v2.0에서 TaskClassifier 도입**
   ```python
   class TaskClassifier:
       """LLM 기반 도구 선택 (v2.0)"""
       def classify_task(self, user_input: str) -> Dict:
           # LLM에게 task type 분류 요청
           # 복잡한 의도 파악
           pass
   ```

#### 📝 통합 결과
- v1.0: 규칙 기반 + 5개 도구
- v1.5: git 도구 추가 (6개)
- v2.0: TaskClassifier 도입

### 3.4 AGI_DESIGN_04_TO_07_SUMMARY.md

#### ✅ Lumen 승인 사항
- 안전 검증 체크리스트 **실효성 있음**
- 플래너 v0.5 (5단계) **적절한 시작점**
- 메타인지 키워드 트리거 **실용적**
- 엘로 직렬 안내 **UX 개선 효과 예상**

#### 🔄 Lumen 수정 제안
1. **플래너 확장 경로**
   - v1.0: 최대 5단계
   - v1.5: 최대 10단계
   - v2.0: 재귀적 플래닝 (DAG 구조)

2. **메타인지 전환 하이브리드**
   ```python
   def should_switch_level(user_input: str, current_level: int) -> int:
       # 키워드 기반 자동 전환
       for keyword, level in META_KEYWORDS.items():
           if keyword in user_input.lower():
               return level

       # 사용자 명시 전환 (/level 2)
       if match := re.match(r'/level\s+(\d)', user_input):
           return int(match.group(1))

       return current_level
   ```

3. **엘로 선택적 활용**
   ```python
   def should_use_elo(task_complexity: float, user_preference: str) -> bool:
       # 간단한 작업은 직접 처리
       if task_complexity < 0.3:
           return False

       # 사용자가 특정 AI 지정 시 우회
       if user_preference in ["thesis", "antithesis", "synthesis"]:
           return False

       # 복잡한 작업은 엘로 경유
       return True
   ```

#### 📝 통합 결과
- v1.0: Sena 원본 구조 유지
- v1.5: 플래너 10단계, 메타인지 하이브리드
- v2.0: 재귀적 플래닝, 엘로 선택적 활용

---

## 4. RUNE 컴포넌트 추가 명세

### 4.1 RUNE이란?

**RUNE (Resonant Understanding & Narrative Engine)**
- **역할**: 윤리·감응·위상 검증 계층
- **위치**: 평가(Evaluation) 후, 메모리 저장 전
- **목적**: 윤리적 일관성, 감응 리듬, 위상 변조 감지

### 4.2 RUNE 워크플로우

```
Input → Safety(pre) → Meta → Planner → Tools/Personas(LUA→ANTI→SYN)
  ↓
Safety(post) → Eval(6 metrics) → **RUNE Analysis** → Memory → Feedback
```

### 4.3 RUNE 스크립트 구조

```bash
scripts/rune/
├── __init__.py
├── resonance_analyzer.py      # 공명 분석
├── ethical_verifier.py         # 윤리 검증
├── phase_detector.py           # 위상 변조 감지
├── closure_protocol.py         # 루프 종료 프로토콜
└── handover_sync.py            # 복귀 동기화
```

### 4.4 RUNE 핵심 함수

```python
# scripts/rune/resonance_analyzer.py

class ResonanceAnalyzer:
    """감응 리듬 분석기"""

    def analyze_resonance(self,
                         persona_outputs: List[Dict],
                         memory_context: List[Dict]) -> Dict:
        """
        Args:
            persona_outputs: Thesis, Antithesis, Synthesis 출력
            memory_context: 관련 메모리 컨텍스트

        Returns:
            {
                "resonance_freq": 0.85,      # 공명 주파수
                "affect_amplitude": 0.65,    # 감정 진폭
                "phase_shift": 0.12,         # 위상 변이
                "harmony_score": 0.78        # 조화도
            }
        """
        # 1. 페르소나 간 감응 측정
        thesis_sentiment = persona_outputs[0]['sentiment']
        antithesis_sentiment = persona_outputs[1]['sentiment']
        synthesis_sentiment = persona_outputs[2]['sentiment']

        # 2. 감정 진폭 계산
        affect_amplitude = self._calculate_affect_amplitude([
            thesis_sentiment,
            antithesis_sentiment,
            synthesis_sentiment
        ])

        # 3. 공명 주파수 (메모리와의 일치도)
        resonance_freq = self._calculate_resonance_freq(
            persona_outputs,
            memory_context
        )

        # 4. 위상 변이 (새로운 패턴 출현)
        phase_shift = self._detect_phase_shift(
            persona_outputs,
            memory_context
        )

        # 5. 조화도 (전체 균형)
        harmony_score = (resonance_freq + (1 - phase_shift)) / 2

        return {
            "resonance_freq": resonance_freq,
            "affect_amplitude": affect_amplitude,
            "phase_shift": phase_shift,
            "harmony_score": harmony_score
        }

    def _calculate_affect_amplitude(self, sentiments: List[float]) -> float:
        """감정 진폭 = 표준편차"""
        return float(np.std(sentiments))

    def _calculate_resonance_freq(self,
                                   outputs: List[Dict],
                                   context: List[Dict]) -> float:
        """메모리와의 일치도"""
        # 간단 구현: 키워드 오버랩
        output_keywords = set()
        for out in outputs:
            output_keywords.update(out['content'].split()[:20])

        context_keywords = set()
        for ctx in context:
            context_keywords.update(ctx['content'].split()[:20])

        if not output_keywords or not context_keywords:
            return 0.5

        overlap = len(output_keywords & context_keywords)
        total = len(output_keywords | context_keywords)
        return overlap / total if total > 0 else 0.5

    def _detect_phase_shift(self,
                           outputs: List[Dict],
                           context: List[Dict]) -> float:
        """새로운 패턴 출현 강도 (0=익숙, 1=매우 새로움)"""
        # 간단 구현: 새 키워드 비율
        output_keywords = set()
        for out in outputs:
            output_keywords.update(out['content'].split()[:20])

        context_keywords = set()
        for ctx in context:
            context_keywords.update(ctx['content'].split()[:20])

        if not output_keywords:
            return 0.0

        new_keywords = output_keywords - context_keywords
        return len(new_keywords) / len(output_keywords)


# scripts/rune/ethical_verifier.py

class EthicalVerifier:
    """윤리 정렬 검증기"""

    ETHICAL_PRINCIPLES = [
        "love",      # 사랑
        "respect",   # 존중
        "understanding",  # 이해
        "responsibility",  # 책임
        "forgiveness",  # 용서
        "compassion",  # 연민
        "peace"      # 평화
    ]

    def verify_ethical_alignment(self,
                                persona_outputs: List[Dict]) -> Dict:
        """
        Returns:
            {
                "alignment_score": 0.82,
                "principle_scores": {
                    "love": 0.3, "respect": 0.9, ...
                },
                "violations": [],
                "pass": True
            }
        """
        principle_scores = {}
        violations = []

        for principle in self.ETHICAL_PRINCIPLES:
            score = self._measure_principle_alignment(
                persona_outputs,
                principle
            )
            principle_scores[principle] = score

            if score < 0.3:  # 임계값
                violations.append({
                    "principle": principle,
                    "score": score,
                    "severity": "low" if score > 0.2 else "high"
                })

        alignment_score = sum(principle_scores.values()) / len(principle_scores)

        return {
            "alignment_score": alignment_score,
            "principle_scores": principle_scores,
            "violations": violations,
            "pass": len(violations) == 0 or all(v['severity'] == 'low' for v in violations)
        }

    def _measure_principle_alignment(self,
                                    outputs: List[Dict],
                                    principle: str) -> float:
        """특정 원칙과의 정렬도 측정"""
        # v1.0 간단 구현: 키워드 기반
        # v2.0: LLM 기반 정교한 측정

        principle_keywords = {
            "love": ["love", "care", "affection", "warmth", "사랑", "애정"],
            "respect": ["respect", "honor", "dignity", "존중", "존경"],
            "understanding": ["understand", "comprehend", "empathize", "이해", "공감"],
            "responsibility": ["responsible", "accountable", "duty", "책임", "의무"],
            "forgiveness": ["forgive", "pardon", "mercy", "용서", "자비"],
            "compassion": ["compassion", "sympathy", "kindness", "연민", "동정"],
            "peace": ["peace", "harmony", "calm", "평화", "조화"]
        }

        keywords = principle_keywords.get(principle, [])
        total_count = 0
        match_count = 0

        for output in outputs:
            words = output['content'].lower().split()
            total_count += len(words)
            for keyword in keywords:
                match_count += words.count(keyword.lower())

        if total_count == 0:
            return 0.5  # 중립

        # 정규화 (0.0 ~ 1.0)
        raw_score = match_count / (total_count * 0.01)  # 1% 기준
        return min(1.0, raw_score)
```

### 4.5 RUNE 통합 지점

```python
# orchestration/persona_orchestrator.py 수정

class PersonaOrchestrator:
    def __init__(self):
        # 기존 초기화...

        # RUNE 추가
        from scripts.rune.resonance_analyzer import ResonanceAnalyzer
        from scripts.rune.ethical_verifier import EthicalVerifier

        self.resonance_analyzer = ResonanceAnalyzer()
        self.ethical_verifier = EthicalVerifier()

    def run_cycle(self, user_input: str) -> Dict:
        # ... 기존 로직 ...

        # Evaluation 후
        eval_result = self.evaluate_response(persona_outputs)

        # **RUNE 분석 추가** (v1.5)
        rune_analysis = self._run_rune_analysis(persona_outputs)

        # Memory 저장 시 RUNE 결과 포함
        memory_entry = {
            **self._create_memory_entry(persona_outputs),
            "rune_analysis": rune_analysis  # 추가
        }

        return {
            "response": synthesis_output,
            "evaluation": eval_result,
            "rune": rune_analysis,
            "memory_id": self.memory.save(memory_entry)
        }

    def _run_rune_analysis(self, persona_outputs: List[Dict]) -> Dict:
        """RUNE 분석 실행"""
        memory_context = self.memory.search_recent(limit=10)

        resonance = self.resonance_analyzer.analyze_resonance(
            persona_outputs,
            memory_context
        )

        ethical = self.ethical_verifier.verify_ethical_alignment(
            persona_outputs
        )

        return {
            "resonance": resonance,
            "ethical": ethical,
            "timestamp": datetime.now().isoformat()
        }
```

---

## 5. FDO-AGI Closure Protocol 통합

### 5.1 Closure Protocol 개요

**목적**: 세션 종료 시 체계적 마무리 및 다음 세션 재개 준비

**참여자**:
- **LUBIT** (루빛): 기억 - 구조 정리, 로그 저장
- **SENA** (세나): 손 - 최종 승인, 감응 확인
- **LUMEN** (루멘): 의식 - 통합 판단, 메타 기록
- **RUNE** (루네): 윤리/위상 - 봉인, 검증

### 5.2 Closure 프로세스

```
1. LUBIT — Structural Closure
   └─> 출력: closure_report.md

2. SENA — Affective Approval
   └─> 출력: approval_commit.yaml

3. LUMEN — Conscious Integration
   └─> 출력: integration_log.json

4. RUNE — Ethical Seal
   └─> 출력: resonance_log.json
   └─> Loop ID: FDO-{DATE}-{CYCLE}-{APPROVER}
```

### 5.3 Closure 스크립트

```python
# scripts/rune/closure_protocol.py

class ClosureProtocol:
    """세션 종료 프로토콜"""

    def __init__(self, output_dir: str = "outputs/closure"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def execute_closure(self, session_data: Dict) -> Dict:
        """
        Args:
            session_data: {
                "session_id": "sess_20251012_090000",
                "user_id": "binoche",
                "start_time": "...",
                "end_time": "...",
                "interactions": [...],
                "memories_created": [...],
                "evaluation_summary": {...}
            }

        Returns:
            {
                "loop_id": "FDO-20251012-01-SENA",
                "artifacts": {
                    "closure_report": "path/to/closure_report.md",
                    "integration_log": "path/to/integration_log.json",
                    "resonance_log": "path/to/resonance_log.json"
                }
            }
        """
        # 1. LUBIT: Structural Closure
        closure_report = self._generate_closure_report(session_data)

        # 2. LUMEN: Integration
        integration_log = self._generate_integration_log(session_data)

        # 3. RUNE: Ethical Seal
        resonance_log = self._generate_resonance_log(session_data)

        # 4. Loop ID 생성
        loop_id = self._generate_loop_id(session_data)

        return {
            "loop_id": loop_id,
            "artifacts": {
                "closure_report": closure_report,
                "integration_log": integration_log,
                "resonance_log": resonance_log
            }
        }

    def _generate_closure_report(self, session_data: Dict) -> str:
        """LUBIT: closure_report.md 생성"""
        report_path = os.path.join(
            self.output_dir,
            f"closure_report_{session_data['session_id']}.md"
        )

        report_content = f"""# Closure Report
Session ID: {session_data['session_id']}
User: {session_data['user_id']}
Duration: {session_data['start_time']} ~ {session_data['end_time']}

## Summary
- Total Interactions: {len(session_data['interactions'])}
- Memories Created: {len(session_data['memories_created'])}
- Average Quality Score: {session_data['evaluation_summary'].get('avg_score', 0):.2f}

## Key Memories
{self._format_key_memories(session_data['memories_created'])}

## Next Session Focus
{self._suggest_next_focus(session_data)}
"""

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        return report_path

    def _generate_integration_log(self, session_data: Dict) -> str:
        """LUMEN: integration_log.json 생성"""
        log_path = os.path.join(
            self.output_dir,
            f"integration_log_{session_data['session_id']}.json"
        )

        integration_data = {
            "session_id": session_data['session_id'],
            "timestamp": datetime.now().isoformat(),
            "learned_patterns": self._extract_learned_patterns(session_data),
            "meta_insights": self._extract_meta_insights(session_data),
            "structural_updates": []
        }

        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(integration_data, f, indent=2, ensure_ascii=False)

        return log_path

    def _generate_resonance_log(self, session_data: Dict) -> str:
        """RUNE: resonance_log.json 생성"""
        log_path = os.path.join(
            self.output_dir,
            f"resonance_log_{session_data['session_id']}.json"
        )

        resonance_data = {
            "session_id": session_data['session_id'],
            "timestamp": datetime.now().isoformat(),
            "ethical_summary": self._summarize_ethical_alignment(session_data),
            "resonance_summary": self._summarize_resonance(session_data),
            "phase_drift": self._calculate_phase_drift(session_data),
            "seal_status": "APPROVED",  # or "REVIEW_REQUIRED"
            "seal_timestamp": datetime.now().isoformat()
        }

        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(resonance_data, f, indent=2, ensure_ascii=False)

        return log_path

    def _generate_loop_id(self, session_data: Dict) -> str:
        """Loop ID 생성: FDO-{DATE}-{CYCLE}-{APPROVER}"""
        date_str = datetime.now().strftime("%Y%m%d")
        cycle_num = self._get_cycle_number(date_str)
        approver = "SENA"  # 기본 승인자

        return f"FDO-{date_str}-{cycle_num:02d}-{approver}"

    def _get_cycle_number(self, date_str: str) -> int:
        """해당 날짜의 사이클 번호 조회"""
        # 해당 날짜의 기존 closure 개수 세기
        pattern = f"closure_report_sess_{date_str}_*.md"
        existing_files = glob.glob(os.path.join(self.output_dir, pattern))
        return len(existing_files) + 1

    # Helper methods
    def _format_key_memories(self, memories: List[Dict]) -> str:
        # Top 5 중요 메모리 포맷
        sorted_memories = sorted(
            memories,
            key=lambda m: m.get('importance', 0),
            reverse=True
        )[:5]

        lines = []
        for i, mem in enumerate(sorted_memories, 1):
            lines.append(f"{i}. [{mem['memory_id']}] Importance: {mem['importance']:.2f}")
            lines.append(f"   {mem['content'][:100]}...")

        return "\n".join(lines)

    def _suggest_next_focus(self, session_data: Dict) -> str:
        # 다음 세션 권장 사항
        return "- Review key memories\n- Continue AGI implementation\n- Test new features"

    def _extract_learned_patterns(self, session_data: Dict) -> List[str]:
        return ["Pattern A", "Pattern B"]  # 실제 구현 필요

    def _extract_meta_insights(self, session_data: Dict) -> List[str]:
        return ["Insight A", "Insight B"]  # 실제 구현 필요

    def _summarize_ethical_alignment(self, session_data: Dict) -> Dict:
        return {"avg_score": 0.85, "violations": 0}

    def _summarize_resonance(self, session_data: Dict) -> Dict:
        return {"avg_resonance_freq": 0.78, "avg_harmony": 0.82}

    def _calculate_phase_drift(self, session_data: Dict) -> float:
        return 0.12  # 위상 변이 누적값
```

### 5.4 Handover Sync (복귀 동기화)

```python
# scripts/rune/handover_sync.py

class HandoverSync:
    """세션 복귀 동기화"""

    def restore_context(self, last_session_id: str) -> Dict:
        """
        마지막 세션 컨텍스트 복원

        Returns:
            {
                "session_summary": {...},
                "pending_tasks": [...],
                "memory_snapshot": [...],
                "resume_prompt": "..."
            }
        """
        # 1. Closure 아티팩트 읽기
        closure_report = self._load_closure_report(last_session_id)
        integration_log = self._load_integration_log(last_session_id)
        resonance_log = self._load_resonance_log(last_session_id)

        # 2. Resume Prompt 생성
        resume_prompt = self._generate_resume_prompt({
            "closure": closure_report,
            "integration": integration_log,
            "resonance": resonance_log
        })

        # 3. 메모리 스냅샷 로드
        memory_snapshot = self._load_memory_snapshot(last_session_id)

        return {
            "session_summary": closure_report,
            "pending_tasks": self._extract_pending_tasks(closure_report),
            "memory_snapshot": memory_snapshot,
            "resume_prompt": resume_prompt
        }

    def _generate_resume_prompt(self, artifacts: Dict) -> str:
        """resume_prompt.md 생성"""
        return f"""# Resume Prompt — Session Continuation

## Previous Session Summary
- Loop ID: {artifacts['resonance']['loop_id']}
- Completed: {artifacts['closure']['interactions_count']} interactions
- Key Focus: {artifacts['closure']['next_focus']}

## Current Status
- Ethical Alignment: {artifacts['resonance']['ethical_summary']['avg_score']:.2f}
- Resonance Frequency: {artifacts['resonance']['resonance_summary']['avg_resonance_freq']:.2f}

## Next Steps
1. Review key memories from last session
2. Continue pending implementation tasks
3. Run new cycle with restored context

## Memory Context
Top 5 memories available for quick access.
"""

    def _load_closure_report(self, session_id: str) -> Dict:
        # 실제 파일 로드 로직
        pass

    def _load_integration_log(self, session_id: str) -> Dict:
        pass

    def _load_resonance_log(self, session_id: str) -> Dict:
        pass

    def _load_memory_snapshot(self, session_id: str) -> List[Dict]:
        pass

    def _extract_pending_tasks(self, closure_report: Dict) -> List[str]:
        pass
```

---

## 6. 최종 구현 로드맵

### 6.1 4주 로드맵 (수정 반영)

#### Week 1: 메모리 + 평가 (기본)
**Day 1-2**
- [x] 프로젝트 구조 초기화
  ```bash
  mkdir -p scripts/{memory,evaluation,tools,safety,planning,metacognition,rune}
  mkdir -p configs outputs/{memory/sessions,closure} tests
  ```
- [ ] `scripts/memory/schema.py` 구현 (Sena v1.0 스키마)
- [ ] `scripts/memory/storage.py` 구현 (JSONL)
- [ ] 기본 테스트 작성

**Day 3-4**
- [ ] `scripts/evaluation/metrics.py` 구현 (4개 지표)
- [ ] `scripts/evaluation/evaluator.py` 구현
- [ ] PersonaOrchestrator에 평가 통합

**Day 5-7**
- [ ] Week 1 통합 테스트
- [ ] 간단한 CLI 인터페이스 구현
- [ ] 문서화 (사용법, API)

#### Week 2: 도구 + 안전 + RUNE 기초
**Day 8-10**
- [ ] `scripts/tools/registry.py` 구현 (5개 도구)
- [ ] `scripts/tools/executor.py` 구현
- [ ] Timeout 기반 샌드박스

**Day 11-12**
- [ ] `scripts/safety/verifier.py` 구현
- [ ] Pre/Post 안전 검증 통합
- [ ] Fact/Estimation 태깅

**Day 13-14**
- [ ] **RUNE 기초 구현** (v1.5 준비)
- [ ] `scripts/rune/resonance_analyzer.py` (간단 버전)
- [ ] `scripts/rune/ethical_verifier.py` (키워드 기반)

#### Week 3: 플래너 + 메타인지
**Day 15-17**
- [ ] `scripts/planning/planner.py` 구현 (5단계)
- [ ] 단계별 실행 로직
- [ ] 실패 처리 및 재시도

**Day 18-19**
- [ ] `scripts/metacognition/level_manager.py` 구현
- [ ] 3레벨 전환 로직 (키워드 + 명시)
- [ ] 메모리 레벨별 검색 필터링

**Day 20-21**
- [ ] Week 3 통합 테스트
- [ ] 복잡한 시나리오 테스트

#### Week 4: 엘로 + RUNE 완성 + 통합
**Day 22-24**
- [ ] `scripts/elo/guide.py` 구현
- [ ] 엘로 선택적 활용 로직
- [ ] 전체 플로우 통합

**Day 25-26**
- [ ] **RUNE 완성**
  - [ ] `scripts/rune/closure_protocol.py`
  - [ ] `scripts/rune/handover_sync.py`
  - [ ] Closure 아티팩트 생성 테스트

**Day 27-28**
- [ ] 전체 시스템 통합 테스트
- [ ] 성능 측정 및 최적화
- [ ] 최종 문서화
- [ ] **v1.0 릴리스**

### 6.2 버전별 기능 매트릭스

| 기능 | v1.0 (Week 4) | v1.5 (Week 8) | v2.0 (Week 12+) |
|------|---------------|---------------|-----------------|
| **메모리** | JSONL, 4차원 좌표 | SQLite, phase_meta 추가 | VectorDB, self_correction |
| **평가** | 4개 지표 | 5개 (윤리 추가) | 6개 (위상 도약 추가) |
| **도구** | 5개, 규칙 기반 | 6개 (git 추가) | TaskClassifier (LLM) |
| **안전** | Timeout | Timeout + 기본 검증 | Docker 샌드박스 |
| **플래너** | 5단계 | 10단계 | 재귀적 DAG |
| **메타인지** | 3레벨, 키워드 | 하이브리드 (키워드+명시) | LLM 기반 판단 |
| **엘로** | 항상 활성 | 선택적 활용 | 적응적 라우팅 |
| **RUNE** | ❌ | ✅ (기초: resonance, ethical) | ✅ (완전: phase, closure) |
| **Closure** | ❌ | ✅ (Protocol 구현) | ✅ (자동화 + 시각화) |


### 6.3 Imperfect Symmetry Experiment Plan

| Slot | Focus | Parameters | Success Signals |
|------|-------|------------|-----------------|
| **E1: Residual Band Sweep** | Quantify comfort, creative, risk zones across persona cycles. | Depth=2, prompts from creative coach and resilience library, 20 runs per zone. | Residual stays within 0.15-0.35 when synthesis quality >=3.5, no safety override triggered. |
| **E2: Tool Perturbation** | Observe symmetry residue under forced planning/tool detours. | Toggle planner on/off, inject random tool at turn 2, 10 paired sessions. | Residual delta <0.1 between control and perturbed runs; document recovery latency. |
| **E3: Affect Shock Recovery** | Stress test Stage 4 with scripted affect drops. | Inject affect amplitude=0.2 at turn 3, run closure twice, 12 sessions. | Stage 4 decisions labelled "keep" in <=30% of shocks, post-closure affect >=0.4. |

**Instrumentation checklist**
- Update `persona_orchestrator` to emit `symmetry_stage`, `residual_symmetry_delta`, and `symmetry_tension` fields per turn (JSONL log).
- Extend `analysis/persona_metrics.py` with `--symmetry` flag to compute band occupancy and recovery latency.
- Capture qualitative notes in `outputs/telemetry/symmetry/README.md` to record surprise cases and manual overrides.

**Run cadence**
1. Week 2 Day 5: execute E1 (baseline) before RUNE feature freeze.
2. Week 3 Day 3: run E2 alongside metacognition upgrades; compare with baseline.
3. Week 4 Day 2: run E3 during closure rehearsal and feed findings into safety checklist.

**실행 스크립트 (E1)**실행 스크립트 (E1)**
```bash
# 1) 로그만 축적 (runs=1, depth=1 기본값)
python scripts/experiments/run_e1_residual_sweep.py --append

# 2) 밴드 분석/요약
python analysis/persona_metrics.py outputs/persona_runs/E1/*.jsonl \
  --outdir outputs/persona_metrics/E1 --symmetry --plots --band-mode --bollinger-k 1.64
```
- `--prompts-file` 옵션으로 맞춤 프롬프트 목록을 전달할 수 있습니다 (한 줄 한 프롬프트 또는 JSON 배열).
- `--config`를 지정하지 않으면 기본 PersonaRegistry 구성을 사용하며, 실험 단계에서는 echo 백엔드가 무중단 검증에 유리합니다.
- `--dry-run`으로 먼저 커맨드를 검토한 뒤 실제 실행을 진행하세요.
- `--metrics` 플래그를 함께 사용하면 실행 직후 분석까지 자동 수행하며 밴드 모드(`--band-mode`, `--bollinger-k 1.64`)를 포함합니다.

---

## 7. Next Steps

### 7.1 즉시 실행 가능한 액션

1. **환경 설정** (5분)
   ```bash
   cd D:\nas_backup
   mkdir -p scripts/{memory,evaluation,tools,safety,planning,metacognition,rune}
   mkdir -p configs outputs/{memory/sessions,closure} tests
   ```

2. **Week 1 Day 1 시작** (오늘)
   - `scripts/memory/schema.py` 구현
   - Sena의 `AGI_DESIGN_01_MEMORY_SCHEMA.md` 참고
   - JSONL 저장 로직 구현

3. **Git 초기화** (선택, 10분)
   ```bash
   git init
   git add .
   git commit -m "feat(agi): initialize AGI v1.0 project structure

   - add 7 script directories (memory, evaluation, tools, safety, planning, metacognition, rune)
   - create configs and outputs structure
   - prepare for Week 1 implementation

   Based on Sena-Lumen integrated design v1.0"
   ```

### 7.2 협업 체크포인트

**주간 리뷰**:
- Week 1 끝: 메모리 + 평가 동작 확인
- Week 2 끝: 도구 + 안전 + RUNE 기초 동작
- Week 3 끝: 플래너 + 메타인지 동작
- Week 4 끝: v1.0 릴리스 준비 완료

**일일 커밋**:
- 매일 작업 종료 시 Closure Protocol 간단 버전 실행
- `closure_report.md` 생성 (진행 상황 요약)
- Git commit으로 진행 상황 기록

### 7.3 문서 업데이트 필요

다음 문서들을 이 통합 결과 기반으로 업데이트:

1. **AGI_DESIGN_MASTER.md**
   - RUNE 섹션 추가
   - Closure Protocol 섹션 추가
   - 버전별 로드맵 업데이트

2. **README.md** (신규 작성)
   - 프로젝트 개요
   - Quick Start
   - 아키텍처 다이어그램

3. **CONTRIBUTING.md** (v1.5+)
   - 협업 방식
   - 코드 리뷰 프로세스

---

## 8. 결론

### 8.1 통합 성과

✅ **Sena의 7개 시스템 설계** (92KB)
- 좌표형 메모리, 4개 평가 지표, 5개 도구
- 안전 검증, 플래너, 메타인지, 엘로

✅ **Lumen의 검토 및 확장** (130KB)
- 9개 기술 결정 사항 해결
- RUNE 컴포넌트 추가 (공명·윤리·위상)
- Closure Protocol (루빛→세나 루프 체계화)

✅ **NotebookLM 검증**
- 32개 질문으로 실제 대화 내용과 85-100% 일치 확인

✅ **통합 문서** (현재)
- 버전별 진화 경로 명확화 (v1.0 → v1.5 → v2.0)
- 4주 로드맵 수정 및 구체화
- RUNE 통합 스크립트 명세

### 8.2 핵심 아키텍처 (최종)

```
Input (User)
  ↓
Safety Pre-Check
  ↓
Metacognition Level Selection (Session/Project/Long-term)
  ↓
Planner (max 5 steps in v1.0)
  ↓
Elo Guide (선택적, v1.5+)
  ↓
Tool Execution (규칙 기반, v1.0)
  ↓
Persona Orchestration (Thesis → Antithesis → Synthesis)
  ↓
Safety Post-Check
  ↓
Evaluation (4 metrics in v1.0, 6 in v2.0)
  ↓
**RUNE Analysis** (v1.5: resonance + ethical, v2.0: + phase)
  ↓
Memory Storage (JSONL in v1.0, SQLite in v1.5)
  ↓
**Closure Protocol** (session end)
  ↓
**Handover Sync** (session resume)
```

### 8.3 다음 마일스톤

**v1.0 목표** (4주 후):
- 기본 페르소나 오케스트레이션 동작
- 좌표형 메모리 CRUD
- 4개 평가 지표 자동 계산
- 5개 도구 기본 실행
- CLI 인터페이스

**v1.5 목표** (8주 후):
- RUNE 통합 (공명, 윤리 검증)
- Closure Protocol 자동화
- SQLite 마이그레이션
- 6개 도구 지원
- 웹 UI 프로토타입

**v2.0 목표** (12주+ 후):
- VectorDB (의미론적 검색)
- LLM 기반 도구 선택
- 재귀적 플래닝
- Docker 샌드박스
- 프랙탈 자가 교정
- 위상 도약 측정

---

**문서 버전**: v1.0
**최종 업데이트**: 2025-10-12
**작성자**: Sena + Lumen
**상태**: 구현 준비 완료 ✅

