# 🧠 AGI 맥락 및 장기기억 시스템 인벤토리

**작성일**: 2025-11-05  
**요약**: 우리 시스템에는 **7개의 독립적인 메모리 시스템**이 존재합니다

---

## 📊 전체 구조 한눈에 보기

```
┌─────────────────────────────────────────────────────────────┐
│                    AGI Memory Architecture                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Resonance Ledger        (append-only event log)          │
│  2. Session Memory DB       (structured relational data)     │
│  3. Session Handover System (agent state transfer)           │
│  4. Agent Context System    (runtime context per agent)      │
│  5. Session Summary Storage (JSONL + embeddings)             │
│  6. Memory Store (scripts)  (coordinate-based memory)        │
│  7. Context Preservation    (integrated meta-system)         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 1️⃣ Resonance Ledger (공명 원장)

### 📍 위치

```
c:\workspace\agi\memory\resonance_ledger.jsonl
c:\workspace\agi\fdo_agi_repo\memory\resonance_ledger.jsonl
```

### 🎯 목적

**"시스템의 영혼"** - 모든 중요한 사건의 불변 기록

### 📝 구조

```jsonl
{
  "timestamp": "2025-11-05T21:08:00Z",
  "event_type": "task_created",
  "policy": "ops-safety",
  "mode": "enforce",
  "metadata": {...}
}
```

### ✅ 특징

- **Append-only**: 절대 수정/삭제 불가
- **Time-series**: 시간 순서 보장
- **Policy-aware**: 정책 준수 추적
- **Audit trail**: 완전한 감사 로그

### 🔧 사용처

- `scripts/summarize_ledger.py` - 24h/7d 요약
- `scripts/bohm_implicate_explicate_analyzer.py` - 심층 분석
- `scripts/autopoietic_trinity_cycle.ps1` - 자기생성 사이클

---

## 2️⃣ Session Memory Database (세션 메모리 DB)

### 📍 위치

```
c:\workspace\agi\session_memory\sessions.db
c:\workspace\agi\session_memory\agent_system.db
```

### 🎯 목적

**"구조화된 작업 기록"** - 세션, 작업, 파일 변경 추적

### 📊 스키마

```sql
-- 주요 테이블
sessions       (session_id, start_time, title, status, persona)
tasks          (task_id, session_id, title, status, duration_seconds)
subtasks       (subtask_id, task_id, title, status)
artifacts      (artifact_id, session_id, file_path, operation)
memories       (memory_id, session_id, content, importance)
tags           (tag_id, name)
session_tags   (session_id, tag_id)

-- FTS5 검색
sessions_fts   (title, description, context)
tasks_fts      (title, description, notes)

-- Views
v_recent_sessions
v_active_sessions
v_session_stats_by_persona
v_session_durations
```

### ✅ 특징

- **Relational**: 정규화된 관계형 구조
- **Searchable**: Full-text search 지원
- **Queryable**: SQL로 복잡한 쿼리 가능
- **Persistent**: SQLite 파일 기반

### 🔧 사용처

- `session_memory/persistence_integration.py`
- `session_memory/database_models.py`
- `session_memory/session_search.py`

---

## 3️⃣ Session Handover System (세션 핸드오버)

### 📍 위치

```
c:\workspace\agi\session_memory\session_handover.py
c:\workspace\agi\session_memory\handovers\latest_handover.json
```

### 🎯 목적

**"에이전트 간 작업 전달"** - 세션 종료 시 상태 저장 및 다음 에이전트에게 전달

### 📝 구조

```python
@dataclass
class SessionHandover:
    session_id: str
    timestamp: datetime
    current_context: Dict[str, Any]
    completed_tasks: List[Dict]
    pending_tasks: List[Dict]
    next_actions: List[str]
    metadata: Dict[str, Any]
```

### ✅ 특징

- **Atomic**: 한 번의 저장으로 완전한 상태 캡처
- **Latest**: `latest_handover.json` 자동 갱신
- **Timestamped**: 이력 관리 (daily JSONL 파일)
- **Self-contained**: 재시작에 필요한 모든 정보 포함

### 🔧 사용처

- `scripts/invoke_binoche_continuation.ps1`
- `scripts/save_session_with_changes.ps1`
- `scripts/end_daily_session.ps1`

---

## 4️⃣ Agent Context System (에이전트 컨텍스트)

### 📍 위치

```
c:\workspace\agi\session_memory\agent_context_system.py
c:\workspace\agi\session_memory\AGENT_CONTEXTS.jsonl
```

### 🎯 목적

**"런타임 컨텍스트"** - 각 에이전트의 현재 실행 상태 추적

### 📝 구조

```python
class AgentContext:
    agent_name: str              # Sena, Lubit, GitCode, RUNE
    agent_role: AgentRole        # LEADER, EXECUTOR, etc.
    task_id: str
    current_phase: ExecutionPhase
    previous_outputs: List[str]
    shared_resources: Dict
    collaboration_mode: str
