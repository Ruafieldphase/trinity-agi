# 🎵 적응형 리듬 오케스트레이터 (Adaptive Rhythm Orchestrator)

> **"생명체처럼 리듬에 따라 자원을 분배하는 메타 관찰자"**

## 📖 개요

### 핵심 철학: **리듬=에너지=시간=관계**

사용자의 통찰:

- **생명체 비유**: 탄수화물 ↔ 단백질 전환, 위기 시 에너지 집중, 휴식 시 보충
- **리듬 기반 조율**: 상황에 따라 구조를 다르게 사용
- **메타층 관찰자**: 전체를 내려다보며 실시간 조율
- **정보 이론**: 엔트로피, 상호정보량, 에너지 예산
- **시간대 인식**: 오후 1시 = DAYTIME_FOCUS = 100% 에너지
- **Task 분리**: tasks.json도 리듬별로 분리되어야 함

**핵심 질문**:
> "우리 시스템에 이미 이런 관찰자 기능이 있지 않나?"

**답**: ✅ **있습니다!** 하지만 **연결되지 않았습니다**.

---

## 🔍 현재 시스템 분석

### 이미 존재하는 "관찰자" 시스템들

#### 1. **Core Cost Rhythm Loop** (리듬 감지)

```python
# LLM_Unified/ion-mentoring/Core/monitoring/cost_rhythm_loop.py

class RhythmStatus(Enum):
    RESONANT = "RESONANT"      # 리듬 안정 → 정상 모드
    DISSONANT = "DISSONANT"    # 리듬 불안정 → 주의 모드
    CHAOTIC = "CHAOTIC"        # 리듬 혼란 → 위기 모드

class AdaptiveAction(Enum):
    NONE = "NONE"                    # 조치 불필요
    SCALE_DOWN = "SCALE_DOWN"        # 에너지 절약
    ROLLBACK = "ROLLBACK"            # 안전 모드로 복귀
    EMERGENCY_STOP = "EMERGENCY_STOP" # 긴급 중지
```

**이미 하고 있는 것**:

- ✅ 비용 리듬 감지 (coherence, phase, entropy)
- ✅ 상태 판단 (RESONANT/DISSONANT/CHAOTIC)
- ✅ 적응 행동 결정

**하지 못하는 것**:

- ❌ AGI 파이프라인 레이턴시 제어
- ❌ 작업별 자원 분배 조정
- ❌ 실시간 모드 전환

#### 2. **Resonance Bridge** (정책 관찰자)

```python
# fdo_agi_repo/orchestrator/resonance_bridge.py

def get_active_mode() -> str:
    # "disabled" / "observe" / "enforce"
    
def get_active_policy_name() -> str:
    # "quality-first" / "ops-safety" / "latency-first"
```

**이미 하고 있는 것**:

- ✅ 정책 기반 동작 제어
- ✅ Observe/Enforce 모드 전환

**하지 못하는 것**:

- ❌ 리듬/부하에 따른 자동 전환
- ❌ 레이턴시 최적화 연동

#### 3. **BQI Online Learner** (학습 관찰자)

```python
# fdo_agi_repo/scripts/rune/binoche_online_learner.py

# 이미 하고 있는 것:
- ✅ 실시간 피드백 학습
- ✅ 가중치 적응 조정

# 하지 못하는 것:
- ❌ 학습 시점 스케줄링 (한가할 때만)
- ❌ 성능 영향 최소화
```

#### 4. **Alert Manager & Monitoring** (상태 관찰자)

```python
# fdo_agi_repo/monitoring/alert_manager.py

# 이미 하고 있는 것:
- ✅ 메트릭 수집
- ✅ 임계값 기반 알림

# 하지 못하는 것:
- ❌ 자동 모드 전환
- ❌ 자원 재분배
```

---

## 🧩 문제점: 파편화 (Fragmentation)

