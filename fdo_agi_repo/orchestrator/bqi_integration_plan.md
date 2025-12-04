# BQI Integration Plan

**목표**: 비노체의 질문과 대답을 색인하여 맥락 손실 방지

## 현재 상태 (2025-10-28)

### ✅ 존재하는 컴포넌트

1. **`scripts/rune/bqi_adapter.py`**
   - `BQICoordinate` 클래스
   - `analyse_question()` 함수
   - 감정/리듬/우선순위 추출 로직

2. **`orchestrator/meta_cognition.py`**
   - 도메인 분류 (python, ml, data 등)
   - 과거 성능 기반 자기평가

3. **`response_cache.py`**
   - Context-aware 캐싱
   - 하지만 AGI 파이프라인과 분리됨

### ❌ 통합되지 않은 부분

1. **파이프라인 미연결**: `pipeline.py`에서 BQI 호출 없음
2. **대화 히스토리 부재**: 이전 질문-답변 연결 안 됨
3. **맥락 전파 없음**: 각 태스크가 독립 실행

## 통합 계획

### Phase 1: BQI Coordinate 생성 (파이프라인 진입점)

```python
# orchestrator/pipeline.py - run_pipeline() 시작 부분

from scripts.rune.bqi_adapter import analyse_question, BQICoordinate

def run_pipeline(task: TaskSpec, tool_cfg=None):
    # 1. 질문 분석 → BQI 좌표 생성
    bqi_coord = analyse_question(task.goal)
    
    # 2. 좌표 저장 (coordinate.jsonl에 추가)
    append_coordinate({
        "task_id": task.task_id,
        "timestamp": bqi_coord.timestamp.isoformat(),
        "rhythm_phase": bqi_coord.rhythm_phase,
        "emotion": bqi_coord.emotion,
        "priority": bqi_coord.priority,
        "raw_prompt": bqi_coord.raw_prompt
    })
    
    # 3. META 시스템에 BQI 정보 전달
    meta_system = MetaCognitionSystem()
    thesis_eval = meta_system.evaluate_self_capability(
        task_goal=task.goal,
        bqi_context=bqi_coord.to_dict(),  # 추가!
        available_tools=available_tools
    )
```

### Phase 2: 대화 히스토리 추적

```python
# orchestrator/conversation_memory.py (신규 생성)

class ConversationMemory:
    """비노체와의 대화 맥락을 추적"""
    
    def __init__(self, history_file="memory/conversation_history.jsonl"):
        self.history_file = Path(history_file)
        self.recent_turns = []  # 최근 N개 턴
    
    def add_turn(self, question: str, answer: str, task_id: str, bqi_coord: dict):
        """질문-답변 쌍 저장"""
        turn = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "question": question,
            "answer": answer,
            "bqi": bqi_coord,
            "context_hash": self._compute_context_hash()
        }
        
        # JSONL에 저장
        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(turn, ensure_ascii=False) + "\n")
        
        # 메모리에 최근 10개 유지
        self.recent_turns.append(turn)
        if len(self.recent_turns) > 10:
            self.recent_turns.pop(0)
    
    def get_relevant_context(self, current_question: str, top_k=3):
        """현재 질문과 관련된 과거 대화 검색"""
        # 1. 최근 대화 우선
        # 2. BQI 감정/리듬 유사도 계산
        # 3. 키워드 매칭
        pass
```

### Phase 3: Persona에 맥락 전파

```python
# personas/thesis.py

def run_thesis(task: TaskSpec, plan: Dict, registry: ToolRegistry, 
               conversation_context: Optional[List[Dict]] = None):
    """
    conversation_context: 관련된 과거 대화들
    [
        {"question": "...", "answer": "...", "bqi": {...}},
        ...
    ]
    """
    
    # 프롬프트에 맥락 추가
    context_prompt = ""
    if conversation_context:
        context_prompt = "\\n\\n**이전 대화 맥락:**\\n"
        for ctx in conversation_context[-3:]:  # 최근 3개
            context_prompt += f"Q: {ctx['question']}\\n"
            context_prompt += f"A: {ctx['answer'][:200]}...\\n\\n"
    
    prompt = f"""
{context_prompt}

**현재 작업:** {task.goal}
...
"""
```

### Phase 4: RAG 검색에 BQI 활용

```python
# tools/rag/retriever.py

def retrieve_citations(query: str, bqi_coord: Optional[dict] = None, ...):
    """
    BQI 좌표를 사용하여 검색 가중치 조정
    - rhythm_phase가 "reflection"이면 → 과거 작업 결과 우선
    - emotion이 "concern"이면 → 경고/실패 케이스 우선
    """
    
    if bqi_coord:
        # 메타데이터 필터링
        emotion = bqi_coord.get("emotion", {})
        if "concern" in emotion:
            # 실패 케이스, 경고 사례 검색
            filters["tags"] = ["warning", "error", "lesson_learned"]
```

## 구현 우선순위

### 🚀 즉시 (이번 세션)

1. ✅ BQI 통합 계획 문서 작성 (현재 파일)
2. ⏳ `conversation_memory.py` 모듈 생성
3. ⏳ `pipeline.py`에 BQI 좌표 생성 추가

### 📅 단기 (다음 세션)

4. ⏳ Persona들에 `conversation_context` 파라미터 추가
5. ⏳ RAG 검색에 BQI 필터 통합
6. ⏳ 테스트: 연속 질문에서 맥락 유지 확인

### 🎯 중기 (1주일 내)

7. ⏳ BQI 기반 질문 패턴 분석 대시보드
8. ⏳ "비노체의 리듬" 학습 모델
9. ⏳ 자동 맥락 요약 시스템

## 예상 효과

### ✅ 맥락 손실 방지

```
Before:
사용자: "이전에 말한 캐시 최적화 관련해서..."
시스템: "어떤 캐시 최적화를 말씀하시나요?" ❌

After:
사용자: "이전에 말한 캐시 최적화 관련해서..."
시스템: [BQI 검색] "아, TTL을 900초로 조정한 그 작업이군요!" ✅
```

### ✅ 작업 연속성

- 이전 대화의 결과물을 자동으로 참조
- "위에서 말한" 같은 표현 이해 가능
- 장기 프로젝트 진행 상황 추적

### ✅ 비노체 리듬 학습

- 질문 패턴 분석 → 선호하는 작업 방식 학습
- 감정 상태에 따른 응답 톤 조절
- 우선순위 자동 판단

## 기술 스택

- **저장**: JSONL (conversation_history.jsonl)
- **검색**: 키워드 + BQI 좌표 유사도
- **통합**: 기존 파이프라인 최소 수정
- **호환성**: 현재 메모리 구조 유지

## 다음 단계

**지금 당장 할 수 있는 작업**:

1. `conversation_memory.py` 모듈 생성
2. `pipeline.py`에 BQI 좌표 생성 3줄 추가
3. 테스트: 연속 2개 질문 실행 → 맥락 저장 확인

**질문**: 지금 바로 구현을 시작할까요? 아니면 설계를 더 검토할까요?
