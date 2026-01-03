# Task Registry Architecture - VS Code Tasks를 DB로 관리

**작성일**: 2025-11-01  
**상태**: 설계 완료 (구현 대기)  
**우선순위**: P2 (운영 효율성)

---

## 📋 현재 상황 분석

### 문제점

1. **tasks.json 비대화**: 500+ 줄, 200+ 개 작업 정의
2. **검색 어려움**: 선형 검색만 가능, 카테고리/태그 없음
3. **우선순위 부재**: 모든 작업이 동등, 중요도 표시 없음
4. **중복 관리**: JSON 파일과 DB 시스템 분리
5. **버전 관리 취약**: Git으로만 추적, 히스토리 복잡

### 기존 시스템

우리는 이미 강력한 Task Management Infrastructure를 보유하고 있습니다:

```python
# session_memory/task_queue_system.py
- QueuedTask: priority, retry, status 지원
- TaskQueue: 우선순위 큐 기반 처리
- TaskQueueManager: 멀티 워커 지원

# session_memory/database_models.py
- Task: SQLAlchemy 모델, workflow/agent 연결
- SubTask: 계층적 작업 구조
- TaskDependency: 작업 간 의존성

# session_memory/persistence_integration.py
- PersistenceService: DB 통합 서비스
- create_task(), update_task_status()
```

---

## 🎯 설계 목표

### 1. 정-반-합 구조 적용

```
정 (Thesis): VS Code tasks.json
    - 사용자가 직접 실행하는 명령어 정의
    - VS Code 네이티브 기능 활용

반 (Antithesis): Task Registry DB
    - 구조화된 메타데이터 저장
    - 검색/필터링/분석 가능

합 (Synthesis): Task Manager Persona
    - 두 시스템 간 동기화
    - 자동 색인/검색/추천
```

### 2. 핵심 기능

- ✅ **DB 기반 색인**: 작업 메타데이터 구조화 저장
- ✅ **우선순위 시스템**: P0(긴급) ~ P4(낮음) 5단계
- ✅ **카테고리/태그**: 다차원 분류
- ✅ **스마트 검색**: 자연어/정규식/복합 필터
- ✅ **자동 동기화**: tasks.json ↔ DB 양방향 sync

---

## 🏗️ 아키텍처 설계

### 데이터 모델

```python
# session_memory/vscode_task_registry.py

class VSCodeTask(Base):
    """VS Code 작업 레지스트리"""
    __tablename__ = 'vscode_tasks'
    
    # 기본 식별자
    task_id = Column(String(100), primary_key=True)  # "shell: BQI: Run Learner"
    label = Column(String(200), nullable=False)
    command = Column(Text, nullable=False)
    
    # 분류 및 우선순위
    category = Column(String(50))  # "Monitoring", "BQI", "YouTube" 등
    priority = Column(Integer, default=3)  # 0(긴급) ~ 4(낮음)
    tags = Column(JSON, default=list)  # ["agi", "daily", "automation"]
    
    # 메타데이터
    description = Column(Text)
    group = Column(String(50))  # "test", "build", "none"
    is_background = Column(Boolean, default=False)
    dependencies = Column(JSON, default=list)  # 의존하는 다른 작업들
    
    # 사용 통계
    run_count = Column(Integer, default=0)
    last_run_at = Column(DateTime)
    avg_duration_sec = Column(Float)
    success_rate = Column(Float)  # 0.0 ~ 1.0
    
    # 상태
    is_active = Column(Boolean, default=True)
    is_deprecated = Column(Boolean, default=False)
    deprecation_reason = Column(Text)
    
    # 변경 추적
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    sync_version = Column(Integer, default=1)  # tasks.json과 동기화 버전
```

### 우선순위 체계