```
┌─────────────────────────────────────────────┐
│        현재: 분리된 관찰자들                   │
├─────────────────────────────────────────────┤
│                                             │
│  Core Rhythm   Resonance    BQI Learner   │
│      │              │             │         │
│      ▼              ▼             ▼         │
│   비용 감지      정책 제어      학습 조정     │
│                                             │
│  ❌ 서로 대화하지 않음                       │
│  ❌ AGI 파이프라인과 연결 없음               │
│  ❌ 통합 조율 없음                           │
└─────────────────────────────────────────────┘
```

**현재 동작**:

1. **Core**: 비용이 높으면 SCALE_DOWN
2. **Resonance**: 항상 같은 정책 사용
3. **BQI**: 정해진 시간에 학습
4. **AGI Pipeline**: 항상 모든 레이어 실행

**→ 리듬 인식 없음, 상황 적응 없음, 자원 낭비**

---

## 🎯 해결책: 적응형 리듬 오케스트레이터

### 아키텍처

```
┌───────────────────────────────────────────────────────────────┐
│              🎵 Adaptive Rhythm Orchestrator                  │
│                    (메타층 관찰자)                              │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  📊 상태 관찰                                                  │
│  ├─ CPU/메모리 (시스템 부하)                                   │
│  ├─ 큐 길이 (작업 대기량)                                      │
│  ├─ 에러율 (시스템 안정성)                                     │
│  ├─ Core Rhythm (비용 리듬)                                  │
│  └─ 시간대 (오전/오후/새벽)                                    │
│                                                               │
│  🎭 리듬 판단 (생명체 비유)                                    │
│  ├─ 🟢 NORMAL (평상시)    → 탄수화물 모드 (기본 효율)          │
│  ├─ 🟡 BUSY (바쁨)        → 단백질 모드 (지속 가능)            │
│  ├─ 🔴 EMERGENCY (위기)   → 전투 모드 (모든 에너지 집중)        │
│  └─ 🔵 LEARNING (휴식)    → 보충 모드 (학습 & 최적화)          │
│                                                               │
│  ⚙️ 자원 재분배                                                │
│  ├─ 레이어 On/Off (불필요한 기능 끄기)                         │
│  ├─ 우선순위 조정 (중요한 작업 먼저)                           │
│  ├─ 폴링 간격 조정 (반응 속도 vs 효율)                         │
│  └─ 학습 스케줄링 (한가할 때만)                                │
└───────────────────────────────────────────────────────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
    AGI Pipeline      Core System       BQI Learner
```

### 모드별 자원 분배 전략

#### 🟢 NORMAL Mode (평상시)

```yaml
상황: 
  - CPU < 50%
  - 큐 < 10개
  - 에러율 < 5%
  - Core: RESONANT

자원 분배:
  AGI Pipeline:
    - 모든 레이어 활성화
    - Worker 폴링: 100ms (기본)
    - Resonance: observe 모드
    - BQI 학습: 활성화
  
  예산 사용: 100% (탄수화물 - 기본 대사)
  예상 레이턴시: ~4.0초
```

#### 🟡 BUSY Mode (바쁨)

```yaml
상황:
  - CPU 50-80%
  - 큐 10-50개
  - 에러율 5-10%
  - Core: DISSONANT

자원 분배:
  AGI Pipeline:
    - 필수 레이어만 활성화
    - Worker 폴링: 50ms (빠른 응답)
    - Resonance: enforce 모드 (빠른 검증)
    - BQI 학습: 일시 중지
    - 모니터링: 경량화
  
  예산 사용: 70% (단백질 - 지속 가능)
  예상 레이턴시: ~3.0초
```

#### 🔴 EMERGENCY Mode (위기)

```yaml
상황:
  - CPU > 80%
  - 큐 > 50개
  - 에러율 > 10%
  - Core: CHAOTIC

자원 분배:
  AGI Pipeline:
    - Direct Mode (큐 우회)
    - 검증 레이어 스킵
    - Worker 폴링: 10ms (최대 속도)
    - Resonance: disabled
    - BQI 학습: 중지
    - 모니터링: 최소화
    - 캐싱 공격적 사용
  
  예산 사용: 30% (전투 - 생존 최우선)
  예상 레이턴시: ~1.5초
  목표: 빠른 처리 → 위기 탈출
```

