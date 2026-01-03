# Session Memory System

## 개요

작업 컨텍스트를 잃어버리는 문제를 해결하기 위한 Hybrid Session Tracking System입니다.

**핵심 기능:**

- 📝 작업 세션 자동 기록 (JSONL + SQLite)
- 🔍 전체 텍스트 검색 (FTS5)
- 🏷️ 태그 기반 분류
- 📊 세션 통계 및 분석
- 🎯 자연어 명령어 지원 (ChatOps)
- 📄 파일 변경 추적
- 🎨 Git 통합 (branch, commit)
- 💯 Resonance Score (작업 만족도)

## 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                   User Interface                        │
├─────────────┬──────────────┬──────────────┬────────────┤
│  ChatOps    │  PowerShell  │  Python CLI  │  VS Code   │
│  (자연어)    │  (편의성)     │  (고급 쿼리)  │  (통합)    │
└─────┬───────┴──────┬───────┴──────┬───────┴─────┬──────┘
      │              │              │             │
      v              v              v             v
┌─────────────────────────────────────────────────────────┐
│                  Session Logger                         │
│  - start_session()  - add_task()  - add_artifact()     │
│  - end_session()    - pause_session()                  │
└───────────┬─────────────────────────────────────────────┘
            │
            ├──────────────┬──────────────────────┐
            v              v                      v
    ┌──────────────┐  ┌────────────┐     ┌──────────────┐
    │ session.jsonl│  │ sessions.db│     │  Git Repo    │
    │  (Source of  │  │  (SQLite + │     │ (branch/hash)│
    │   Truth)     │  │   FTS5)    │     │              │
    └──────────────┘  └────────────┘     └──────────────┘
```

**데이터 흐름:**

1. **JSONL**: 불변 감사 추적, Git-friendly, 백업 용이
2. **SQLite**: 빠른 쿼리, FTS5 검색, 집계/통계
3. **Auto-sync**: 각 작업 후 JSONL → SQLite 동기화

## 빠른 시작

### 1. 새 세션 시작 (자연어)

```powershell
chatops_router.ps1 -Say "세션 시작해"
```

또는 직접:

```powershell
.\session_memory\session_tools.ps1 start "BQI Phase 6 구현"
```

### 2. 작업 추가

```powershell
chatops_router.ps1 -Say "작업 추가"
```

또는:

```powershell
.\session_memory\session_tools.ps1 task "Binoche_Observer Persona Learner 설계"
```

### 3. 파일 추적

```powershell
.\session_memory\session_tools.ps1 file "fdo_agi_repo/scripts/rune/binoche_persona_learner.py"
```

### 4. 세션 종료

```powershell
chatops_router.ps1 -Say "세션 종료"
# Resonance score (0.0-1.0) 입력: 0.85
```

### 5. 과거 작업 찾기 (자연어!)

```powershell
# 최근 작업 보기
chatops_router.ps1 -Say "지난번에 뭐 했지?"

# 키워드 검색
chatops_router.ps1 -Say "BQI 작업 찾아줘"

# 활성 세션
chatops_router.ps1 -Say "활성 세션"

# 통계
chatops_router.ps1 -Say "세션 통계"
```

## ChatOps 명령어

| 자연어 (한국어) | 영어 | Intent | 동작 |
|----------------|------|--------|------|
| 세션 시작해, 작업 시작 | start session | `session_start` | 새 세션 생성 |
| 작업 추가, 할 일 추가 | add task | `session_add_task` | 현재 세션에 작업 추가 |
| 세션 종료, 작업 끝 | end session | `session_end` | 현재 세션 종료 |
| 지난번에 뭐 했지?, 최근 작업 | recent work | `session_recent` | 최근 10개 세션 표시 |
| BQI 작업 찾아줘 | find BQI work | `session_search:bqi` | "BQI" 검색 |
| 활성 세션, 진행중 작업 | active sessions | `session_active` | 활성/일시정지 세션 |
| 세션 통계, 작업 통계 | session stats | `session_stats` | 페르소나별 통계 |
| 세션 상세, 세션 정보 | session details | `session_details` | 세션 상세 정보 |

> **English quick commands**  
> Natural-language phrases such as `start the session`, `add a task`, `end session`, `recent sessions`, `search sessions for bqi`, `active sessions`, `session stats`, `session details`, `save conversations`, and `wrap up the day` now resolve to the same intents. Stream/Bot controls like `start the stream`, `stop the stream`, `start the bot`, `stop the bot`, `switch to ai dev`, `preflight`, and `install obs deps` are also recognised in English.

## PowerShell 명령어

```powershell
# 세션 관리
.\session_tools.ps1 start <title>           # 새 세션 시작
.\session_tools.ps1 task <title>            # 작업 추가
.\session_tools.ps1 file <path>             # 파일 추적
.\session_tools.ps1 end [resonance]         # 세션 종료
.\session_tools.ps1 pause                   # 세션 일시정지
.\session_tools.ps1 resume <session-id>     # 세션 재개

