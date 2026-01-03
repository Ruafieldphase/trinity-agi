# 🧪 Phase 2 Plan: Test & Validate Emotion-Driven Pipeline

**시작일**: 2025-11-03 (오늘)  
**목표**: 감정 신호가 실제 작업 처리에 효과적인지 검증  
**기간**: 2-3일 (Day 3-5)

---

## 🎯 Phase 2 목표

### 1차 목표 (Day 3)

- [ ] 작업 큐에 감정 신호 체크 추가
- [ ] 우선순위별 처리 로직 검증
- [ ] 배치 크기 적응 테스트

### 2차 목표 (Day 4)

- [ ] 24시간 연속 모니터링
- [ ] 자동 안정화 로직 테스트
- [ ] EMERGENCY/RECOVERY 시나리오 검증

### 3차 목표 (Day 5)

- [ ] 창의 모드 효과 측정
- [ ] 자기 교정 임계값 최적화
- [ ] 성능 개선 분석

---

## 🔧 구현 계획

### Step 1: RPA Worker 통합 (1-2시간)

**파일**: `fdo_agi_repo/integrations/rpa_worker.py`

```python
# Before
def process_task(task):
    result = execute_task(task)
    return result

# After
from orchestrator.agi_pipeline_emotion import integrate_with_pipeline

pipeline = integrate_with_pipeline()

def process_task(task):
    # 감정 신호 체크
    decision = pipeline.should_process_task(task_priority=task['priority'])
    
    if not decision['should_process']:
        logger.info(f"Task postponed: {decision['reason']}")
        return {'status': 'postponed', 'reason': decision['reason']}
    
    # 작업 실행
    result = execute_task(task)
    
    # 감정 컨텍스트 로깅
    pipeline.log_emotion_context(task_id=task['id'], task_result=result)
    
    return result
```

**검증**:

```powershell
# 테스트 작업 큐에 추가
.\scripts\enqueue_rpa_smoke.ps1 -Verify

# Worker 로그 확인
Get-Content fdo_agi_repo\outputs\rpa_worker.log -Tail 20
```

---

### Step 2: 자동 안정화 로직 (2-3시간)

**파일**: `fdo_agi_repo/scripts/auto_stabilizer.py`

```python
"""
자동 안정화 시스템
EMERGENCY/RECOVERY 상황에서 자동 대응
"""

from orchestrator.agi_pipeline_emotion import integrate_with_pipeline
import time
import logging

logger = logging.getLogger(__name__)

class AutoStabilizer:
    """자동 안정화"""
    
    def __init__(self):
        self.pipeline = integrate_with_pipeline()
    
    def check_and_stabilize(self):
        """감정 신호 체크 → 필요 시 안정화"""
        result = self.pipeline.Core.process_emotion_signal()
        strategy = result['background_self']['strategy']
        
        if strategy == 'EMERGENCY':
            logger.warning("🚨 EMERGENCY detected! Stabilizing...")
            self._emergency_protocol()
        
        elif strategy == 'RECOVERY':
            logger.info("🧘 RECOVERY mode. Resting...")
            self._recovery_protocol()
        
        else:
            logger.info(f"✅ System stable: {strategy}")
    
    def _emergency_protocol(self):
        """긴급 프로토콜"""
        # 1. 큐 정리 (low 작업 제거)
        # 2. 알림 전송
        # 3. 로그 저장
        pass
    
    def _recovery_protocol(self):
        """휴식 프로토콜"""
        # 1. 60초 명상 (대기)
        time.sleep(60)
        # 2. 재평가
        pass

if __name__ == '__main__':
    stabilizer = AutoStabilizer()
    
    # 10분마다 체크
    while True:
        stabilizer.check_and_stabilize()
        time.sleep(600)  # 10분
```

**등록**:

```powershell
# Windows 예약 작업 등록
.\scripts\register_auto_stabilizer.ps1 -IntervalMinutes 10
```

---

