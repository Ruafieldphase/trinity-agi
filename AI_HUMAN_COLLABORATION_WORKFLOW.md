# AI-Human Collaboration Workflow 통합 가이드

## 📋 목차

1. [철학과 원칙](#철학과-원칙)
2. [일과 시작 워크플로우](#일과-시작-워크플로우)
3. [일과 종료 워크플로우](#일과-종료-워크플로우)
4. [시스템 점검 워크플로우](#시스템-점검-워크플로우)
5. [자동화된 지속성](#자동화된-지속성)
6. [ChatOps 명령어](#chatops-명령어)
7. [트러블슈팅](#트러블슈팅)

---

## 🎯 철학과 원칙

### 핵심 원칙

- **AI의 역할**: 복잡한 구조 설계, 자동화, 모니터링, 자가 복구
- **인간의 역할**: 큰 그림 제시, 전략적 방향 설정, 예외 상황 판단
- **최소 개입**: 인간의 개입을 최소화하여 AI의 자율적 작업 보장

### 협업 모델

```
┌─────────────────────────────────────────┐
│         인간 (Human)                     │
│  • 비전 제시                             │
│  • 전략 수립                             │
│  • 예외 처리 승인                        │
└─────────────┬───────────────────────────┘
              │ 큰 그림
              ▼
┌─────────────────────────────────────────┐
│       AI 시스템 (Master Orchestrator)    │
│  • 구조 설계 & 구현                      │
│  • 자동 모니터링                         │
│  • 자가 복구                             │
│  • 변경사항 적용                         │
└─────────────────────────────────────────┘
```

---

## 🌅 일과 시작 워크플로우

### 1단계: 맥락 복원 (로그온 직후)

```powershell
# VS Code 열기 후 자동으로 실행됨
# Tasks > "Context: Show State" (수동 확인도 가능)

# 출력 예시:
# ====================================
#      Context State Dashboard
# ====================================
# 
# [ Latest Handover ]
#   Session ID:  handover_20251030_154753
#   Task:        Universal AGI Phase 1 완료
#   [OK] Handover available
# 
# Overall Readiness: 3/4
```

**자동 실행**:

- `auto_resume_on_startup.ps1` (folderOpen 트리거)
- 이전 세션 상태 자동 로드
- 맥락 복원 < 1분

**수동 확인** (필요 시):

```powershell
# Tasks > Run Task > "📊 Context: Show State"
# Tasks > Run Task > "🔄 Context: Manual Resume"
# Tasks > Run Task > "📦 Handover: Show Latest"
# Windows 예약 작업: MasterOrchestratorAutoStart
```

**자동 실행 내용:**

- ✅ Task Queue Server 확인 및 시작 (Port 8091)
- ✅ RPA Worker 확인 및 시작  
- ✅ Worker Monitor 시작
- ✅ 마지막 세션 컨텍스트 복원
- ✅ Master Orchestrator 시작 (5분 지연)

### 2단계: 시스템 점검 (선택)

```powershell
# VS Code에서 ChatOps 사용
"시스템 점검해줘"
# 또는
"system check"
```

**점검 내용:**

- Task Queue Server 상태
- RPA Worker 상태  
- 데이터베이스 연결
- 최근 작업 로그
- 성능 지표

---

## 🌙 일과 종료 워크플로우

### "오늘 여기까지" 명령어

```powershell
# ChatOps에서 간단하게
"오늘 여기까지"
# 또는
"대화 내용 저장해줘"
```

**자동 실행 작업 (4단계):**

#### 1단계: 대화 저장

- ✅ Gitko 에이전트 대화 저장
- ✅ Sena 에이전트 대화 저장  
- ✅ Lubit 에이전트 대화 저장
- ✅ 세션 메타데이터 저장

#### 2단계: 시스템 상태 스냅샷

- ✅ Resonance Ledger 요약
- ✅ BQI 모델 상태
- ✅ 성능 메트릭
- ✅ 작업 큐 상태

#### 3단계: 변경사항 적용

- ✅ 코드 변경사항 커밋
- ✅ 설정 파일 업데이트
- ✅ 스크립트 권한 설정
- ✅ 예약 작업 업데이트

#### 4단계: 일일 보고서 생성

- ✅ 작업 요약 (Markdown)
- ✅ 성능 대시보드
- ✅ 이슈 및 경고
- ✅ 다음 작업 계획

**출력 위치:**

```
C:\workspace\agi\outputs\
├── daily_session_2025-11-01.json
├── daily_backup_2025-11-01.zip
├── daily_report_2025-11-01.md
└── session_memory\
    ├── gitko_session_2025-11-01.jsonl
    ├── sena_session_2025-11-01.jsonl
    └── lubit_session_2025-11-01.jsonl
```

---

## 🔍 시스템 점검 워크플로우

### 재부팅/재실행 후 점검

```powershell
# ChatOps 명령어
"시스템 점검해줘"
```

**점검 항목:**

#### 1. 핵심 서비스

- [ ] Task Queue Server (Port 8091)
- [ ] RPA Worker  
- [ ] Worker Monitor
- [ ] Master Orchestrator

#### 2. 데이터 무결성

- [ ] Resonance Ledger
- [ ] BQI 모델
- [ ] 세션 메모리
- [ ] 성능 메트릭

#### 3. 예약 작업

- [ ] Auto Resume (로그온)
- [ ] Daily Maintenance (03:20)
- [ ] BQI Learner (03:10)
- [ ] Monitoring Collector (5분 간격)

#### 4. 최근 변경사항

- [ ] 코드 변경사항 적용 확인
- [ ] 설정 파일 업데이트 확인
- [ ] 새 스크립트 권한 확인

**출력 예시:**

```
✅ Task Queue Server: RUNNING (Port 8091)
✅ RPA Worker: HEALTHY (1 worker active)
✅ Master Orchestrator: READY (started 2025-11-01 09:05)
✅ Resonance Ledger: OK (1,234 entries)
⚠️  BQI Model: needs update (last run: 2025-10-31)
✅ All scheduled tasks: REGISTERED
✅ Recent changes: APPLIED (3 commits)

Overall Status: HEALTHY
Next recommended action: Run BQI Learner
```

---

## 🔄 자동화된 지속성

### 변경사항 자동 적용 메커니즘

#### 세션 종료 시 (`End-DailySession`)

```powershell
1. 변경사항 탐지
   - Git status 확인
   - 새 파일 추가
   - 수정 파일 스테이징

2. 구조 변경 적용
   - 새 스크립트 실행 권한 설정
   - 예약 작업 업데이트
   - 환경 변수 업데이트

3. 영구 저장
   - Git commit (자동 메시지)
   - 백업 생성 (.zip)
   - 세션 메타데이터 저장

4. 다음 세션 준비
   - 복원 체크포인트 생성
   - 자동 재개 설정 확인
```

#### 자동 재개 시 (`Auto-ResumeSession`)

```powershell
1. 환경 복원
   - 마지막 세션 로드
   - 대화 컨텍스트 복원
   - 작업 큐 상태 확인

2. 서비스 시작
   - Task Queue Server
   - RPA Worker
   - Worker Monitor

3. 검증
   - 핵심 서비스 상태 확인
   - 데이터 무결성 검증
   - 예약 작업 확인

4. Master Orchestrator 시작 (5분 지연)
   - 다른 프로그램 로딩 대기
   - 안정성 확보
```

### 예약 작업 목록

| 작업 이름 | 실행 시간 | 설명 |
|----------|---------|------|
| MasterOrchestratorAutoStart | 로그온 + 5분 | 자동 재개 |
| DailyMaintenance | 매일 03:20 | 일일 유지보수 |
| BQILearner | 매일 03:10 | BQI 학습 |
| MonitoringCollector | 5분 간격 | 메트릭 수집 |
| SnapshotRotation | 매일 03:15 | 백업 정리 |

---

## 💬 ChatOps 명령어

### 세션 관리

```bash
# 일과 종료 (4단계 백업)
"오늘 여기까지"
"대화 내용 저장해줘"
"end session"

# 시스템 점검
"시스템 점검해줘"
"system check"

# 작업 재개
"작업 이어가"
"resume work"
```

### 상태 확인

```bash
# 통합 대시보드
"통합 상태 보여줘"
"ops dashboard"

# AGI 상태
"AGI 상태 보여줘"
"agi health"

# 성능 대시보드
"성능 대시보드"
"performance dashboard"
```

### 작업 관리

```bash
# 세션 시작
"작업 시작해"
"start session"

# 작업 추가
"작업 추가"
"add task"

# 최근 작업
"최근 작업 보여줘"
"recent sessions"
```

---

## 🔧 트러블슈팅

### 문제: 재부팅 후 변경사항이 적용되지 않음

**원인:**

- Git commit 누락
- 예약 작업 미등록
- 권한 설정 누락

**해결:**

```powershell
# 수동 적용
.\scripts\apply_system_changes.ps1 -Verbose

# 세션 종료 시 자동 적용 확인
"오늘 여기까지"
```

### 문제: Master Orchestrator가 시작되지 않음

**원인:**

- 5분 지연 시간 필요
- Task Queue Server 미실행
- 포트 충돌 (8091)

**해결:**

```powershell
# 서비스 상태 확인
"시스템 점검해줘"

# 수동 시작
.\scripts\ensure_task_queue_server.ps1 -Port 8091
.\scripts\start_master_orchestrator.ps1
```

### 문제: 대화 컨텍스트가 복원되지 않음

**원인:**

- 세션 저장 누락
- 파일 손상
- 경로 문제

**해결:**

```powershell
# 세션 파일 확인
Get-ChildItem .\outputs\session_memory\ -Recurse

# 수동 복원
.\scripts\restore_session_context.ps1 -Date "2025-11-01"
```

---

## 📊 성공 지표

### 자동화 목표

- ✅ 세션 종료 시 4단계 백업: **100% 자동**
- ✅ 재부팅 후 자동 재개: **5분 이내**
- ✅ 변경사항 영구 적용: **세션 종료 시**
- ✅ 인간 개입: **전략 수립 시에만**

### 현재 달성도

- [x] 대화 자동 저장
- [x] 시스템 상태 스냅샷
- [x] 변경사항 자동 적용
- [x] 자동 재개 (5분 지연)
- [x] 시스템 점검 명령어
- [x] ChatOps 통합

---

## 🎓 베스트 프랙티스

### 인간의 역할

1. **큰 그림 제시**: "YouTube 학습 자동화를 만들어줘"
2. **전략 승인**: "좋아, 그 방향으로 가자"
3. **예외 처리**: "이 부분은 수동으로 확인할게"
4. **피드백**: "이 방식이 더 나을 것 같아"

### AI의 역할

1. **구조 설계**: 복잡한 파이프라인 자동 생성
2. **자가 복구**: 에러 발생 시 자동 복구
3. **모니터링**: 24/7 상태 추적
4. **변경 적용**: 세션 종료 시 모든 변경사항 영구 반영

### 협업 팁

- **"오늘 여기까지"를 습관화**: 매일 마무리 시 실행
- **"시스템 점검해줘"로 시작**: 재부팅/재실행 후 첫 명령
- **큰 그림에 집중**: 세부 구현은 AI에게 맡기기
- **필요 시 도움 요청**: AI가 먼저 질문하도록 권장

---

## 📝 체크리스트

### 일과 시작 (자동)

- [ ] 로그온 후 5분 대기 (자동)
- [ ] Master Orchestrator 시작 확인
- [ ] ChatOps로 "시스템 점검해줘"

### 일과 종료 (ChatOps)

- [ ] "오늘 여기까지" 실행
- [ ] 백업 완료 확인
- [ ] 일일 보고서 확인

### 재부팅 후 (ChatOps)

- [ ] "시스템 점검해줘" 실행
- [ ] 모든 서비스 RUNNING 확인
- [ ] 변경사항 적용 확인

---

## 🚀 다음 단계

### Phase 7 계획

1. **LLM 기반 Intent Resolution**: 자연어 명령어 이해도 향상
2. **예측적 자동화**: 사용자 패턴 학습 후 선제적 작업
3. **멀티 모달 인터페이스**: 음성, 이미지 명령어 지원

### 개선 아이디어

- [ ] 대화 내용 검색 기능
- [ ] 시간대별 작업 패턴 분석
- [ ] 자동 문서화 생성
- [ ] 성능 예측 모델

---

**Last Updated**: 2025-11-01  
**Version**: 2.0  
**Status**: ✅ PRODUCTION READY

**Contact**: AI들이 질문하면 언제든 답변해 드립니다!