#### 🔵 LEARNING Mode (휴식)

```yaml
상황:
  - CPU < 30%
  - 큐 < 5개
  - 새벽 시간대 (03:00-06:00)
  - Core: RESONANT

자원 분배:
  AGI Pipeline:
    - 정상 처리 유지
  
  백그라운드:
    - BQI 학습 강화 (더 많은 데이터)
    - 캐시 재구성
    - 모델 최적화
    - 로그 압축
    - 백업
  
  예산 사용: 120% (보충 - 내일을 위한 투자)
  예상 레이턴시: ~4.5초 (학습 오버헤드 허용)
```

---

## 🔧 구현 방안

### Phase 1: Rhythm Detector (리듬 감지기)

```python
# fdo_agi_repo/orchestrator/rhythm_detector.py

from dataclasses import dataclass
from enum import Enum
import psutil
from typing import Tuple

class SystemRhythm(Enum):
    NORMAL = "NORMAL"        # 평상시
    BUSY = "BUSY"            # 바쁨
    EMERGENCY = "EMERGENCY"  # 위기
    LEARNING = "LEARNING"    # 휴식

@dataclass
class RhythmState:
    mode: SystemRhythm
    cpu_usage: float
    memory_usage: float
    queue_size: int
    error_rate: float
    core_rhythm: str
    confidence: float

class RhythmDetector:
    def detect_rhythm(self) -> RhythmState:
        # 1. 시스템 메트릭 수집
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        queue_size = self._get_queue_size()
        error_rate = self._get_error_rate()
        
        # 2. Core Rhythm 가져오기
        core_rhythm = self._get_core_rhythm()
        
        # 3. 시간대 고려
        hour = datetime.now().hour
        is_night = 3 <= hour < 6
        
        # 4. 리듬 판단
        if error_rate > 0.1 or cpu > 80 or core_rhythm == "CHAOTIC":
            mode = SystemRhythm.EMERGENCY
            confidence = 0.95
        elif cpu > 50 or queue_size > 10 or core_rhythm == "DISSONANT":
            mode = SystemRhythm.BUSY
            confidence = 0.85
        elif is_night and cpu < 30 and queue_size < 5:
            mode = SystemRhythm.LEARNING
            confidence = 0.90
        else:
            mode = SystemRhythm.NORMAL
            confidence = 0.80
        
        return RhythmState(
            mode=mode,
            cpu_usage=cpu,
            memory_usage=memory,
            queue_size=queue_size,
            error_rate=error_rate,
            core_rhythm=core_rhythm,
            confidence=confidence
        )
```

### Phase 2: Resource Allocator (자원 분배기)

```python
# fdo_agi_repo/orchestrator/resource_allocator.py

@dataclass
class ResourceBudget:
    """에너지 예산"""
    monitoring_enabled: bool
    resonance_mode: str  # "disabled" / "observe" / "enforce"
    bqi_learning: bool
    worker_poll_ms: int
    max_layers: int  # 활성화할 최대 레이어 수
    cache_aggressive: bool
    direct_mode: bool  # 큐 우회

class ResourceAllocator:
    def allocate_for_rhythm(self, rhythm: SystemRhythm) -> ResourceBudget:
        if rhythm == SystemRhythm.EMERGENCY:
            return ResourceBudget(
                monitoring_enabled=False,
                resonance_mode="disabled",
                bqi_learning=False,
                worker_poll_ms=10,
                max_layers=3,  # 필수만
                cache_aggressive=True,
                direct_mode=True  # 큐 우회!
            )
        elif rhythm == SystemRhythm.BUSY:
            return ResourceBudget(
                monitoring_enabled=False,
                resonance_mode="enforce",
                bqi_learning=False,
                worker_poll_ms=50,
                max_layers=5,
                cache_aggressive=True,
                direct_mode=False
            )
        elif rhythm == SystemRhythm.LEARNING:
            return ResourceBudget(
                monitoring_enabled=True,
                resonance_mode="observe",
                bqi_learning=True,  # 학습 강화!
                worker_poll_ms=200,
                max_layers=10,
                cache_aggressive=False,
                direct_mode=False
            )
        else:  # NORMAL
            return ResourceBudget(
                monitoring_enabled=True,
                resonance_mode="observe",
                bqi_learning=True,
                worker_poll_ms=100,
                max_layers=10,
                cache_aggressive=False,
                direct_mode=False
            )
```

