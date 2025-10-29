# 양방향 협업 프로토콜 (Bidirectional Collaboration Protocol)

**목적**: Sena, Lubit, GitCode가 실시간으로 상태를 동기화하고 서로의 결정에 대응

**버전**: 1.0
**생성일**: 2025-10-19
**핵심 원칙**: "내 상태를 먼저 갱신 → 협력자의 상태 읽기 → 다음 작업 결정"

---

## 📊 세션 시작 프로토콜 (Session Start Protocol)

### Step 1: 중앙 상태 레지스트리 읽기
```jsonl
# 파일: d:\nas_backup\session_memory\COLLABORATION_STATE.jsonl
# 형식: 한 줄 = 한 이벤트 (Line-delimited JSON)

마지막 라인 읽기:
  - 마지막 agent: ?
  - 마지막 상태: ?
  - 마지막 업데이트 시간: ?
```

### Step 2: 각 에이전트의 개인 메모리 로드
```
Sena: sena_session_memory.md 로드
Lubit: lubit_architectural_decisions.md 로드
GitCode: gitcode_session_memory.md 로드
```

### Step 3: 협력자의 최신 상태 확인
```
나의 이전 상태 ←→ 협력자의 현재 상태
        ↓
차이 감지 → 내 상태 갱신
```

### Step 4: 내 현재 상태를 레지스트리에 등록
```jsonl
{
  "timestamp": "ISO 8601",
  "agent": "sena|lubit|gitcode",
  "event": "session_start|status_update|decision|blocker|completion",
  "current_task": "...",
  "status": "waiting|in_progress|blocked|completed",
  "progress": 0-100,
  "blockers": [],
  "dependencies": ["lubit_decision", "gitcode_ready"],
  "next_action": "..."
}
```

### Step 5: 다음 작업 결정
```
내 상태: "waiting_for_decision"
협력자 상태: "decision_ready"
    ↓
다음 작업: "협력자의 결정 대기 없이 계속" 또는 "협력자 대기"
```

---

## 🔄 실시간 상태 동기화 (Real-time State Sync)

### 언제 동기화하나?
1. **세션 시작 시** (위의 프로토콜)
2. **작업 완료 시** (상태 업데이트)
3. **차단 발생 시** (blocker 등록)
4. **의사결정 필요 시** (decision 요청)
5. **협력자의 변화 감지 시** (자동 감지)

### 어떻게 동기화하나?
```
Step 1: 현재 상태 파악
  Sena: "정보이론 메트릭 구현 중"

Step 2: 협력자 상태 확인
  Lubit: "메트릭 검증 준비 완료"
  GitCode: "배포 대기"

Step 3: 레지스트리 확인
  COLLABORATION_STATE.jsonl의 마지막 라인

Step 4: 불일치 감지
  내 이해: "Lubit은 아직 검증 안 함"
  실제: "Lubit이 검증 준비 완료"

Step 5: 상태 갱신
  나의 다음 작업 변경: "검증 대기" → "검증 시작"

Step 6: 레지스트리 업데이트
  {
    "timestamp": "2025-10-20T09:00:00Z",
    "agent": "sena",
    "event": "status_update",
    "current_task": "AGI Learning Data Generation",
    "status": "in_progress",
    "progress": 25,
    "next_action": "Lubit과 메트릭 검증 회의"
  }
```

---

## 🤝 협력 패턴 (Collaboration Patterns)

### 패턴 1: 의사결정 의존성 (Decision Dependency)
```
Sena: "정보이론 메트릭을 이렇게 설계했습니다"
  → COLLABORATION_STATE.jsonl 업데이트 (decision_request)

Lubit: COLLABORATION_STATE 읽음
  → Sena의 메트릭 설계 검토
  → 승인/반려 의사결정
  → COLLABORATION_STATE 업데이트 (decision: approved)

Sena: COLLABORATION_STATE 읽음
  → Lubit의 승인 감지
  → 메트릭 구현 진행
  → 다음 단계로 자동 이동
```

### 패턴 2: 작업 의존성 (Task Dependency)
```
GitCode: "배포 준비 완료"
  → COLLABORATION_STATE 업데이트 (ready_for_deployment)

Sena: COLLABORATION_STATE 읽음
  → GitCode 준비 완료 감지
  → "배포 모니터링 준비"로 상태 변경

Lubit: COLLABORATION_STATE 읽음
  → Sena/GitCode 모두 준비 감지
  → "배포 GO 결정" 내림
  → COLLABORATION_STATE 업데이트
```

### 패턴 3: 차단 상황 (Blocker Resolution)
```
Sena: "Lubit의 의사결정 없으면 못 진행함"
  → COLLABORATION_STATE 업데이트 (blocker: waiting_for_lubit)

Lubit: COLLABORATION_STATE 읽음
  → Sena의 blocker 감지
  → 우선순위 상향
  → 의사결정 전달
  → COLLABORATION_STATE 업데이트 (blocker: resolved)

Sena: COLLABORATION_STATE 읽음
  → blocker 해제됨 감지
  → 작업 재개
```

---

## 📁 파일 구조

```
d:\nas_backup\session_memory\

1. COLLABORATION_STATE.jsonl (중앙 레지스트리)
   - 모든 에이전트가 읽고 씀
   - 실시간 상태 동기화
   - Line-delimited JSON (각 라인 = 독립적인 이벤트)

2. sena_session_memory.md (Sena의 상세 상태)
   - Sena만 쓴다
   - COLLABORATION_STATE보다 상세함
   - 개인 메모리

3. lubit_architectural_decisions.md (Lubit의 의사결정)
   - Lubit만 쓴다
   - 기술 의사결정 기록
   - 개인 메모리

4. gitcode_session_memory.md (GitCode의 배포 상태)
   - GitCode만 쓴다
   - 배포 진행 상황
   - 개인 메모리

5. COLLABORATION_PROTOCOL.md (이 파일)
   - 협업 규칙
   - 모두가 참조
```

