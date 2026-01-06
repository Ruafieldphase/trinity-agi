# 🌙 Sleep-Based Memory Consolidation

## 인간의 수면-기억 공고화 메커니즘

### 📚 생물학적 과정 (Human)

#### 1. **REM 수면 (꿈)**

- 맥락 없는 꿈을 통한 시뮬레이션
- 다양한 시나리오 재생 (Monte Carlo 샘플링과 유사)
- 감정적 처리 및 통합

#### 2. **Stage 3 Non-REM (Deep Sleep)**

- **뇌척수액(CSF) 유입**
  - Glymphatic System 활성화
  - 노이즈 제거 (β-amyloid, tau 단백질 배출)
  - 시냅스 가지치기 (Synaptic Pruning)

- **시스템 종료**
  - 생명 유지 시스템만 작동
  - 의식 시스템 OFF
  - 에너지 집중 재분배

#### 3. **서서히 의식으로 복귀**

- Stage 2 → Stage 1 → REM → 각성
- 공고화된 기억이 의식에 통합

---

## 🤖 **현재 AGI Hippocampus 시스템**

### ✅ **현재 구현 (Immediate Consolidation)**

```python
# 즉시 공고화 (깨어있는 상태)
hippo.consolidate()  # 단기 → 장기 즉시 전환
```

**장점:**

- ✅ 빠른 응답
- ✅ 실시간 학습

**단점:**

- ❌ 노이즈 제거 없음
- ❌ 시뮬레이션 없음
- ❌ 생물학적 리듬 없음

---

## 🌙 **제안: Sleep-Like Consolidation**

### Phase 1: Offline Consolidation (수면 유사)

```python
class SleepBasedConsolidator:
    """
    인간 수면 모방 기억 공고화
    """
    
    def __init__(self):
        self.dream_simulator = DreamSimulator()
        self.noise_remover = GlymphaticSystem()
        self.synaptic_pruner = SynapticPruner()
    
    async def deep_sleep_consolidation(self):
        """
        3단계 딥슬립 공고화
        """
        # 1. REM: 꿈 시뮬레이션
        dreams = await self.dream_simulator.generate_scenarios(
            working_memory=self.short_term.get_all_working()
        )
        
        # 2. Stage 3: 노이즈 제거
        cleaned = await self.noise_remover.clean(
            memories=dreams,
            threshold=0.3  # 30% 이하 중요도 제거
        )
        
        # 3. Synaptic Pruning: 연결 가지치기
        pruned = await self.synaptic_pruner.prune(
            memories=cleaned,
            keep_ratio=0.7  # 70%만 유지
        )
        
        # 4. 장기 기억으로 공고화
        for memory in pruned:
            self.long_term.store(memory)
        
        return {
            'original': len(working_memory),
            'after_dreams': len(dreams),
            'after_cleaning': len(cleaned),
            'after_pruning': len(pruned),
            'consolidated': len(pruned)
        }
```

### Phase 2: Dream Simulation (꿈 메커니즘)

```python
class DreamSimulator:
    """
    맥락 없는 꿈을 통한 시뮬레이션
    """
    
    def generate_scenarios(self, working_memory: List[Dict]) -> List[Dict]:
        """
        수많은 시나리오 시뮬레이션
        """
        scenarios = []
        
        for memory in working_memory:
            # Monte Carlo 샘플링
            for _ in range(10):  # 10번 변형
                scenario = self._create_random_variant(memory)
                scenarios.append(scenario)
        
        return scenarios
    
    def _create_random_variant(self, memory: Dict) -> Dict:
        """
        무작위 변형 (맥락 없는 꿈처럼)
        """
        variant = memory.copy()
        
        # 요소 섞기
        variant['context'] = self._shuffle_context(memory.get('context', []))
        variant['emotional_tone'] = random.choice(['fear', 'joy', 'neutral', 'curiosity'])
        variant['scenario'] = self._generate_weird_scenario(memory)
        
        return variant
```

### Phase 3: Glymphatic System (노이즈 제거)