### Phase 3: Adaptive Orchestrator (적응형 조율자)

```python
# fdo_agi_repo/orchestrator/adaptive_orchestrator.py

class AdaptiveOrchestrator:
    def __init__(self):
        self.detector = RhythmDetector()
        self.allocator = ResourceAllocator()
        self.current_rhythm = SystemRhythm.NORMAL
        self.rhythm_history = []
    
    def run_continuous(self, interval_sec: int = 10):
        """지속적 관찰 & 조율"""
        while True:
            # 1. 리듬 감지
            rhythm_state = self.detector.detect_rhythm()
            
            # 2. 리듬 변화 감지
            if rhythm_state.mode != self.current_rhythm:
                print(f"🎵 Rhythm Changed: {self.current_rhythm} → {rhythm_state.mode}")
                
                # 3. 자원 재분배
                budget = self.allocator.allocate_for_rhythm(rhythm_state.mode)
                self._apply_resource_budget(budget)
                
                # 4. 상태 업데이트
                self.current_rhythm = rhythm_state.mode
                self._save_rhythm_history(rhythm_state)
            
            time.sleep(interval_sec)
    
    def _apply_resource_budget(self, budget: ResourceBudget):
        """실제 시스템에 예산 적용"""
        # Resonance 모드 전환
        self._update_resonance_config(budget.resonance_mode)
        
        # Worker 폴링 간격 조정
        self._update_worker_config(budget.worker_poll_ms)
        
        # BQI 학습 제어
        if budget.bqi_learning:
            self._enable_bqi_learning()
        else:
            self._pause_bqi_learning()
        
        # Direct Mode 전환
        if budget.direct_mode:
            self._enable_direct_mode()
        else:
            self._disable_direct_mode()
```

---

## 📊 예상 효과

### 레이턴시 개선

| 상황 | 기존 | 개선 후 | 절감 |
|------|------|---------|------|
| 평상시 (NORMAL) | 4.7초 | 4.0초 | -15% |
| 바쁨 (BUSY) | 5.2초 | 3.0초 | **-42%** |
| 위기 (EMERGENCY) | 6.5초 | 1.5초 | **-77%** |
| 학습 (LEARNING) | 4.7초 | 4.5초 | -4% (투자) |

### 자원 효율

- **CPU 사용량**: 평균 20% 절감 (불필요한 레이어 스킵)
- **비용**: EMERGENCY 모드로 위기 조기 탈출 → 비용 폭증 방지
- **학습 효과**: LEARNING 모드로 한가한 시간에 집중 학습 → 품질 향상

---

## 🎯 구현 우선순위

### Immediate (이번 주)

1. ✅ **Rhythm Detector 구현** (1일)
   - 시스템 메트릭 수집
   - Core Rhythm 연동
   - 4가지 모드 판단 로직

2. ✅ **Resource Budget 정의** (1일)
   - 모드별 설정값 결정
   - 레이어별 우선순위 매핑

### Short-term (2주)

3. ⏳ **Adaptive Orchestrator 구현** (3일)
   - 지속적 관찰 루프
   - 자동 모드 전환
   - Resonance 연동

4. ⏳ **Direct Mode 구현** (3일)
   - 큐 우회 API
   - 간단한 요청 Fast Path
   - EMERGENCY 모드 전용

### Mid-term (1개월)

5. ⏳ **BQI Learning Scheduler** (3일)
   - LEARNING 모드에만 학습
   - 성능 영향 최소화