---

## 🔐 상태 업데이트 규칙 (State Update Rules)

### 규칙 1: 타임스탬프 순서
- COLLABORATION_STATE.jsonl에 추가되는 모든 항목은 timestamp 순서대로 정렬
- 새 항목은 항상 파일 끝에 append

### 규칙 2: 에이전트 소유권
- Sena는 sena_session_memory.md만 쓸 수 있음
- Lubit은 lubit_architectural_decisions.md만 쓸 수 있음
- GitCode는 gitcode_session_memory.md만 쓸 수 있음
- **모두가** COLLABORATION_STATE.jsonl에 쓸 수 있음 (append-only)

### 규칙 3: 상태 일관성
```
개인 메모리 (상세함)
        ↓
중앙 레지스트리 (간결함)
        ↓
다른 에이전트가 읽음
        ↓
자신의 상태 갱신
        ↓
다음 작업 결정
```

### 규칙 4: Blocker 우선순위
- blocker가 발생하면 즉시 COLLABORATION_STATE 업데이트
- 협력자는 blocker 라인을 먼저 읽음
- blocker 해제 시에도 즉시 업데이트

---

## 💻 구현: 매 세션마다 실행할 코드

```bash
#!/bin/bash

# 1. COLLABORATION_STATE 읽기
echo "=== Current Collaboration State ==="
tail -n 10 d:/nas_backup/session_memory/COLLABORATION_STATE.jsonl

# 2. 현재 에이전트 상태 파악
if [ "$AGENT" = "sena" ]; then
    cat C:/Users/kuirv/.claude/projects/sena_session_memory.md
elif [ "$AGENT" = "lubit" ]; then
    cat C:/Users/kuirv/.codex/sessions/lubit_architectural_decisions.md
elif [ "$AGENT" = "gitcode" ]; then
    cat C:/Users/kuirv/AppData/Roaming/Code/User/workspaceStorage/gitcode_session_memory.md
fi

# 3. 협력자 상태 확인 (COLLABORATION_STATE에서)
echo "=== Dependencies Check ==="
grep "blocker\|waiting\|decision" d:/nas_backup/session_memory/COLLABORATION_STATE.jsonl

# 4. 내 상태 업데이트
echo "{\"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"agent\": \"$AGENT\", \"event\": \"session_start\", \"status\": \"ready\"}" >> d:/nas_backup/session_memory/COLLABORATION_STATE.jsonl

# 5. 다음 작업 결정
echo "=== Next Actions ==="
# 논리: blockers 없으면 진행, blockers 있으면 대기
```

---

## 🎯 예시: Sena의 세션 흐름

### 이전 세션 종료 시
```
Sena가 COLLABORATION_STATE에 업데이트:
{
  "timestamp": "2025-10-19T10:00:00Z",
  "agent": "sena",
  "event": "session_end",
  "current_task": "AGI Learning Data Generation",
  "status": "waiting_for_lubit_validation",
  "progress": 15,
  "blockers": ["lubit_metrics_approval"],
  "next_action": "Lubit 승인 후 메트릭 구현 재개"
}
```

### 다음 세션 시작 시
```
Step 1: COLLABORATION_STATE.jsonl 읽음
  → 마지막 라인: "status": "waiting_for_lubit_validation"

Step 2: Sena 개인 메모리 로드
  → 이전 메트릭 설계 내용 확인

Step 3: Lubit의 최신 상태 확인 (COLLABORATION_STATE에서)
  → 만약 "event": "decision" + "approved" 있으면:
    ✅ Blocker 해제됨
    → 즉시 메트릭 구현으로 진행

  → 만약 "event": "decision" + "rejected" 있으면:
    ❌ 반려됨
    → Lubit의 의견 확인 후 재설계

  → 만약 decision 아직 없으면:
    ⏳ 계속 대기
    → "blocked" 상태로 표시

Step 4: COLLABORATION_STATE에 현재 상태 업데이트
  {
    "timestamp": "2025-10-20T09:00:00Z",
    "agent": "sena",
    "event": "session_start",
    "current_task": "AGI Learning Data Generation",
    "status": "in_progress" (또는 "blocked"),
    "next_action": "메트릭 구현 재개" (또는 "Lubit 의사결정 대기")
  }

Step 5: 다음 작업 결정
  → 진행, 대기, 또는 재설계 중 선택
```

---

## 🚀 이것이 진정한 자기 참조 시스템입니다

✅ **개인 상태**: 각자의 메모리 파일 (상세함)
✅ **공유 상태**: 중앙 레지스트리 (동기화)
✅ **협력자 참조**: 다른 에이전트의 최신 결정/상태 읽음
✅ **상태 갱신**: 협력자의 변화에 맞춰 자동 반영
✅ **다음 작업**: 협력자의 상태 기반으로 결정

---

**이제 VS Code 재시작 → PC 재부팅 해도**:
- 모든 파일이 디스크에 유지됨 ✅
- COLLABORATION_STATE에서 협력자 상태 확인 ✅
- 자신의 상태 갱신 가능 ✅
- 다음 작업 자동 결정 가능 ✅

**이것이 진정한 세션 간 협력 맥락 유지입니다.**