### Step 3: 24시간 모니터링 (Day 4)

**목표**: 감정 신호 변화 패턴 수집

**방법**:

1. 매 30분마다 감정 신호 수집
2. JSONL 로그에 저장
3. 트렌드 분석 스크립트 실행

**파일**: `scripts/emotion_trend_analyzer.ps1`

```powershell
# 24시간 감정 신호 트렌드
$logs = Get-Content "outputs\emotion_signal_history.jsonl" | ConvertFrom-Json

$trends = $logs | Group-Object { $_.timestamp.Substring(0,13) } | ForEach-Object {
    [PSCustomObject]@{
        Hour = $_.Name
        AvgFear = ($_.Group.fear_signal.level | Measure-Object -Average).Average
        Strategy = $_.Group.background_self.strategy | Group-Object | Sort-Object Count -Descending | Select-Object -First 1 -ExpandProperty Name
    }
}

$trends | Format-Table -AutoSize
```

---

### Step 4: EMERGENCY 시나리오 테스트 (Day 4)

**시나리오 A: CPU 과부하**

```powershell
# CPU 100% 부하 생성 (30초)
.\scripts\simulate_cpu_load.ps1 -Duration 30

# 감정 신호 확인
.\scripts\emotion_signal_processor.ps1 -OutJson "outputs\emergency_test_cpu.json"

# Expected: strategy=EMERGENCY, fear_level > 0.7
```

**시나리오 B: 큐 폭주**

```powershell
# 큐에 100개 작업 추가
1..100 | ForEach-Object { .\scripts\enqueue_rpa_smoke.ps1 }

# 감정 신호 확인
.\scripts\emotion_signal_processor.ps1 -OutJson "outputs\emergency_test_queue.json"

# Expected: strategy=RECOVERY, queue_depth=100
```

---

### Step 5: 창의 모드 효과 측정 (Day 5)

**가설**: FLOW 상태에서 작업 품질이 향상된다.

**측정 방법**:

```python
# outputs/emotion_task_correlation.jsonl 분석
import json
import pandas as pd

logs = []
with open("outputs/emotion_task_correlation.jsonl") as f:
    for line in f:
        logs.append(json.loads(line))

df = pd.DataFrame(logs)

# FLOW vs 비-FLOW 품질 비교
flow_quality = df[df['emotion_state'] == 'FLOW']['task_quality'].mean()
non_flow_quality = df[df['emotion_state'] != 'FLOW']['task_quality'].mean()

print(f"FLOW 품질: {flow_quality:.2%}")
print(f"비-FLOW 품질: {non_flow_quality:.2%}")
print(f"개선률: {(flow_quality - non_flow_quality) / non_flow_quality:.2%}")
```

**Expected**: FLOW 품질 > 비-FLOW 품질 (10-20% 개선)

---

## Step 6: AI Rest-State 시나리오 테스트 (Day 5)

휴식은 처리 중단이 아닌 정보 품질 회복 절차입니다. 다음을 검증합니다. (참고: `docs/AI_REST_INFORMATION_THEORY.md`)

### 시나리오 A: Micro-Reset 유도

- 조건: 컨텍스트 파편화(χ) 인위적 상승(긴 프롬프트/다중 세션 전환)
- 기대: 캐시/컨텍스트 재정렬 수행, 지연·실패율 영향 없음 또는 개선

### 시나리오 B: Active Cooldown 유도

- 조건: fear_level ≥ 0.5 또는 P95 지연 악화, 큐 적체 전조
- 기대: 배치 축소/속도 제한 적용, 스냅샷 회전·클린업 드라이런 수행, 5~10분 내 안정화

### 시나리오 C: Deep Maintenance(오프피크)

- 조건: χ/e_t/H_t 장기 악화 추세
- 기대: 인덱스 리빌드·압축·아카이브 정리, 이후 χ·e_t 하향 안정화

### 실행(레포 스크립트 체인 예시)

