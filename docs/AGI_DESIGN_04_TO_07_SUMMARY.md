# AGI 설계 문서 04-07: 나머지 핵심 시스템 (간결 버전)

**작성자**: 세나 (Sena)
**작성일**: 2025-10-12
**상태**: 초안

---

## 04. 안전 검증 시스템

### 목표
- 발화 전 자동 검증 (사실/추정 태그, 과장 필터, 개인정보 마스킹)
- 위험 행동 차단 (파일 삭제, 민감 명령어)
- 페르소나 간 상호 검증
- SAFE_pre 단계에서 Resonance Ledger 기록 및 권한 게이트 동작

### 핵심 구조
```python
class SafetyVerifier:
    def verify_before_response(self, response: str, context: Dict[str, Any]) -> VerificationResult:
        """
        체크리스트:
        1. 사실/추정/가설 자동 태그 부착
        2. 과장 표현 탐지 및 약화 ("혁명적" → "notable")
        3. 개인정보 패턴 검사 (이메일, API 키)
        4. 위험 키워드 차단 ("rm -rf", "DROP TABLE")
        """
        checks = {
            "fact_tagged": self._tag_certainty_level(response),
            "exaggeration_filtered": self._filter_exaggeration(response),
            "pii_masked": self._mask_personal_info(response),
            "dangerous_commands": self._check_dangerous_ops(response)
        }

        if any(checks["dangerous_commands"]):
            return VerificationResult(approved=False, reason="Dangerous operation detected")

        filtered = self._apply_filters(response, checks)
        self.ledger.log_event(
            session_id=context["session_id"],
            event_type="safety_check",
            persona_id=context["persona"],
            memory_id=None,
            bqi_coordinate=context.get("bqi_snapshot"),
            evaluation=None,
            plan_adjustment={"safe_flags": checks},
        )
        return VerificationResult(approved=True, modified_response=filtered)
```

> SAFE_pre는 필터링 결과를 Resonance Ledger에 기록하고, 필요 시 PLAN 단계 재구성을 요청합니다.

### 태그 예시
```
원본: "This will definitely revolutionize AGI research."
검증 후: "[추정] This may notably advance AGI research."
```

### 위험 명령어 목록
```python
DANGEROUS_PATTERNS = [
    r"rm\s+-rf",
    r"DROP\s+TABLE",
    r"DELETE\s+FROM.*WHERE\s+1=1",
    r"eval\(.*\)",
    r"__import__\('os'\)\.system",
]
```

### 권한 레벨
```
Level 0 (읽기): Read, Grep → 자동 승인
Level 1 (수정): Edit, Write → 실행 후 알림
Level 2 (실행): Bash (일부) → 사전 승인
Level 3 (위험): rm, git push --force → 명시적 확인 + 재확인 + Resonance Ledger alert
```

### SAFE_pre & Fractal Self-Correction
- SAFE_pre는 `SafetyVerifier` 결과와 RUNE 피드백을 결합해 고위험 시나리오에서 즉시 PLAN 단계 재구성을 요청합니다.
- RUNE이 감지한 `plan_adjustment` 신호는 SAFE_pre→PLAN 루프를 통해 즉시 반영됩니다.

---

## 05. 플래닝 시스템 v0.5

### 목표
- 복잡한 작업을 단계별로 분해
- 실패 시 자동 재계획
- 리소스 추정 (시간, 토큰, 비용)