# 검색 및 조회
.\session_tools.ps1 search <query>          # 전체 텍스트 검색
.\session_tools.ps1 recent [N]              # 최근 N개 세션
.\session_tools.ps1 details <session-id>    # 세션 상세
.\session_tools.ps1 active                  # 활성 세션
.\session_tools.ps1 similar <session-id>    # 유사 세션 (태그 기반)
.\session_tools.ps1 by-file <pattern>       # 파일 경로로 검색

# 내보내기 및 통계
.\session_tools.ps1 export <session-id> <path>  # Markdown 내보내기
.\session_tools.ps1 stats                   # 페르소나별 통계
.\session_tools.ps1 help                    # 도움말
```

## Python API

```python
from session_logger import SessionLogger
from session_search import SessionSearch

# 세션 시작
logger = SessionLogger()
session_id = logger.start_session(
    title="BQI Phase 6 Implementation",
    description="Binoche_Observer Persona Learning with Ensemble Judges",
    context="Implementing online learning for judge ensemble weights",
    persona="Perple",
    tags=["bqi", "phase-6", "machine-learning"]
)

# 작업 추가
logger.add_task(
    title="Design Binoche_Observer Persona Learner",
    description="Create adaptive persona model based on resonance feedback",
    status="in-progress"
)

# 파일 추적
logger.add_artifact(
    file_path="fdo_agi_repo/scripts/rune/binoche_persona_learner.py",
    artifact_type="code",
    operation="created",
    description="Persona learning algorithm implementation"
)

# 세션 종료
logger.end_session(resonance_score=0.90)

# 검색
searcher = SessionSearch()
results = searcher.search_text("BQI", limit=10)
recent = searcher.get_recent_sessions(limit=5, status="completed")
active = searcher.get_active_sessions()
stats = searcher.get_stats_by_persona()

# 내보내기
session = searcher.get_session_details(session_id)
searcher.export_to_markdown(session, "outputs/session_report.md")
```

## 데이터베이스 스키마

### 주요 테이블

**sessions**

- `session_id` (UUID, PK)
- `start_time`, `end_time` (ISO-8601)
- `title`, `description`, `context`
- `status` (active/paused/completed/abandoned)
- `branch`, `commit_hash` (Git 정보)
- `persona` (Perple, Binoche_Observer, Sena 등)
- `parent_session_id` (FK, 연속 작업 추적)
- `resonance_score` (0.0-1.0)

**tasks**

- `task_id` (UUID, PK)
- `session_id` (FK)
- `task_number` (자동 증가)
- `title`, `description`
- `status` (not-started/in-progress/completed/blocked)
- `started_at`, `completed_at`
- `duration_seconds`
- `result`, `notes`

**artifacts**

- `artifact_id` (UUID, PK)
- `session_id` (FK), `task_id` (FK, nullable)
- `artifact_type` (file/code/script/doc/data)
- `file_path`, `relative_path`
- `content_hash` (SHA256)
- `file_size_bytes`
- `operation` (created/modified/deleted)
- `description`

**tags** + **session_tags** (Many-to-Many)

### FTS5 Virtual Tables

- `sessions_fts`: Full-text search on title, description, context
- `tasks_fts`: Full-text search on title, description, notes

### Views

- `v_recent_sessions`: 최근 세션 + 작업/파일 수 + 태그
- `v_active_sessions`: 활성/일시정지 세션만 필터
- `v_session_stats_by_persona`: 페르소나별 집계
- `v_session_durations`: 세션 지속 시간 계산

## 사용 시나리오

### 1. 매일 아침 루틴

```powershell
# 어제 뭐 했는지 확인
chatops_router.ps1 -Say "지난번에 뭐 했지?"

# 오늘 작업 시작
chatops_router.ps1 -Say "세션 시작해"
# Title: Daily standup 2025-10-30

# 작업 추가
chatops_router.ps1 -Say "작업 추가"
# Task: Review BQI Phase 6 results
```

### 2. 버그 수정 중

```powershell
# 세션 시작
.\session_tools.ps1 start "Fix ChatOps session search intent extraction"

# 작업 추가
.\session_tools.ps1 task "Analyze regex pattern for Korean query extraction"

# 파일 추적
.\session_tools.ps1 file "scripts/chatops_intent.py"

# 종료
.\session_tools.ps1 end 0.75
```

### 3. 과거 작업 참조

```powershell
# 특정 키워드 검색
chatops_router.ps1 -Say "Canary 작업 찾아줘"

# 파일로 검색
.\session_tools.ps1 by-file "chatops_router.ps1"

# 유사 세션 찾기 (태그 기반)
.\session_tools.ps1 similar 85aed5f1
```

### 4. 통계 및 분석

```powershell
# 페르소나별 통계
chatops_router.ps1 -Say "세션 통계"

# 활성 세션 확인
chatops_router.ps1 -Say "활성 세션"