```python
class TaskPriority(Enum):
    """작업 우선순위"""
    P0_CRITICAL = 0   # 긴급: 시스템 복구, 데이터 손실 방지
    P1_HIGH = 1       # 높음: 일일 운영 필수 작업
    P2_NORMAL = 2     # 보통: 정기 모니터링, 보고서
    P3_LOW = 3        # 낮음: 개발/테스트, 수동 검증
    P4_OPTIONAL = 4   # 선택: 실험, 일회성 작업

# 자동 우선순위 추론 규칙
PRIORITY_RULES = {
    # 키워드 기반 자동 분류
    "P0_CRITICAL": ["emergency", "recover", "rollback", "force"],
    "P1_HIGH": ["daily", "register", "start", "monitor"],
    "P2_NORMAL": ["generate", "report", "status", "check"],
    "P3_LOW": ["test", "debug", "dry-run", "verify"],
    "P4_OPTIONAL": ["demo", "example", "prompt", "explore"]
}
```

### 카테고리 체계

```python
TASK_CATEGORIES = {
    "System": ["Monitoring", "Performance", "Health"],
    "AGI": ["BQI", "Resonance", "Ledger", "Evidence"],
    "Integration": ["YouTube", "RPA", "Comet-Gitko"],
    "Operations": ["Deployment", "Canary", "Rollback"],
    "Development": ["Test", "Debug", "Validation"],
    "Streaming": ["OBS", "YouTube Bot", "ChatOps"]
}
```

---

## 🤖 Task Manager Persona

### 역할 정의

```yaml
name: TaskManager
role: "VS Code 작업 레지스트리 관리자"
responsibilities:
  - tasks.json 파싱 및 DB 동기화
  - 스마트 검색 및 추천
  - 사용 패턴 분석 및 최적화 제안
  - 중복/비활성 작업 정리

capabilities:
  - NLP 기반 작업 검색
  - 실행 통계 수집
  - 의존성 그래프 분석
  - 자동 카테고리 분류
```

### 주요 기능

#### 1. 동기화 (Sync)

```bash
# tasks.json → DB
python -m session_memory.task_manager sync --source vscode --force

# DB → tasks.json (백업 생성)
python -m session_memory.task_manager sync --source db --backup
```

#### 2. 검색 (Search)

```bash
# 자연어 검색
python -m session_memory.task_manager search "24시간 모니터링 보고서"

# 복합 필터
python -m session_memory.task_manager search \
    --category "Monitoring" \
    --priority "P1_HIGH" \
    --tag "daily"

# 정규식
python -m session_memory.task_manager search --regex "AGI.*24h"
```

#### 3. 추천 (Recommend)

```bash
# 컨텍스트 기반 추천
python -m session_memory.task_manager recommend \
    --context "세션 시작" \
    --top 5

# 출력 예:
# 1. [P1] Monitoring: Quick Status
# 2. [P1] AGI: Health Gate (Latest)
# 3. [P2] Core: Quick Health Probe
# 4. [P2] Performance: Dashboard (ops-daily)
# 5. [P3] System: Health Check (Quick)
```

#### 4. 분석 (Analyze)

```bash
# 사용 통계
python -m session_memory.task_manager analyze --period 7d

# 출력:
# Top 10 Most Used:
#   1. Monitoring: Quick Status (142회, 평균 2.3초)
#   2. AGI: Summarize 24h + Health Gate (87회, 평균 15.1초)
#   ...
# 
# Unused (30+ days):
#   - Load Test: Run All Scenarios (마지막: 2024-09-15)
#   - YouTube: E2E Pipeline Test (full) (마지막: 2024-10-02)
```

---

## 🔧 구현 계획

### Phase 1: 기반 구조 (1일)

```python
# session_memory/vscode_task_registry.py
class VSCodeTask(Base): ...
class TaskCategory(Base): ...
class TaskTag(Base): ...
class TaskExecution(Base): ...  # 실행 이력

# session_memory/task_manager.py
class TaskManager:
    def sync_from_vscode(self): ...
    def sync_to_vscode(self): ...
    def parse_tasks_json(self): ...
    def generate_tasks_json(self): ...
```

### Phase 2: 검색 및 색인 (1일)

```python
class TaskSearch:
    def search_by_keywords(self, query: str): ...
    def search_by_category(self, category: str): ...
    def search_by_priority(self, priority: int): ...
    def search_by_tags(self, tags: List[str]): ...
    def fuzzy_search(self, query: str): ...  # 오타 허용
```