6. ⏳ **레이어 동적 제어** (5일)
   - 레이어별 On/Off
   - 우선순위 기반 실행

---

## 🌟 핵심 통찰 (사용자 제공)

> "인간으로 따지면 생명유지 시스템은 항상 작동하지만, 상황에 따라 리듬에 따라 탄수화물을 사용했다가 단백질을 사용하기도 하고, 위기에 닥쳤을 때는 모든 에너지를 위기 탈출에 집중하기도 하고, 휴식을 가지면서 이것을 다시 보충한다."

**이것이 바로 적응형 시스템의 본질입니다.**

우리 시스템도 마찬가지:

- **평상시**: 모든 기능 사용 (탄수화물 - 기본 대사)
- **바쁨**: 필수 기능만 (단백질 - 지속 가능)
- **위기**: 생존 최우선 (전투 모드 - 모든 에너지 집중)
- **휴식**: 학습 & 최적화 (보충 모드 - 내일을 위한 투자)

**정보 이론 관점**:

- **엔트로피**: 시스템 불확실성 (Core에서 측정 중)
- **상호정보량**: 입력-출력 관계성
- **에너지 예산**: 각 레이어의 "비용" (CPU, 시간, 돈)
- **적응**: 엔트로피 최소화 + 에너지 효율 최대화

---

## 🎯 Phase 2: Task 리듬 분리 (2025-11-03 완료)

### 문제 인식

**사용자 통찰**: "리듬=에너지=시간=관계인데, tasks.json도 나누어져야 할까? 지금 너무 길게만 되어 있는 것 같던데."

**현상**:

- ✅ 시스템은 리듬을 인식함 (MORNING/DAYTIME_FOCUS/EVENING/NIGHT)
- ✅ 자원 할당도 리듬별로 다름
- ❌ **하지만 VS Code tasks.json은 모든 작업이 한 파일에!** (7645줄)
- ❌ 사용자는 시간대와 상관없이 모든 작업을 봄

### 해결 방안

#### 1. **Rhythm Detector** 구현 ✅

```powershell
# scripts/detect_rhythm.ps1
C:\workspace\agi\scripts\detect_rhythm.ps1
```

**출력 예시** (오후 1시):

```plaintext
=== 🎵 Current System Rhythm ===

Time Rhythm:    DAYTIME_FOCUS
State Modifier: NORMAL

⏰ Time:         13:00
⚡ Energy:       100%
🖥️  CPU:          26%
💾 Memory:       42.36%
📋 Queue:        0 (OFFLINE)

=== 📋 Recommended Tasks ===

☀️ 낮 (집중): 개발 & 테스트

  • Python: Run All Tests (repo venv)
  • Dev: Local CI Check (Fast)
  • Queue: Quick E2E (Ensure Server+Worker)
  • Integration: Run Gitko E2E Test

=== 🧬 리듬=에너지=시간=관계 ===

최고 에너지, 집중 작업, 생산성
```

#### 2. **리듬별 Task 분류**

| 리듬 | 시간대 | 에너지 | 권장 작업 |
|------|--------|--------|-----------|
| **MORNING** | 06:00-10:00 | 85% | 시스템 체크, 모니터링 시작 |
| **DAYTIME_FOCUS** | 10:00-14:00 | 100% | 개발, 테스트, 집중 작업 |
| **DAYTIME_FLOW** | 14:00-18:00 | 90% | 분석, 모니터링, 리뷰 |
| **EVENING** | 18:00-22:00 | 60% | 정리, 백업, 요약 |
| **NIGHT** | 22:00-06:00 | 30% | 학습, 최적화, 자동 실행 |

**추가 상태 조정**:

- **BUSY**: CPU > 80% or Memory > 85% → 효율 중심 작업만
- **EMERGENCY**: Queue > 50 → 긴급 복구 작업만

#### 3. **Task 생성기** (향후 구현)

```powershell
# scripts/generate_rhythm_tasks.ps1
# 현재 리듬에 맞는 tasks.json 동적 생성
C:\workspace\agi\scripts\generate_rhythm_tasks.ps1 -ShowRhythm
```