# 상세 정보
.\session_tools.ps1 details 85aed5f1
```

## 고급 기능

### 1. 연속 작업 추적

```python
# 이전 세션을 부모로 지정
session_id = logger.start_session(
    title="BQI Phase 6 - Day 2",
    parent_session_id="85aed5f1-efb8-4d83-a087-35ccd86a57f9"
)
```

### 2. FTS5 고급 검색

```python
# Boolean queries
results = searcher.search_text("BQI AND phase-6")
results = searcher.search_text("ChatOps OR session")

# Phrase search
results = searcher.search_text('"session memory"')

# Prefix search
results = searcher.search_text("canary*")
```

### 3. JSON 내보내기

```python
session = searcher.get_session_details(session_id)
searcher.export_to_json([session], "outputs/session.json")
```

### 4. 커스텀 쿼리

```python
import sqlite3

conn = sqlite3.connect("session_memory/sessions.db")
cursor = conn.cursor()

# 긴 세션 찾기 (4시간 이상)
cursor.execute("""
    SELECT * FROM v_session_durations
    WHERE duration_minutes > 240
    ORDER BY duration_minutes DESC
""")

# 높은 resonance 세션
cursor.execute("""
    SELECT * FROM sessions
    WHERE resonance_score > 0.85
    ORDER BY resonance_score DESC
    LIMIT 10
""")
```

## 통합 계획

### Phase 2 (다음 작업)

- [x] ChatOps 통합 ✅
- [ ] Resonance Ledger 연동 (기존 데이터 import)
- [ ] VS Code 파일 모니터링
- [ ] Daily Summary 자동 생성

### Resonance Ledger 연동

```python
# Import script 예정
# - Read fdo_agi_repo/memory/resonance_ledger.jsonl
# - Convert ledger events to sessions
# - Tag with "legacy" or "from-ledger"
# - Map resonance scores
```

### VS Code 통합

```typescript
// FileSystemWatcher 예정
const watcher = workspace.createFileSystemWatcher('**/*');
watcher.onDidCreate(uri => {
    // Prompt: "Track this file in current session?"
    sessionLogger.add_artifact(uri.fsPath, 'file', 'created');
});
```

### Daily Summary

```python
# scripts/generate_daily_summary.py 예정
# - Query last 24h sessions
# - Group by persona, status, tags
# - Generate Markdown with stats
# - Save to outputs/daily_summaries/YYYY-MM-DD.md
```

## 파일 구조

```
session_memory/
├── schema.sql                  # Database schema (200 lines)
├── session_logger.py           # Core logger (450 lines)
├── session_search.py           # Search & CLI (400 lines)
├── session_tools.ps1           # PowerShell wrapper (200 lines)
├── sessions.db                 # SQLite database
├── session_log.jsonl           # Immutable log
└── README.md                   # This file

scripts/
├── chatops_router.ps1          # Natural language router (updated)
└── chatops_intent.py           # Intent resolver (updated)
```

## 문제 해결

### Q: 세션이 시작되지 않음

```powershell
# Python 경로 확인
python --version  # Should be Python 3.x

# 디렉토리 확인
cd C:\workspace\agi\session_memory
Test-Path sessions.db  # Should return True after first run
```

### Q: 검색 결과가 없음

```powershell
# 데이터 확인
python session_search.py recent --limit 5

# FTS5 재구축 (드물게 필요)
sqlite3 sessions.db "INSERT INTO sessions_fts(sessions_fts) VALUES('rebuild');"
```

### Q: ChatOps 명령어가 작동 안 함

```powershell
# Intent 확인
python scripts/chatops_intent.py --say "세션 시작해"
# Should output: session_start

# 직접 실행 테스트
.\session_memory\session_tools.ps1 help
```

### Q: 한글 인코딩 문제

```powershell
# PowerShell 콘솔 UTF-8 설정
chcp 65001

# 스크립트 상단에 추가
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

## 베스트 프랙티스

1. **세션 시작 시 명확한 제목**: "BQI Phase 6" 대신 "BQI Phase 6 - Binoche_Observer Persona Learner Implementation"
2. **태그 일관성 유지**: "bqi", "phase-6", "machine-learning" (소문자, 하이픈)
3. **Resonance Score 기준**:
   - 0.0-0.3: 실패 또는 막힘
   - 0.4-0.6: 부분 성공
   - 0.7-0.8: 성공
   - 0.9-1.0: 뛰어난 성과
4. **세션 종료 전 파일 추적**: 생성/수정한 모든 주요 파일 기록
5. **자연어 명령 활용**: ChatOps로 빠르게 검색 ("지난번에 뭐 했지?")

## 참고 자료

- [SQLite FTS5 문서](https://www.sqlite.org/fts5.html)
- [Python sqlite3 모듈](https://docs.python.org/3/library/sqlite3.html)
- [PowerShell 스크립팅 가이드](https://docs.microsoft.com/powershell/)

## 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능

---

**Last Updated**: 2025-10-29  
**Version**: 1.0.0  
**Status**: ✅ Production Ready (ChatOps 통합 완료)