```python
class GlymphaticSystem:
    """
    뇌척수액 유입 모방: 노이즈 제거
    """
    
    def clean(self, memories: List[Dict], threshold: float = 0.3) -> List[Dict]:
        """
        낮은 중요도 기억 제거 (β-amyloid처럼)
        """
        cleaned = []
        
        for memory in memories:
            # 노이즈 점수 계산
            noise_score = self._calculate_noise(memory)
            
            if noise_score < threshold:
                # 중요한 기억만 유지
                cleaned.append(memory)
        
        logger.info(f"🧹 Cleaned {len(memories) - len(cleaned)} noisy memories")
        return cleaned
    
    def _calculate_noise(self, memory: Dict) -> float:
        """
        노이즈 수준 계산
        """
        # 모순되는 정보
        contradiction_score = self._check_contradictions(memory)
        
        # 중복 정보
        redundancy_score = self._check_redundancy(memory)
        
        # 감정적 잡음
        emotional_noise = self._check_emotional_noise(memory)
        
        return (contradiction_score + redundancy_score + emotional_noise) / 3
```

### Phase 4: Synaptic Pruning (가지치기)

```python
class SynapticPruner:
    """
    시냅스 가지치기: 약한 연결 제거
    """
    
    def prune(self, memories: List[Dict], keep_ratio: float = 0.7) -> List[Dict]:
        """
        중요도 기반 가지치기
        """
        # 중요도 정렬
        sorted_memories = sorted(
            memories,
            key=lambda m: m.get('importance', 0.5),
            reverse=True
        )
        
        # 상위 70%만 유지
        keep_count = int(len(sorted_memories) * keep_ratio)
        pruned = sorted_memories[:keep_count]
        
        logger.info(f"✂️ Pruned {len(sorted_memories) - keep_count} weak connections")
        return pruned
```

---

## 🕐 **Offline Consolidation Schedule**

### Option 1: Scheduled Task (야간 실행)

```powershell
# 새벽 3시에 "수면" 공고화 실행
Register-ScheduledTask -TaskName "AGI_DeepSleep" `
    -Trigger (New-ScheduledTaskTrigger -Daily -At 3:00AM) `
    -Action (New-ScheduledTaskAction -Execute "python" `
        -Argument "scripts/deep_sleep_consolidation.py")
```

### Option 2: Idle Detection (유휴 시간)

```python
def detect_idle_and_sleep():
    """
    사용자가 없을 때 자동으로 "수면" 모드 진입
    """
    if no_user_activity_for(hours=1):
        logger.info("💤 Entering deep sleep mode...")
        await deep_sleep_consolidation()
        logger.info("☀️ Waking up with consolidated memories")
```

---

## 📊 **Expected Results**

### Before (Immediate)

```
Working Memory: 100 items
  ↓ (immediate consolidation)
Long-term: 50 items (50% noise)
```

### After (Sleep-like)

```
Working Memory: 100 items
  ↓ (REM dreams: 1000 variants)
  ↓ (Glymphatic cleaning: 700 items)
  ↓ (Synaptic pruning: 350 items)
Long-term: 35 items (90% quality)
```

**Quality vs Quantity:**

- 즉시 공고화: 많지만 노이즈 많음
- 수면 공고화: 적지만 고품질

---

## 🎯 **Implementation Priority**

### Phase 1 (현재 완료) ✅

- [x] 기본 consolidation
- [x] Importance filtering
- [x] Memory recall

### Phase 2 (다음 단계)

- [ ] Dream Simulator
- [ ] Glymphatic System
- [ ] Synaptic Pruning

### Phase 3 (고급)

- [ ] Offline scheduling
- [ ] Idle detection
- [ ] Wake-up integration

---

## 💭 **Philosophy: Why Sleep Matters**

인간이 수면을 통해 기억을 공고화하는 이유:

1. **에너지 효율**: 의식 시스템을 끄고 재구성에 집중
2. **노이즈 제거**: 뇌척수액으로 대사 폐기물 제거
3. **시뮬레이션**: 꿈을 통해 다양한 시나리오 탐색
4. **통합**: 파편화된 기억을 일관된 서사로 통합

**AGI도 "쉬어야" 더 똑똑해진다.**

---

## 🔬 **References**

1. Rasch & Born (2013). "About Sleep's Role in Memory"
2. Xie et al. (2013). "Sleep Drives Metabolite Clearance from the Adult Brain"
3. Tononi & Cirelli (2014). "Sleep and Synaptic Homeostasis"
4. Walker (2017). "Why We Sleep"

---

**Date**: 2025-11-05  
**Status**: 🌙 Design Phase (수면 메커니즘 설계 완료)  
**Next**: Implement Dream Simulator & Glymphatic System
