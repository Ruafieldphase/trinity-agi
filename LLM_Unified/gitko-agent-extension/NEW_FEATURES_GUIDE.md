# 🎯 Gitko Agent Extension - 새 기능 가이드

**버전**: 0.2.0  
**추가일**: 2025-11-02

---

## 🌟 새로 추가된 기능

### 1. 🎯 Task Queue Monitor

Task Queue Server (Port 8091)를 실시간으로 모니터링하는 WebView 패널

**실행 방법**:
- 명령 팔레트 (`Ctrl+Shift+P`)에서 `Gitko: Show Task Queue Monitor` 실행
- 또는 `@gitko`에게 "task queue 상태 보여줘" 요청

**주요 기능**:
- ✅ 실시간 큐 상태 모니터링 (2초마다 자동 갱신)
- ✅ Pending / In-Flight / Completed / Failed 작업 통계
- ✅ Success Rate 및 평균 처리 시간 표시
- ✅ 작업 상세 정보 (Task ID, Type, 타임스탬프)
- ✅ Completed 작업 일괄 삭제 기능

**필수 조건**:
```powershell
# Task Queue Server 실행 필요
cd LLM_Unified\ion-mentoring
.\.venv\Scripts\python.exe task_queue_server.py --port 8091
```

---

### 2. 🌊 Resonance Ledger Viewer

AGI 자기교정 시스템의 Resonance Ledger를 시각화하는 타임라인 뷰

**실행 방법**:
- 명령 팔레트에서 `Gitko: Show Resonance Ledger` 실행
- 또는 `@gitko`에게 "resonance ledger 보여줘" 요청

**주요 기능**:
- ✅ 최근 100개 이벤트를 타임라인으로 표시
- ✅ Agent별 필터링 (Sena, Lubit, Binoche 등)
- ✅ Resonance Score 시각화
- ✅ 파일 변경 자동 감지 및 실시간 업데이트
- ✅ Event Type, Action, Context 상세 정보
- ✅ Evidence Link 지원

**데이터 경로**:
```
c:\workspace\agi\fdo_agi_repo\memory\resonance_ledger.jsonl
```

---

## 🔧 설정

### `settings.json`에서 설정 가능한 항목:

```json
{
  "gitko.taskQueueUrl": "http://127.0.0.1:8091",
  "gitko.enableHttpPoller": true,
  "gitko.httpPollingInterval": 2000
}
```

---

## 🚀 사용 시나리오

### 시나리오 1: RPA 작업 모니터링

1. Task Queue Server 시작
   ```powershell
   cd LLM_Unified\ion-mentoring
   .\.venv\Scripts\python.exe task_queue_server.py --port 8091
   ```

2. RPA Worker 시작
   ```powershell
   cd fdo_agi_repo
   .\.venv\Scripts\python.exe integrations\rpa_worker.py --server http://127.0.0.1:8091
   ```

3. VS Code에서 **Task Queue Monitor** 열기
   - `Ctrl+Shift+P` → `Gitko: Show Task Queue Monitor`

4. 실시간으로 작업 진행 상황 확인
   - Pending: 대기 중인 작업
   - In-Flight: 현재 실행 중
   - Completed: 완료된 작업
   - Failed: 실패한 작업

### 시나리오 2: AGI 학습 과정 추적

1. **Resonance Ledger Viewer** 열기
   - `Ctrl+Shift+P` → `Gitko: Show Resonance Ledger`

2. 에이전트별 활동 필터링
   - "Sena" 버튼: 브리지형 에이전트 활동만 보기
   - "Lubit" 버튼: 분석형 에이전트 활동만 보기
   - "All" 버튼: 전체 이벤트 보기

3. Resonance Score 추적
   - 높은 점수 = 성공적인 학습 패턴
   - 낮은 점수 = 개선 필요한 영역

---

## 🎨 UI 미리보기

### Task Queue Monitor
```
┌─────────────────────────────────────────┐
│ 🎯 Task Queue Monitor        🔄 Refresh │
├─────────────────────────────────────────┤
│ Health: HEALTHY  Success Rate: 86.08%   │
│                                         │
│ ⏳ Pending: 5    🔄 In-Flight: 2       │
│ ✅ Completed: 128  ❌ Failed: 12        │
│                                         │
│ 📋 Pending Tasks                        │
│   [youtube_learning] Priority: high     │
│   ID: task-abc123                       │
│   Created: 2025-11-02 10:30:15         │
└─────────────────────────────────────────┘
```

### Resonance Ledger
```
┌─────────────────────────────────────────┐
│ 🌊 Resonance Ledger          🔄 Refresh │
├─────────────────────────────────────────┤
│ Total Events: 95   Avg Score: 0.82     │
│ Active Agents: 3   Event Types: 8      │
│                                         │
│ Filter: [All] [Sena] [Lubit] [Binoche] │
│                                         │
│ Timeline:                               │
│  ● task_completed                       │
│    👤 Sena  ⚡ execute  🎯 0.85         │
│    2025-11-02 10:25:33                 │
│    ▼ Context                           │
│                                         │
│  ● learning_pattern_detected            │
│    👤 Lubit  🎯 0.92                   │
│    2025-11-02 10:24:15                 │
└─────────────────────────────────────────┘
```

---

## 📝 다음 단계

현재 구현된 기능:
- ✅ Task Queue 실시간 모니터링
- ✅ Resonance Ledger 타임라인 뷰
- ✅ 파일 변경 자동 감지
- ✅ Agent별 필터링

계획 중인 기능:
- ⏳ 통합 대시보드 (한 화면에서 모든 정보)
- ⏳ 알림 시스템 (Task 실패 시 자동 알림)
- ⏳ 성능 차트 (시간대별 Success Rate)
- ⏳ Evidence Index 검색 기능

---

## 🐛 문제 해결

### Task Queue Monitor에 "Connection Error" 표시될 때

**원인**: Task Queue Server가 실행되지 않음

**해결**:
```powershell
cd LLM_Unified\ion-mentoring
.\.venv\Scripts\python.exe task_queue_server.py --port 8091
```

### Resonance Ledger가 비어있을 때

**원인**: `resonance_ledger.jsonl` 파일이 없거나 경로가 틀림

**확인**:
```powershell
ls c:\workspace\agi\fdo_agi_repo\memory\resonance_ledger.jsonl
```

---

## 💡 팁

1. **자동 시작**: `.vscode/tasks.json`에 Task Queue Server 시작 작업 추가
2. **단축키**: 자주 쓰는 명령에 키바인딩 설정
3. **멀티 모니터**: Monitor를 별도 창으로 분리하여 사용

---

**문의**: GitHub Issues 또는 @gitko에게 질문하세요!