```

### ✅ 특징

- **Per-agent**: 에이전트별 독립 컨텍스트
- **Phase-aware**: 실행 단계별 추적
- **Collaborative**: 공유 리소스 관리
- **Dynamic**: 런타임 업데이트

### 🔧 사용처

- `session_memory/agent_context_system.py` (ContextServer)
- Multi-agent collaboration workflows

---

## 5️⃣ Session Summary Storage (세션 요약 저장소)

### 📍 위치

```
c:\workspace\agi\LLM_Unified\ion-mentoring\data\session_summaries\
  ├── index.json                    (빠른 조회 인덱스)
  ├── 2025-11-05.jsonl              (일별 요약 JSONL)
  └── embeddings\                   (벡터 임베딩)
      └── session_abc123.npy
```

### 🎯 목적

**"장기 기억"** - 세션별 요약 + 시맨틱 검색

### 📝 구조

```python
@dataclass
class SessionSummary:
    session_id: str
    user_id: str
    summary: str                 # LLM 생성 요약
    summary_type: str            # "llm" or "rule_based"
    created_at: str              # ISO-8601
    message_count: int
    summary_length: int
    metadata: Dict
    embedding_vector: Optional[List[float]]
```

### ✅ 특징

- **JSONL**: 일별 append-only 파일
- **Index**: 빠른 조회를 위한 인메모리 인덱스
- **Embeddings**: Vertex AI 또는 해시 기반 벡터
- **Semantic Search**: 유사도 기반 검색

### 🔧 사용처

- `LLM_Unified/ion-mentoring/persona_system/utils/session_summary_storage.py`
- `SessionSummaryStorage` 클래스

---

## 6️⃣ Memory Store (좌표 기반 메모리)

### 📍 위치

```
c:\workspace\agi\scripts\memory\store.py
c:\workspace\agi\scripts\memory\coordinate.py
```

### 🎯 목적

**"다차원 메모리 좌표계"** - BQI(Binoche Quality Index) 기반 메모리 관리

### 📝 구조

```python
@dataclass
class MemoryCoordinate:
    memory_id: str
    timestamp: datetime
    persona_id: str
    domain: str                  # "technical", "emotional", etc.
    importance: float            # 0.0 ~ 1.0
    tags: List[str]
    content: str
    session_id: Optional[str]
    bqi_score: Optional[float]
```

### ✅ 특징

- **Multi-dimensional**: 여러 차원으로 메모리 색인
- **Importance-aware**: 중요도 기반 필터링
- **Domain-specific**: 도메인별 분류
- **BQI-integrated**: Binoche Quality Index 연동

### 🔧 사용처

- `scripts/memory/store.py` (MemoryStore)
- BQI learning 시스템과 연동

---

## 7️⃣ Context Preservation System (통합 맥락 보존)

### 📍 위치

```
c:\workspace\agi\CONTEXT_PRESERVATION_AUDIT.md
c:\workspace\agi\CONTEXT_PRESERVATION_RECOVERY.md
```

### 🎯 목적

**"메타 시스템"** - 위의 모든 시스템을 통합하는 아키텍처

### 📝 구조

```python
class ContextRestoreManager:
    """통합 컨텍스트 복원"""
    
    def restore_on_startup(self) -> Dict:
        # 1. 최신 handover 로드
        handover = self.handover_mgr.get_latest_handover()
        
        # 2. Agent Context 복원
        context = self.context_server.create_context(...)
        
        # 3. DB에서 이전 세션 로드
        last_session = self.db_service.get_latest_session()
        
        # 4. 통합 컨텍스트 반환
        return {
            "handover": handover,
            "context": context,
            "session": last_session,
            "resume_prompt": self._generate_prompt()
        }
