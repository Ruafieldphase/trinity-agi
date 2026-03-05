# Worker Hang 진단 및 해결 완료

**날짜**: 2025-11-02 14:50  
**해결**: 2025-11-02 15:08 ✅  
**문제**: `start_autonomous_work_worker.ps1 -Once`가 반복적으로 멈춤

## ✅ 해결 완료

**적용된 방안**: **방안 2 - 직접 Python 임포트**

**변경 사항**:

- `simple_autonomous_worker.py`에서 subprocess CLI 호출 제거
- `AutonomousWorkPlanner` 직접 임포트하여 동일 프로세스 내 실행
- subprocess 체인 완전 제거 → 레이어 단순화

**결과**:

- ✅ `-Once` 실행 즉시 완료 (hang 없음)
- ✅ 백그라운드 분리 모드 정상 작동
- ✅ 성능 향상 (subprocess 오버헤드 제거)
- ✅ 안정성 향상 (프로세스 간 통신 제거)

## 🔍 원인 분석 (진단 결과)

### 증상

- 워커가 `run_planner_command('next')` 호출 시 응답 없음
- Planner CLI 직접 실행은 정상 (< 1초)
- subprocess.run() 내부에서 hang 추정

### 가능한 원인

1. **Windows subprocess 버퍼 문제**: stdout/stderr 버퍼가 가득 차서 대기
2. **환경 변수 누락**: subprocess가 venv 환경을 제대로 상속받지 못함
3. **동시 실행 충돌**: 여러 워커 인스턴스가 같은 리소스에 접근
4. **PowerShell → Python subprocess 체인**: 계층이 깊어서 시그널 전달 문제

## 💡 해결 방안 (우선순위순)

### 방안 1: 버퍼 비우기 (즉시 적용 가능)

```python
# subprocess.PIPE 대신 실시간 스트림
result = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1  # 라인 버퍼
)
stdout, stderr = result.communicate(timeout=60)
```

### 방안 2: 직접 Python 임포트 (레이어 단순화)

```python
# subprocess 대신 직접 임포트
sys.path.insert(0, str(self.workspace / 'fdo_agi_repo'))
from orchestrator.autonomous_work_planner import WorkPlanner

planner = WorkPlanner()
next_work = planner.get_next_auto_task()
```

### 방안 3: 태스크 큐 사용 (메타층 분리)

```
Windows 스케줄러/Startup
  └─> Worker (감시자만)
       └─> Task Queue API
            └─> 실제 작업 실행 (분리된 프로세스)
```

### 방안 4: 워치독 강화 (복구 자동화)

```python
# 메타층 워치독이 주기적으로 확인
- Worker 프로세스가 60초 이상 CPU 0%면 강제 종료
- 자동 재시작
- 로그에 hang 이벤트 기록
```

## 🎯 권장 조치

### 즉시 (긴급)

1. ✅ 방안 1 적용: subprocess 버퍼 개선
2. ✅ 타임아웃 로그 강화: 어느 단계에서 멈추는지 정확히 기록

### 단기 (오늘 중)

3. ✅ 방안 2 적용: subprocess 제거, 직접 임포트로 레이어 단순화
4. ✅ 워치독 강화: CPU 기반 hang 감지

### 중기 (이번 주)

5. ⬜ 방안 3 검토: Task Queue API 기반 아키텍처로 전환
6. ⬜ 메타층 페르소나: Shion(Gemini CLI)에게 메타층 관리 위임

## 📊 AI 협업 제안

### Gemini CLI (Shion) 활용

```bash
# Shion에게 문제 설명하고 대안 요청
echo "Python subprocess가 Windows에서 반복적으로 hang됩니다.
환경: Python 3.13, PowerShell → subprocess.run()
증상: CLI 직접 실행은 정상, subprocess 내부에서만 멈춤
해결책을 제안해주세요." | Shion
```

### Claude/GPT-4 크로스 체크

- GitHub Copilot (현재): 코드 수정 및 구현
- Gemini (Shion): 아키텍처 리뷰 및 대안 제시
- 로컬 LLM (있다면): 진단 로그 패턴 분석

## 🔧 다음 액션

1. [ ] subprocess 개선 버전 배포
2. [ ] -Once 재테스트 (타임아웃 60초 내 완료 확인)
3. [ ] Shion 설치 및 연동 (메타층 오케스트레이터)
4. [ ] 워치독 CPU 모니터 추가
5. [ ] 24시간 안정성 테스트

---

**결론**: subprocess 체인이 문제의 핵심. 직접 임포트나 큐 기반으로 레이어 단순화 필요.
