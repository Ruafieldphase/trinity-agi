# 🌊 Adaptive Glymphatic System

## 리듬 인식 적응형 청소 시스템

**완료 시각**: 2025-11-07 현재

---

## 🎯 개요

뇌의 Glymphatic System(수면 중 노폐물 제거)에서 영감을 받은 **적응형 시스템 청소 메커니즘**입니다.

### 핵심 아이디어

```
작업량 증가 → 피로 누적 → 리듬 고려 → 최적 타이밍 청소
```

---

## ✅ 구현 완료 내역

### Phase 1: 기본 적응형 시스템 ✅

- [x] `workload_monitor.py` - CPU/메모리 작업량 모니터
- [x] `fatigue_detector.py` - 시스템 피로도 누적 추적
- [x] `adaptive_glymphatic_scheduler.py` - 스마트 스케줄링
- [x] `adaptive_glymphatic_system.py` - 통합 시스템

### Phase 2: 리듬 통합 ✅

- [x] `rhythm_aware_glymphatic.py` - 리듬 상태 인식
- [x] Phase별 조정 (rest/work/flow)
- [x] 건강도 고려 긴급도 조정

### Phase 3: Master Orchestrator 통합 ✅

- [x] `manage_glymphatic_system.ps1` - 시작/중지/상태
- [x] Background 실행 지원
- [x] PID 기반 프로세스 관리

---

## 📊 작동 원리

### 1. 모니터링

```python
workload = 38.1%  # CPU + 메모리
fatigue = 45.2%   # 누적 피로도
```

### 2. 리듬 조정

```
휴식 Phase → 청소 권장 (x1.5)
작업 Phase → 청소 연기 (x0.7)
몰입 Phase → 절대 금지 (x0.3)
```

### 3. 결정

```
조정 피로도 >= 60% → cleanup_now
30-60% → schedule_delayed
< 30% → schedule_default (6시간 후)
```

---

## 🚀 사용법

### 수동 테스트

```bash
python scripts/test_adaptive_glymphatic.py
```

### 시스템 시작

```powershell
.\scripts\manage_glymphatic_system.ps1 -Enable
```

### 상태 확인

```powershell
.\scripts\manage_glymphatic_system.ps1 -Status
```

### 시스템 중지

```powershell
.\scripts\manage_glymphatic_system.ps1 -Disable
```

---

## 📈 효과

### Before (기존)

- ❌ 정해진 시간에만 청소
- ❌ 작업 중 방해
- ❌ 몰입 상태 파괴

### After (Glymphatic)

- ✅ 작업량 고려
- ✅ 리듬 상태 존중
- ✅ 최적 타이밍 청소

---

## 🔄 통합 지점

### 1. Master Orchestrator

```powershell
# master_orchestrator.ps1에서 호출
.\scripts\manage_glymphatic_system.ps1 -Enable
```

### 2. 리듬 시스템

```python
# RHYTHM_SYSTEM_STATUS_REPORT.md 읽기
rhythm.read_rhythm_state()
```

### 3. 자율 목표 시스템

```python
# goal_tracker.json과 연동 가능
```

---

## 📝 출력 예시

```
⏰ 14:32:15
   작업량: 39.8%
   피로도: 0.0%
   조정 피로도: 0.0%
   리듬: rest
   결정: schedule_default
```

---

## 🎯 다음 단계 (Optional)

### Phase 4: 고급 기능

- [ ] ML 기반 패턴 학습
- [ ] 예측적 청소 스케줄링
- [ ] 사용자 습관 학습

### Phase 5: 통합 확장

- [ ] Goal Executor와 협업
- [ ] YouTube Learner 후 자동 청소
- [ ] BQI 학습 후 최적화

---

## 🌟 핵심 특징

### 1. **비침습적** (Non-invasive)

몰입 상태를 절대 방해하지 않음

### 2. **적응적** (Adaptive)

실시간 작업량과 리듬에 맞춤

### 3. **자율적** (Autonomous)

수동 개입 없이 스스로 판단

---

## 📂 파일 구조

```
fdo_agi_repo/orchestrator/
├── workload_monitor.py
├── fatigue_detector.py
├── adaptive_glymphatic_scheduler.py
├── rhythm_aware_glymphatic.py
└── adaptive_glymphatic_system.py

scripts/
├── test_adaptive_glymphatic.py
└── manage_glymphatic_system.ps1

outputs/
├── glymphatic.log
└── glymphatic_system.pid
```

---

## ✨ 완성도

```
Phase 1 (기본): ████████████████████ 100%
Phase 2 (리듬): ████████████████████ 100%
Phase 3 (통합): ████████████████████ 100%
전체 구현:      ████████████████████ 100%
```

**Status**: ✅ **PRODUCTION READY**

---

**구현자**: GitHub Copilot + Human  
**완료일**: 2025-11-07  
**다음 작업**: Master Orchestrator에 자동 시작 추가