### Phase 3: 통계 및 분석 (1일)

```python
class TaskAnalytics:
    def record_execution(self, task_id, duration, success): ...
    def get_usage_stats(self, period_days: int): ...
    def get_success_rate(self, task_id: str): ...
    def find_unused_tasks(self, days: int): ...
    def suggest_optimizations(self): ...
```

### Phase 4: CLI 도구 (반나절)

```bash
# scripts/task_cli.py
task search "monitoring"
task run "Quick Status" --record  # 실행 + 통계 기록
task list --category AGI --priority P1
task analyze --period 30d
task clean --unused-days 60 --dry-run
```

---

## 📊 예상 효과

### 정량적 개선

- **검색 속도**: 선형 O(n) → 색인 O(log n)
- **작업 발견**: 수동 스크롤 → 즉시 검색
- **중복 제거**: ~20% 작업 통합 가능 (예상)
- **관리 시간**: 주 1시간 → 월 1시간

### 정성적 개선

- ✅ 우선순위 기반 작업 필터링
- ✅ 사용 패턴 분석으로 워크플로우 최적화
- ✅ 비활성 작업 자동 정리
- ✅ 컨텍스트 기반 작업 추천

---

## 🚦 실행 여부 결정

### 현재 시스템 평가

- ✅ **작동 중**: tasks.json은 문제없이 작동
- ⚠️ **관리 부담**: 수동 검색/정리 필요
- 🔄 **확장성**: 200개 → 500개 시 관리 한계

### 권장 사항

**지금 당장 필요한가?** → **아니오**

- 현재 시스템은 정상 작동 중
- 긴급한 문제는 없음

**언제 필요한가?**

1. 작업 개수 500개 이상 시
2. 팀 협업 필요 시 (여러 사람이 tasks.json 편집)
3. 자동화된 워크플로우 추천 필요 시

**점진적 도입 전략**

```
단계 1 (선택): 현재 tasks.json 분석 스크립트
    → 중복/미사용 작업 찾기
    → 카테고리 자동 분류

단계 2 (나중): DB 동기화 기능 추가
    → 검색 API 구현

단계 3 (미래): TaskManager Persona 완전 통합
    → 자동 최적화 제안
```

---

## 🎯 즉시 실행 가능한 대안

현재 시스템을 유지하면서 개선할 수 있는 방법:

### 1. 간단한 분석 스크립트

```powershell
# scripts/analyze_tasks.ps1
# - 카테고리별 작업 개수
# - 중복 가능성 있는 작업 (라벨 유사도)
# - 사용 빈도 추정 (git log 기반)
```

### 2. tasks.json 주석 개선

```json
{
  "label": "Monitoring: Quick Status",
  "// metadata": {
    "priority": "P1_HIGH",
    "category": "Monitoring",
    "tags": ["daily", "ops", "health"],
    "frequency": "multiple-per-day"
  }
}
```

### 3. 카테고리별 파일 분할

```
.vscode/
  tasks.json (메인 + 가장 자주 사용)
  tasks/
    monitoring.json
    agi.json
    youtube.json
    streaming.json
```

---

## 💡 최종 결론

**추천: 현 상태 유지 + 점진적 개선**

1. ✅ **지금**: 현재 tasks.json 유지 (작동 중, 문제 없음)
2. 📝 **단기** (1주 내): 분석 스크립트 추가 (중복/미사용 작업 찾기)
3. 🔄 **중기** (1개월): 필요 시 주석 기반 메타데이터 추가
4. 🚀 **장기** (필요 시): DB 통합 (작업 500개 이상 또는 팀 확장 시)

**이유**:

- "완벽한 시스템"보다 "작동하는 시스템"이 우선
- 과도한 추상화는 복잡성만 증가
- 문제가 명확해지면 그때 해결

---

**다음 단계 제안**:

1. 이 문서 검토 후 피드백
2. 원하시면 **간단한 분석 스크립트** 먼저 작성
3. 실제 필요성 확인 후 단계적 구현

어떻게 진행하시겠습니까? 🤔