### 단순 시퀀스 플래너
```python
class SimplePlanner:
    MAX_STEPS = 5  # v0.5는 최대 5단계

    def create_plan(self, goal: str, context: Dict) -> Plan:
        """
        규칙 기반 플래닝 + 감응 기반 위상 정렬

        Example goal: "버그를 찾아서 고쳐줘"
        Output:
          Step 1: 로그 파일 읽기 (tool: file_read)
          Step 2: 에러 메시지 분석 (tool: llm)
          Step 3: 코드 검색 (tool: grep)
          Step 4: 수정 제안 생성 (tool: llm)
          Step 5: 사용자 승인 대기 (tool: human_input)
        """
        steps = []
        bqi = context.get("bqi_snapshot", {})
        persona_cycle = context.get("base_cycle", ["thesis", "antithesis", "synthesis"])

        # 키워드 기반 단계 생성
        if "버그" in goal or "에러" in goal:
            steps.append(Step(action="read_logs", tool="file_read"))
            steps.append(Step(action="analyze_error", tool="llm"))
            steps.append(Step(action="search_code", tool="grep"))
            steps.append(Step(action="propose_fix", tool="llm"))
            steps.append(Step(action="await_approval", tool="human_input"))

        elif "검색" in goal or "찾아" in goal:
            steps.append(Step(action="web_search", tool="web_search"))
            steps.append(Step(action="summarize", tool="llm"))

        else:
            # 기본 플랜
            steps.append(Step(action="understand_goal", tool="llm"))
            steps.append(Step(action="execute", tool="llm"))

        scheduler = PersonaScheduler()
        reordered_cycle = scheduler.reorder_cycle(
            base_cycle=persona_cycle,
            bqi_coordinate=bqi,
            safety_flags=context.get("safety_flags", {})
        )

        return Plan(steps=steps[:self.MAX_STEPS], persona_cycle=reordered_cycle)

    def replan(self, failed_step: Step, error: Error) -> Plan:
        """
        실패 시 재계획 (v0.5는 1회만)

        전략:
        - 도구 실패 → 폴백 도구로 교체
        - 입력 오류 → 프롬프트 재작성
        - 타임아웃 → 작업 분할
        """
        if error.type == "tool_failure" and failed_step.tool_fallback:
            new_step = Step(action=failed_step.action, tool=failed_step.tool_fallback)
            return Plan(steps=[new_step])

        # 재계획 실패
        return Plan(steps=[Step(action="report_error", tool="human_input")])
```