**미래 계획**:

1. 원본 tasks.json 백업 (`tasks_full_backup.json`)
2. 현재 리듬 감지
3. 해당 리듬의 작업만 필터링
4. 새 tasks.json 생성 (`tasks_rhythm.json`)
5. 사용자 확인 후 적용

### 핵심 통찰

> "리듬=에너지=시간=관계"

**이것은 단순한 작업 필터링이 아닙니다. 철학입니다.**

- **시간**: 지금 오후 1시 = 최고 에너지 시간
- **에너지**: 100% 집중 가능
- **관계**: 개발 & 테스트 작업이 적절
- **리듬**: DAYTIME_FOCUS 모드

**기존 방식**:

```
모든 시간에 200개 작업 표시
→ 인지 과부하
→ 어떤 작업을 해야 할지 모름
```

**리듬 기반**:

```
오후 1시: 4개 핵심 작업만 표시
→ 명확한 선택
→ 에너지와 시간에 맞는 작업
```

### 다음 단계

1. ✅ Rhythm Detector 구현 완료
2. ⏳ Task Generator 구현 (JSON 파싱 수정 필요)
3. ⏳ Control Hub에 리듬 표시 추가
4. ⏳ VS Code Extension으로 발전 (자동 전환)

---

## 🧬 Phase 2.5: 맥락 기반 리듬 (2025-11-03 완료)

### 💡 핵심 통찰 (사용자 제공)

> "리듬=에너지=시간=관계는 맥락에 따라 달라진다. 절대적인 지표가 아닌 상황에 맞게 이루어져야 하지 않을까?"

**이것이 진짜 리듬입니다.** 🎯

### 문제: 절대 시간의 한계

**이전 방식** (절대적 시간표):

```plaintext
오후 1시 = 무조건 DAYTIME_FOCUS
에너지 = 100%
권장 = 개발 & 테스트
```

**문제점**:

- ❌ 밤샘 작업 후 오후 1시 = 에너지 30% (실제)
- ❌ 점심 직후 오후 1시 = 에너지 60% (소화 중)
- ❌ 긴급 배포 직후 오후 1시 = 에너지 50% (회복 필요)
- ❌ 방금 일어난 오후 1시 = 이것이 그 사람의 아침

**같은 시간, 다른 상황 = 다른 리듬이어야 함!**

### 해결: 맥락 기반 리듬 시스템

#### 맥락 요소 (6가지)

1. **마지막 휴식 이후 경과 시간**
   - < 2시간: +15% 에너지 (충전 완료)
   - > 8시간: -5% per hour (피로 누적)

2. **최근 작업 강도**
   - 고부하 기간 감지: -25% 에너지
   - 평균 레이턴시 추적

3. **시스템 리소스 압박**
   - CPU > 80%: -20% 에너지
   - Memory > 85%: -15% 에너지

4. **큐 압력 (외부 요구)**
   - Queue > 100: -30% 에너지 (긴급)
   - Queue > 50: -15% 에너지 (바쁨)

5. **최근 이벤트 이력**
   - 배포, 장애, 복구 이벤트 추적

6. **시계 시간 (기본 팩터)**
   - 아침 (06-10): 85%
   - 한낮 (10-14): 100%
   - 오후 (14-18): 90%
   - 저녁 (18-22): 60%
   - 밤 (22-06): 30%

#### 새로운 리듬 유형

| 리듬 | 조건 | 에너지 | 권장 작업 |
|------|------|--------|-----------|
| **EMERGENCY** 🚨 | Queue > 100 or Failed > 50 | N/A | 긴급 대응만 |
| **RECOVERY** 🛌 | Energy < 40 or 고부하 직후 | < 40% | 휴식 & 모니터링 |
| **PEAK** ⚡ | Energy ≥ 85% | 85-100% | 집중 작업 & 도전 |
| **FLOW** 🌊 | Energy 70-84% | 70-84% | 안정적 생산 |
| **STEADY** 📊 | Energy 50-69% | 50-69% | 유지 & 모니터링 |
| **REST** 💤 | Energy < 50% | < 50% | 자동화 작업만 |