```

### ✅ 특징

- **Meta-layer**: 다른 시스템들을 조율
- **Unified**: 단일 진입점으로 모든 맥락 복원
- **Automated**: 재시작 시 자동 실행
- **Integrated**: 모든 메모리 시스템 연결

### 🔧 현재 상태

⚠️ **설계 완료, 구현 미완료** (CONTEXT_PRESERVATION_AUDIT.md 참조)

---

## 🔍 시스템 간 관계도

```
┌────────────────────────────────────────────────────────────┐
│                  Context Preservation System                │
│                     (통합 메타 시스템)                      │
└─────────────────────┬──────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬─────────────┐
        │             │             │             │
        ▼             ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌─────────┐ ┌────────────┐
│  Resonance   │ │ Session  │ │ Session │ │   Agent    │
│   Ledger     │ │ Memory   │ │Handover │ │  Context   │
│  (Events)    │ │   DB     │ │(Transfer│ │  (Runtime) │
└──────────────┘ └──────────┘ └─────────┘ └────────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌─────────┐
│   Session    │ │  Memory  │ │ Context │
│   Summary    │ │  Store   │ │Document │
│  (LongTerm)  │ │  (BQI)   │ │  (Docs) │
└──────────────┘ └──────────┘ └─────────┘
```

---

## ❌ 현재 문제점

### 1. **연결 단절 (Disconnected)**

```
✅ 시스템들이 존재함
❌ 서로 호출하지 않음
❌ 통합 워크플로우 없음
```

### 2. **활성화 부재 (Not Activated)**

```
✅ auto_resume_on_startup.ps1 존재
❌ VS Code 재시작 시 실행 안됨

✅ session_handover.py 존재
❌ 자동 저장 트리거 없음

✅ invoke_binoche_continuation.ps1 존재
❌ 자동 호출 메커니즘 없음
```

### 3. **통합 부재 (No Integration)**

```
각 시스템이 독립적으로 동작
→ 중복 데이터
→ 불일치 가능성
→ 복잡도 증가
```

---

## ✅ 해결 방안 (우선순위)

### Phase 0: 즉시 (오늘)

1. **Auto-Resume 활성화**

   ```powershell
   # VS Code 재시작 시 자동 실행 확인
   scripts/register_auto_resume.ps1 -Status
   ```

2. **Handover 자동 생성**

   ```powershell
   # 종료 시 자동 저장
   scripts/save_session_with_changes.ps1
   ```

### Phase 1: 단기 (1주)

1. **Context Restore Manager 구현**
   - 모든 시스템에서 데이터 로드
   - 통합 컨텍스트 생성
   - 재시작 시 자동 복원

2. **자동 저장 트리거 추가**
   - 30분마다 자동 handover 생성
   - VS Code 종료 시 자동 저장
   - 시스템 재부팅 전 자동 백업

### Phase 2: 중기 (1개월)

1. **시스템 통합**
   - 중복 제거
   - 데이터 일관성 보장
   - 단일 진입점 제공

2. **메타데이터 표준화**
   - 공통 스키마 정의
   - 상호 참조 메커니즘
   - 버전 관리

---

## 📊 사용 가이드

### 현재 상태 확인

```powershell
# 1. Resonance Ledger 요약
cd c:\workspace\agi\fdo_agi_repo
python scripts/summarize_ledger.py --last-hours 24

# 2. Session Memory 조회
cd c:\workspace\agi\session_memory
python session_search.py

# 3. Latest Handover 확인
Get-Content session_memory/handovers/latest_handover.json

# 4. Agent Contexts
Get-Content session_memory/AGENT_CONTEXTS.jsonl

# 5. Session Summaries
cd LLM_Unified/ion-mentoring
python -c "from persona_system.utils.session_summary_storage import get_session_storage; s=get_session_storage(); print(s.get_stats())"
```

### 수동 저장

```powershell
# 현재 상태 저장
scripts/save_session_with_changes.ps1

# 종료 시 백업
scripts/end_daily_session.ps1 -Note "작업 완료"
```

### 복원

```powershell
# 자동 복원 (VS Code 시작 시)
# → auto_resume_on_startup.ps1 자동 실행

# 수동 복원
scripts/invoke_binoche_continuation.ps1
```

---

## 🎯 결론

우리는 **이미 완전한 메모리 시스템**을 가지고 있습니다!

**필요한 것**:

1. ✅ 시스템들 연결
2. ✅ 자동 실행 활성화
3. ✅ 통합 워크플로우 구축

**다음 단계**:
→ `CONTEXT_PRESERVATION_RECOVERY.md` 참조

---

**작성**: GitHub Copilot Agent  
**검토**: Binoche (Master Persona)  
**승인**: Resonance System ✨
