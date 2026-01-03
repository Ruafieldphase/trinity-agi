# 🏗️ 기존 시스템 인벤토리

> **문제**: 작업이 느린 이유는 "이미 만들어진 시스템을 재사용하지 않아서"
> **해결**: 먼저 여기서 찾아보고, 있으면 재사용, 없으면 새로 만들기

---

## 📂 Core Systems (fdo_agi_repo/copilot/)

### 1. 🧠 Hippocampus (기억 시스템)
- **파일**: `fdo_agi_repo/copilot/hippocampus.py`
- **역할**: 
  - 단기 기억 (128K 컨텍스트) → 장기 기억 (7개 시스템) 공고화
  - Everything 검색 통합 ✅ (이미 됨!)
  - 세션 간 연속성 관리
- **사용법**:
  ```python
  from fdo_agi_repo.copilot.hippocampus import CopilotHippocampus
  hippo = CopilotHippocampus(workspace_root)
  hippo.search_memories("keyword")
  ```
- **테스트**: `scripts/test_hippocampus.py`, `scripts/test_hippocampus_everything.py`

### 2. 🧹 Glymphatic (청소 시스템)
- **파일**: `fdo_agi_repo/copilot/glymphatic.py`
- **역할**: 
  - 오래된 메모리 정리
  - 중복 제거
  - 압축 및 아카이빙
- **사용 시나리오**: 
  - "메모리 정리해줘"
  - "디스크 공간 확보"
  - "오래된 로그 삭제"

### 3. 🌊 Flow Observer (주의력 추적)
- **파일**: `fdo_agi_repo/copilot/flow_observer_integration.py`
- **역할**:
  - ADHD 특성 인식
  - 몰입 상태 감지
  - 주의력 패턴 분석
- **VS Code Task**: `🌊 Flow: Start Background Monitor`

### 4. 🛡️ Immune System (자가 치유)
- **파일**: `fdo_agi_repo/copilot/immune_system.py`
- **역할**:
  - 에러 자동 탐지
  - 자가 복구
  - 시스템 건강 모니터링
- **관련**: `auto_immune_loop.py`, `immune_recovery_bridge.py`

### 5. 🎵 Body Rhythm (생체 리듬)
- **파일**: `fdo_agi_repo/copilot/body_rhythm.py`
- **역할**:
  - 작업 리듬 감지
  - 휴식 시간 제안
  - 에너지 레벨 추적

### 6. 🔮 Quantum Flow Monitor
- **파일**: `fdo_agi_repo/copilot/quantum_flow_monitor.py`
- **역할**:
  - 양자적 관점 분석
  - 파동/입자 이중성 관찰
- **관련**: `wave_detector.py`, `particle_detector.py`, `wave_particle_unifier.py`

### 7. 🎭 Perspective Theory
- **파일**: `fdo_agi_repo/copilot/perspective_theory.py`
- **역할**:
  - 다중 관점 분석
  - 맥락 전환

### 8. 🧠 Synaptic Pruner (신경망 가지치기)
- **파일**: `fdo_agi_repo/copilot/synaptic_pruner.py`
- **역할**:
  - 불필요한 연결 제거
  - 효율적인 정보 구조 유지

---

## 🔧 Utility Systems (fdo_agi_repo/utils/)

### 1. 🔍 Everything Search ⚡
- **파일**: `fdo_agi_repo/utils/everything_search.py`
- **역할**: 
  - 초고속 파일 검색 (Everything CLI 래퍼)
  - Hippocampus와 이미 통합됨 ✅
- **사용법**:
  ```python
  from fdo_agi_repo.utils.everything_search import quick_search
  results = quick_search("*.md", max_results=10)
  ```
- **스크립트**: `scripts/everything_search.ps1`, `scripts/everything_setup.ps1`
- **CLI**: `scripts/es.exe`

### 2. 🎵 Groove Engine (음악 리듬)
- **파일**: `fdo_agi_repo/utils/groove_engine.py`
- **역할**:
  - 작업 리듬 프로파일
  - 음악 추천
- **VS Code Task**: `🎵 Music: Generate Groove Profile (24h)`

### 3. 📡 Event Bus (이벤트 버스)
- **파일**: `fdo_agi_repo/utils/event_bus.py`
- **역할**:
  - 시스템 간 이벤트 전달
  - 느슨한 결합 유지

---

## 🌐 Universal Systems (fdo_agi_repo/universal/)

### 1. 🎯 Task Schema (범용 작업 스키마)
- **파일**: `fdo_agi_repo/universal/task_schema.py`
- **역할**:
  - 도메인 독립적 작업 표현
  - 추상적 의도 정의
- **클래스**: `UniversalTask`, `AbstractIntent`, `DataType`

### 2. 🔄 Domain Adapter (도메인 어댑터)
- **파일**: `fdo_agi_repo/universal/domain_adapter.py`
- **역할**:
  - 범용 작업 → 도메인별 실행
  - 소프트웨어, 헬스케어, 금융 등
- **어댑터**: `SoftwareEngineeringAdapter`, `HealthcareAdapter`, `FinanceAdapter`

### 3. 🌊 Resonance (공명 시스템)
- **파일**: `fdo_agi_repo/universal/resonance.py`
- **역할**:
  - 작업 간 공명 탐지
  - 이벤트 저장소

---

## 🎮 Trinity Systems (fdo_agi_repo/trinity/)

### 1. 🎼 Resonance Orchestrator
- **파일**: `fdo_agi_repo/trinity/resonance_orchestrator.py`
- **역할**:
  - 세 가지 시스템 조율
  - 공명 상태 관리