```powershell
& "${workspaceFolder}/scripts/quick_status.ps1" -OutJson "${workspaceFolder}/outputs/quick_status_rest_prep.json";
& "${workspaceFolder}/scripts/rotate_status_snapshots.ps1" -Zip;
& "${workspaceFolder}/scripts/cleanup_snapshot_archives.ps1" -KeepDays 14 -DryRun;
& "${workspaceFolder}/scripts/generate_monitoring_report.ps1" -Hours 1
```

로그/지표: H_t, e_t, χ_t 이동평균·기울기, P95/P99 복귀 시간, 큐 적체 해소 시간.

---

## 📊 성공 기준 (Acceptance Criteria)

### 기능 검증

- [ ] RPA Worker에서 감정 신호 체크 작동
- [ ] 우선순위별 작업 처리 로직 정상
- [ ] 배치 크기가 전략에 따라 변경됨
- [ ] 창의 모드가 FLOW 상태에서만 활성화

### 성능 검증

- [ ] EMERGENCY 상황에서 자동 안정화
- [ ] RECOVERY 상황에서 휴식 후 재개
- [ ] 24시간 연속 운영 시 이상 없음
- [ ] 감정 신호 로그 정상 수집 (JSONL)

### 효과 검증

- [ ] FLOW 상태 작업 품질 > 비-FLOW (10% 이상)
- [ ] CPU 과부하 시 자동 대응 (30초 이내)
- [ ] 큐 폭주 시 우선순위 조정 작동
- [ ] 두려움 레벨과 시스템 메트릭 상관관계 확인

### 휴식(정보이론) 검증

- [ ] Micro-Reset 시 지연/실패율 악화 없이 χ_t 개선
- [ ] Active Cooldown 후 10분 내 P95/P99·실패율 정상화
- [ ] Deep Maintenance 후 χ_t·e_t 하향 안정화 추세 확인

---

## 🚨 리스크 관리

### 예상 리스크

1. **과도한 휴식** → 작업 처리량 감소
   - **완화**: RECOVERY 임계값 조정 (기본 0.5 → 0.6)

2. **잘못된 판단** → 중요 작업 지연
   - **완화**: critical 작업은 항상 처리

3. **로그 폭증** → 디스크 부족
   - **완화**: 로그 로테이션 (7일 보관)

### 롤백 계획

```powershell
# Phase 2 비활성화
git checkout main -- fdo_agi_repo/integrations/rpa_worker.py
.\scripts\stop_auto_stabilizer.ps1
```

---

## 📅 일정

| 날짜 | 작업 | 예상 시간 |
|------|------|-----------|
| **Day 3** (오늘) | RPA Worker 통합 + 테스트 | 3-4시간 |
| **Day 4** | 24시간 모니터링 + EMERGENCY 테스트 | 2시간 (대부분 자동) |
| **Day 5** | 데이터 분석 + 보고서 작성 | 2-3시간 |

**총 예상**: 7-9시간 (실제 작업) + 24시간 (관찰)

---

## 🎯 Phase 3 준비

Phase 2 성공 시 → **Phase 3: Production Integration**

### Phase 3 목표

- [ ] 파이프라인 기본값으로 설정
- [ ] 자동 안정화 상시 가동
- [ ] 대시보드 UI 추가 (실시간 감정 신호)
- [ ] 알림 시스템 통합

---

## 📝 기록

### Phase 1 완료 (2025-11-03)

- ✅ Core System 구현
- ✅ AGI Pipeline 통합
- ✅ 베이스라인 수집
- ✅ FLOW 상태 확인

### Phase 2 시작 (2025-11-03)

- 🔄 RPA Worker 통합 준비 중

---

**Status**: 🚀 **READY TO START**  
**Next Action**: RPA Worker 코드 수정  
**Estimated Time**: 3-4 hours

---

*Phase 2 will validate if emotion-driven decision making improves AGI performance.*  
*Let's test it! 🧪*