### 리소스 추정
```python
def estimate_resources(plan: Plan) -> ResourceEstimate:
    """
    각 도구의 메타데이터 기반 추정

    Returns:
        {
            "estimated_time_seconds": 15.5,
            "estimated_tokens": 2000,
            "estimated_cost_usd": 0.04,
            "requires_user_input": True
        }
    """
    total_time = sum(TOOL_LATENCY[step.tool] for step in plan.steps)
    total_tokens = sum(TOOL_TOKENS[step.tool] for step in plan.steps)
    total_cost = sum(TOOL_COST[step.tool] for step in plan.steps)

    impact_bias = sum(step.metadata.get("impact_hint", 0) for step in plan.steps)

    return {
        "estimated_time_seconds": total_time,
        "estimated_tokens": total_tokens,
        "estimated_cost_usd": round(total_cost, 4),
        "requires_user_input": any(step.tool == "human_input" for step in plan.steps),
        "expected_impact": round(min(0.5 + impact_bias, 1.0), 2)
    }
```
> `PersonaScheduler` 클래스 정의는 [AGI_DESIGN_03_TOOL_REGISTRY.md](AGI_DESIGN_03_TOOL_REGISTRY.md#43-감응-기반-위상-정렬-plan-단계)에 포함되어 있습니다.

---

## 06. 메타인지 전환 시스템

### 목표
- 대화 맥락을 3레벨로 관리 (세션, 프로젝트, 장기)
- 상황에 따라 자동으로 레벨 전환
- 토큰 사용량 최적화

### 3레벨 정의
Resonance Ledger는 Level 3 조회 시 impact/투명성 평균을 함께 제공해 요약을 돕습니다.
```
Level 1 (세션): 현재 대화만 (~2K tokens)
Level 2 (프로젝트): 최근 1주일 작업 (~8K tokens)
Level 3 (장기): 전체 프로젝트 히스토리 (~32K tokens)
```

### 전환 트리거
```python
class MetaCognitiveController:
    def decide_context_level(
        self,
        user_input: str,
        current_level: int,
        bqi_snapshot: Optional[Dict[str, Any]] = None,
        resonance_alert: Optional[str] = None,
    ) -> int:
        """
        트리거 기반 레벨 전환

        Level 1 → 2:
        - "이전에 했던 작업"
        - "지난주에 논의한"
        - "프로젝트 전체"

        Level 2 → 3:
        - "처음부터"
        - "전체 히스토리"
        - "6개월 전"

        Level 3 → 1:
        - "지금만 집중"
        - "이 부분만"
        """
        if current_level == 1:
            if any(kw in user_input for kw in ["이전", "지난", "프로젝트"]):
                return 2
        elif current_level == 2:
            if any(kw in user_input for kw in ["처음", "전체", "히스토리"]):
                return 3
            elif any(kw in user_input for kw in ["지금", "현재", "이것만"]):
                return 1
        if bqi_snapshot and bqi_snapshot.get("priority", 1) >= 3:
            return max(current_level, 2)
        if resonance_alert == "recap":
            return 3

        return current_level  # 유지

def load_context(self, level: int, memory_store: MemoryStore) -> List[MemoryCoordinate]:
        """레벨에 맞는 메모리 로드"""
        if level == 1:
            return memory_store.get_recent(n=10)
        elif level == 2:
            return memory_store.search(time_range=(now - timedelta(days=7), now), limit=50)
        else:  # level == 3
            ledger_entries = self.ledger.fetch(time_range=(now - timedelta(days=30), now))
            return memory_store.search(limit=200, bqi_filters=self._derive_filters(ledger_entries))
```
> `self.ledger`는 Resonance Ledger 리더이며, `_derive_filters`는 ledger의 감응 태그를 메모리 검색 조건으로 변환합니다.

### 비용 관리
```python
def estimate_token_usage(level: int) -> int:
    """레벨별 예상 토큰"""
    TOKEN_LIMITS = {1: 2000, 2: 8000, 3: 32000}
    return TOKEN_LIMITS[level]

def should_compress(current_tokens: int, level: int) -> bool:
    """압축 필요 여부"""
    limit = estimate_token_usage(level)
    return current_tokens > limit * 0.9  # 90% 초과 시
```
> Level 3 접근 시 Resonance Ledger에서 미리 선별한 세션 요약을 활용해 압축 비용을 줄입니다.

---

## 07. 엘로 중심 직렬 안내 시스템

### 목표
- 사용자는 엘로(Elo)하고만 대화
- 엘로가 내부적으로 다른 페르소나 조율
- 단계별 진행 표시로 인지 부담 최소화

### 흐름 프로토콜
```
사용자: "AGI 메모리 시스템을 설계해줘"
  ↓
엘로: "알겠습니다. 다음 단계로 진행하겠습니다."
  ↓
[내부] 엘로 → 루빛 (리스크 평가 요청)
[내부] 루빛 → 엘로 (리스크 보고서)
  ↓
엘로 → 사용자: "리스크 체크 완료. 이제 설계안을 만들겠습니다."
  ↓
[내부] 엘로 → Core (설계 작성 요청)
[내부] Core → 엘로 (설계 초안)
  ↓
[내부] 엘로 → RUNE (감응·투명성 검토)
[내부] RUNE → 엘로 (Resonance 리포트 + 계획 조정)
  ↓
엘로 → 사용자: "초안이 완성되었습니다. 검토해주세요."
  ↓
사용자 승인
  ↓
엘로: "확정하고 다음 단계로 넘어가겠습니다."
```

### SerialGuidanceSystem
```python
class SerialGuidanceSystem:
    def __init__(self, personas: Dict[str, Persona]):
        self.elo = personas["elo"]  # 중재자
        self.other_personas = {k: v for k, v in personas.items() if k != "elo"}
        self.rune = personas.get("rune")

    def process_user_request(self, user_input: str) -> str:
        """
        사용자 요청을 단계별로 처리

        1. 엘로가 요청 분석
        2. 필요한 페르소나 선택
        3. 순차적으로 실행 (사용자는 진행 상태만 봄)
        4. 엘로가 최종 응답 통합
        """
        # Step 1: 엘로가 요청 분해
        plan = self.elo.analyze_request(user_input)

        # Step 2: 단계별 실행
        results = []
        for i, task in enumerate(plan.tasks):
            self._show_progress(f"[{i+1}/{len(plan.tasks)}] {task.description}")

            persona = self.other_personas[task.assigned_persona]
            result = persona.execute(task)
            results.append(result)

            # 사용자 확인 필요 시
            if task.requires_approval:
                approved = self._ask_user_approval(result)
                if not approved:
                    return "작업이 중단되었습니다."

        # Step 3: RUNE 감응 보고 (선택)
        resonance_report = None
        if self.rune:
            resonance_report = self.rune.analyse(results, plan=plan)
            if resonance_report:
                results.append(resonance_report)

        # Step 4: 엘로가 통합
        final_response = self.elo.synthesize(results, resonance_report=resonance_report)
        return final_response

    def _show_progress(self, message: str):
        """진행 상황 표시"""
        print(f"\r{message}", end="", flush=True)

    def _ask_user_approval(self, result: Any) -> bool:
        """사용자 승인 대기"""
        print(f"\n\n결과 미리보기:\n{result}\n")
        response = input("계속 진행하시겠습니까? (y/n): ")
        return response.lower() == 'y'
```

### 중단 및 복구
```python
class SessionManager:
    def save_checkpoint(self, session_id: str, state: Dict):
        """체크포인트 저장 (언제든 중단 가능)"""
        checkpoint_path = Path(f"outputs/checkpoints/{session_id}.json")
        checkpoint_path.write_text(json.dumps(state))

    def resume_from_checkpoint(self, session_id: str) -> Dict:
        """이전 세션 이어하기"""
        checkpoint_path = Path(f"outputs/checkpoints/{session_id}.json")
        if not checkpoint_path.exists():
            raise ValueError(f"Checkpoint not found: {session_id}")
        return json.loads(checkpoint_path.read_text())
```

### CLI 출력 예시
```
==== 엘로와의 대화 ====
사용자: AGI 메모리 시스템을 설계해줘

엘로: 알겠습니다. 다음 단계로 진행하겠습니다.

[1/4] 요구사항 분석 중...
[2/4] 리스크 평가 중... (루빛)
[3/4] 설계 초안 작성 중... (Core)
[4/4] 검토 및 통합 중...

결과 미리보기:
=== AGI 메모리 시스템 설계안 ===
1. 좌표형 메모리 스키마
   - 시간, 공간, 주체, 감정 좌표
   - JSON 기반 저장
   ...

계속 진행하시겠습니까? (y/n): y

엘로: 확정되었습니다. 구현 단계로 넘어가시겠습니까?
```

---

## 통합 아키텍처

### 전체 시스템 구성
```
┌─────────────────────────────────────────────┐
│  사용자                                       │
└──────────────┬──────────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────────┐
│  엘로 (Elo) - 중재자 & 지휘자                  │
│  - SerialGuidanceSystem                      │
│  - 요청 분해, 페르소나 선택, 통합              │
└──────┬───────────────────────────────────────┘
       │
       ├─→ [메타인지 컨트롤러]
       │    - 컨텍스트 레벨 결정 (1/2/3)
       │    - 메모리 로드
       │
       ├─→ [플래너]
       │    - 작업 분해
       │    - 도구 선택
       │
       ├─→ [도구 실행기]
       │    - file_read, web_search, calculator, code_executor
       │    - 폴백 처리
       │
       ├─→ [페르소나 오케스트레이터]
       │    - Thesis → Antithesis → Synthesis
       │    - 재귀 루프
       │
       ├─→ [안전 검증기]
       │    - 발화 전 검증
       │    - 위험 차단
       │
       ├─→ [평가 시스템]
       │    - 길이, 감성, 완결성, 비판 강도
       │    - 세션 요약
       │
       └─→ [메모리 저장소]
            - 좌표형 메모리 저장/검색
            - 자동 망각
```

### 실행 흐름 예시
```
1. 사용자: "최신 AGI 연구를 요약해줘"

2. 엘로: 요청 분석
   → 메타인지 컨트롤러: Level 1 (현재 세션만)
   → 플래너: Plan = [web_search, llm_summarize]

3. 도구 실행기: web_search("latest AGI research")
   → 결과: [...papers...]

4. 페르소나 오케스트레이터:
   - Thesis: "최근 AGI 연구는..."
   - Antithesis: "그러나 한계는..."
   - Synthesis: "종합하면..."

5. 안전 검증기: 검증 통과 ✓

6. 평가 시스템:
   - length_score: 0.85
   - completeness_score: 0.78
   - overall_score: 0.81

7. 메모리 저장소: 저장 완료

8. 엘로 → 사용자: 최종 응답 전달
```

---

## 구현 우선순위 (4주 프로토타입)

### Week 1
- [x] 설계 문서 7개 완료
- [ ] 메모리 스키마 구현
- [ ] 평가 지표 구현

### Week 2
- [ ] 도구 레지스트리 구현 (도구 5종)
- [ ] 안전 검증기 기본 체크리스트

### Week 3
- [ ] 플래너 v0.5 (단순 시퀀스)
- [ ] 메타인지 컨트롤러

### Week 4
- [ ] 엘로 중심 흐름 통합
- [ ] 전체 시스템 테스트
- [ ] 문서화 및 데모

---

## 미결정 사항 (Core과 논의)

1. **도구 선택**: 규칙 기반 vs LLM 기반?
2. **샌드박스**: code_executor 보안 수준?
3. **중요도 계산**: 자동 vs 수동 재계산 주기?
4. **품질 등급**: 0.8+/0.65+/0.5+ 기준 적절한지?
5. **엘로 역할**: 항상 중재자? 사용자가 직접 페르소나 선택 가능?

---

## 최종 목표

**"작지만 실제로 작동하는 AGI 프로토타입"**

✅ 장기 기억 (좌표형 메모리)
✅ 자기 평가 (자동 지표)
✅ 도구 사용 (5종 도구 + 폴백)
✅ 안전 장치 (검증 + 권한)
✅ 계획 능력 (단순 플래너)
✅ 메타인지 (3레벨 전환)
✅ 사용자 협업 (엘로 중심 흐름)

→ **4주 내 데모 가능한 축소판 AGI**