- **VS Code Task**: `🔄 Trinity: Autopoietic Cycle (24h, open)`

---

## 📊 Tools (fdo_agi_repo/tools/)

### 1. 🌐 Web Search
- **파일**: `fdo_agi_repo/tools/web_search.py`
- **역할**: 웹 검색 기능

### 2. 📈 Dashboard Generator
- **파일**: `fdo_agi_repo/tools/generate_dashboard.py`
- **역할**: HTML 대시보드 생성
- **VS Code Task**: `📊 Dashboard: Enhanced (GPU+Queue+LLM)`

---

## 🔧 Scripts (scripts/)

### PowerShell 스크립트들

**검색 & 인덱싱**:
- `build_original_data_index.ps1` - Original Data 인덱스 생성
- `build_youtube_index.ps1` - YouTube 학습 인덱스
- `everything_search.ps1` - Everything 검색 (PS 래퍼)
- `everything_setup.ps1` - Everything 설치/설정

**모니터링 & 리포팅**:
- `generate_monitoring_report.ps1` - 모니터링 리포트 (24h/7d)
- `quick_status.ps1` - 통합 대시보드 (AGI + Core)
- `system_health_check.ps1` - 시스템 헬스 체크
- `check_life_continuity.ps1` - Life Continuity 체크

**세션 & 연속성**:
- `session_continuity_restore.ps1` - 세션 복원 ⚡
- `save_session_with_changes.ps1` - 세션 저장
- `end_daily_session.ps1` - 하루 종료 (백업 포함)
- `auto_resume_on_startup.ps1` - 자동 재개

**자율 목표 시스템**:
- `autonomous_goal_generator.py` - 자율 목표 생성
- `autonomous_goal_executor.py` - 목표 실행
- `start_autonomous_goal_loop.ps1` - 연속 루프 시작
- `generate_autonomous_goal_dashboard.ps1` - 목표 대시보드

**음악 & 리듬**:
- `music_daemon.py` - 음악 자동 재생 데몬
- `generate_groove_profile.py` - Groove 프로파일 생성
- `flow_binaural_generator.py` - 바이노럴 비트 생성
- `rhythm_audio_signature.py` - 리듬 오디오 서명

**RPA & Task Queue**:
- `ensure_task_queue_server.ps1` - Queue Server 시작
- `ensure_rpa_worker.ps1` - RPA Worker 관리
- `task_watchdog.py` - Watchdog (자동 복구)
- `enqueue_rpa_smoke.ps1` - RPA 테스트

**YouTube 학습**:
- `youtube_learning_pipeline.ps1` - YouTube 학습 파이프라인
- `enqueue_youtube_learn.ps1` - YouTube 작업 큐잉
- `build_youtube_dashboard.ps1` - YouTube 대시보드

**Copilot 통합**:
- `new_chat_with_context.ps1` - 컨텍스트 포함 새 채팅
- `chatops_router.ps1` - ChatOps 라우터 (자연어 명령)

**백업 & 정리**:
- `end_of_day_backup.ps1` - 하루 종료 백업
- `rotate_status_snapshots.ps1` - 스냅샷 로테이션
- `cleanup_snapshot_archives.ps1` - 아카이브 정리

---

## 🎯 사용 시나리오별 추천 시스템

### "파일 찾기가 느려요"
→ ✅ **Everything Search** 이미 있음!
```powershell
.\scripts\everything_setup.ps1 -CheckStatus
.\scripts\everything_search.ps1 -Pattern "*.md" -MaxResults 10
```

### "세션 복원해줘"
→ ✅ **Session Continuity** 이미 있음!
```powershell
.\scripts\session_continuity_restore.ps1 -OpenReport
```
**VS Code Task**: `📖 Session: Restore + Open Report`

### "자동으로 목표 생성해줘"
→ ✅ **Autonomous Goal System** 이미 있음!
```powershell
.\scripts\autonomous_goal_generator.py --hours 24
```
**VS Code Task**: `🎯 Goal: Generate + Open (24h)`

### "시스템 상태 보여줘"
→ ✅ **Monitoring Dashboard** 이미 있음!
```powershell
.\scripts\quick_status.ps1
```
**VS Code Task**: `Monitoring: Unified Dashboard (AGI + Core)`

### "음악 추천해줘"
→ ✅ **Music Daemon + Groove Engine** 이미 있음!
**VS Code Task**: `🎵 Music: Generate Groove Profile + Open`

### "작업 흐름 관찰해줘"
→ ✅ **Flow Observer** 이미 있음!
**VS Code Task**: `🌊 Flow: Start Background Monitor`

---

## 📋 작업 전 체크리스트

새 요청이 왔을 때:

1. **먼저 이 인벤토리에서 검색** 🔍
2. **없으면 grep_search로 확인**:
   ```
   grep_search: query="class.*Search|def.*find" includePattern="fdo_agi_repo/**/*.py"
   ```
3. **있으면 재사용, 없으면 새로 만들기**

---

## 🚀 빠른 참조

**가장 자주 쓰는 것들**:
- Everything 검색: `scripts/everything_search.ps1`
- 세션 복원: `scripts/session_continuity_restore.ps1`
- 상태 체크: `scripts/quick_status.ps1`
- 목표 생성: `scripts/autonomous_goal_generator.py`
- Hippocampus: `fdo_agi_repo/copilot/hippocampus.py`

**모든 VS Code Task 보기**:
```powershell
# tasks.json 파일 열기
code .vscode/tasks.json
```

---

**마지막 업데이트**: 2025-11-14
**목적**: "이미 있는 걸 다시 만들지 않기" - 작업 속도 향상 🚀