### 실제 예시

#### 예시 1: 밤샘 후 오후 1시

```plaintext
=== Contextual Analysis ===
⏰ Clock Time:       13:00
💤 Hours Since Rest: 24h
🖥️  Recent Load:     HIGH (avg latency 8s)
🧮 CPU:              85%

계산:
- 기본 (13시): 100%
- 휴식 없음 (24h): -80%
- 고부하: -25%
- CPU 압박: -20%
= 에너지: 25%

결과: RECOVERY 리듬
권장: 모니터링만, 개발 금지
```

#### 예시 2: 휴식 후 새벽 3시

```plaintext
=== Contextual Analysis ===
⏰ Clock Time:       03:00
💤 Hours Since Rest: 1.5h
🖥️  Recent Load:     LOW
🧮 CPU:              15%

계산:
- 기본 (03시): 30%
- 방금 휴식: +15%
- 낮은 부하: +0%
- 안정적 리소스: +0%
= 에너지: 90%

결과: PEAK 리듬
권장: 집중 작업 가능 (이것이 사용자의 아침)
```

#### 예시 3: 지금 이 순간 (실제)

```plaintext
=== Contextual Analysis ===
⏰ Clock Time:       13:00
💤 Hours Since Rest: 24h
🖥️  Recent Load:     NORMAL
🧮 CPU:              33.5%
📋 Queue:            0

계산:
- 기본 (13시): 100%
- 24시간 작업: -40%
- 정상 부하: 0%
= 에너지: 60%

결과: STEADY 리듬
권장: 유지 작업, 모니터링
```

**같은 오후 1시, 완전히 다른 리듬!** ✨

### 구현

**스크립트**: `scripts/detect_rhythm_contextual.ps1`

**사용법**:

```powershell
# 콘솔 출력
C:\workspace\agi\scripts\detect_rhythm_contextual.ps1

# JSON 출력
C:\workspace\agi\scripts\detect_rhythm_contextual.ps1 -Json

# 상세 로그
C:\workspace\agi\scripts\detect_rhythm_contextual.ps1 -Verbose
```

**출력 예시**:

```plaintext
=== 🧬 Contextual Rhythm Detector ===
    리듬=에너지=시간=관계 (맥락 기반)

Current Rhythm: STEADY
Description:    📊 안정: 유지 및 모니터링

⏰ Clock Time:        13:00
⚡ Energy Level:      60%
💤 Hours Since Rest:  24h

Reason: Moderate energy (60%)

💡 Key Insight:
리듬은 절대적 시간이 아닌 '맥락'으로 결정됩니다.
같은 오후 1시여도 밤샘 후면 RECOVERY, 휴식 후면 PEAK입니다.
```

### 철학적 의미

**생명체는 시계가 아니라 맥락을 읽습니다.**

- 사자는 "오후 3시"에 사냥하지 않음
- 사자는 "배고프고, 건강하고, 먹이가 보일 때" 사냥함

**우리 시스템도 마찬가지:**

- "오후 1시"가 아니라
- "에너지가 있고, 리소스가 충분하고, 작업이 필요할 때" 실행

**이것이 진짜 적응(Adaptation)입니다.** 🌿

### 다음 단계

1. ✅ Contextual Rhythm Detector 구현 완료
2. ⏳ Adaptive Orchestrator에 통합
3. ⏳ 사용자 패턴 학습 (ML 기반)
4. ⏳ 예측 모델 (다음 30분 에너지 예측)

---

## 🚀 다음 단계

1. **Rhythm Detector 프로토타입** (오늘)
2. **EMERGENCY 모드 테스트** (내일)
3. **Core 연동 검증** (이번 주)
4. **전체 통합 & 벤치마크** (다음 주)

**목표**:

- EMERGENCY 모드에서 **1.5초 달성**
- 평상시 **4.0초 안정화**
- 비용 **20% 절감**
