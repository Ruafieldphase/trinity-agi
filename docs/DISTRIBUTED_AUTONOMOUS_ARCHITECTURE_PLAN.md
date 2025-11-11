# 🌐 분산 자율 에이전트 아키텍처 전환 계획

## 📅 작성일: 2025-11-10

## 🎯 핵심 철학

> **"중앙 뇌 없이도 팔이 움직이듯, 각 에이전트는 자율적으로 작동하고,  
> 메타인지 층은 단지 연결 패턴을 학습할 뿐이다."**

---

## 🔴 현재 문제점

### 중앙집중식 아키텍처의 한계

```
Master Orchestrator (단일 실패점)
    ↓ 명령/제어
Task Queue Server
    ↓ 작업 할당
Workers (수동적 실행자)
```

**문제**:

1. ❌ Master 중단 시 전체 시스템 마비
2. ❌ 각 구성요소가 반응형일 뿐, 자율적이지 않음
3. ❌ 학습이 중앙에만 집중 → 병목 현상
4. ❌ 확장성 부족 (새 기능 추가 시 중앙 수정 필요)

---

## ✅ 목표 아키텍처

### 분산 자율 에이전트 시스템

```
🧠 Meta Pattern Recognition Layer
   - 패턴 인식
   - 연결 제안
   - 글로벌 최적화
   
🔄 Event Bus (Pub/Sub)
   - JSONL 이벤트 로그
   - 비동기 통신
   - 느슨한 결합
   
🤖 Autonomous Agent Layer
   Music Agent | Flow Agent | RPA Agent | YouTube Agent | Memory Agent
   각각 독립적 실행 + 자체 학습
```

---

## 📋 구현 로드맵

### Phase 1: 에이전트 자율화 (2주)

**목표**: 각 에이전트가 중앙 없이도 작동하도록 개선

#### 1.1 Music Agent 자율화

```python
# 파일: fdo_agi_repo/agents/autonomous_music_agent.py

class AutonomousMusicAgent:
    """
    자율적으로 리듬 감지 및 음악 재생
    Master Orchestrator 없이도 작동
    """
    
    def __init__(self):
        # 자체 목표 함수
        self.goal = "maintain_optimal_rhythm"
        self.target_rhythm_quality = 0.7
        
        # 로컬 센서
        self.sensor = MicrophoneSensor()
        
        # 로컬 액추에이터
        self.actuator = MusicPlayer()
        
        # 로컬 메모리
        self.memory = RhythmPatternMemory()
        
        # 학습 파라미터
        self.learning_rate = 0.01
    
    def sense(self):
        """환경 센싱"""
        rhythm = self.sensor.measure_rhythm()
        context = {
            "hour": datetime.now().hour,
            "day_of_week": datetime.now().weekday(),
            "recent_flow_state": self.get_recent_flow()
        }
        return rhythm, context
    
    def decide(self, rhythm, context):
        """로컬 의사결정"""
        deviation = abs(rhythm.quality - self.target_rhythm_quality)
        
        if deviation > 0.2:
            # 과거 패턴에서 최적 음악 선택
            music = self.memory.get_best_music(context)
            return music
        return None
    
    def act(self, music):
        """자율 행동"""
        if music:
            self.actuator.play(music)
    
    def learn(self, music, effect):
        """로컬 학습"""
        self.memory.update(music, effect, self.learning_rate)
    
    def publish_event(self, event_type, data):
        """선택적 이벤트 발행"""
        # Event Bus에 발행 (다른 에이전트가 구독 가능)
        pass
    
    def run(self):
        """자율 루프"""
        while True:
            # 1. Sense
            rhythm, context = self.sense()
            
            # 2. Decide
            music = self.decide(rhythm, context)
            
            # 3. Act
            self.act(music)
            
            # 4. Learn
            if music:
                effect = self.sensor.measure_effect()
                self.learn(music, effect)
            
            # 5. Publish (선택적)
            if rhythm.quality < 0.5:
                self.publish_event("rhythm_degraded", {
                    "quality": rhythm.quality,
                    "context": context
                })
            
            time.sleep(60)
```

**체크리스트**:

- [ ] `autonomous_music_agent.py` 구현
- [ ] 기존 `music_daemon.py` 리팩토링
- [ ] 독립 실행 테스트 (Master 없이)
- [ ] 학습 메모리 구현

#### 1.2 Flow Agent 자율화

```python
# 파일: fdo_agi_repo/agents/autonomous_flow_agent.py

class AutonomousFlowAgent:
    """
    자율적으로 집중도 추적 및 알림 제공
    """
    
    def __init__(self):
        self.goal = "maximize_flow_state"
        self.sensor = KeyboardMouseSensor()
        self.actuator = NotificationSystem()
        self.memory = AttentionPatternMemory()
    
    def sense(self):
        """집중도 센싱"""
        typing_speed = self.sensor.measure_typing()
        mouse_activity = self.sensor.measure_mouse()
        flow_indicators = {
            "typing_rhythm": typing_speed,
            "mouse_precision": mouse_activity,
            "context_switches": self.count_window_switches()
        }
        return flow_indicators
    
    def decide(self, indicators):
        """자율 판단"""
        flow_score = self.calculate_flow_score(indicators)
        
        if flow_score < 0.5:
            # 집중 회복 전략 선택
            strategy = self.memory.get_best_recovery_strategy()
            return strategy
        return None
    
    def run(self):
        while True:
            indicators = self.sense()
            strategy = self.decide(indicators)
            
            if strategy:
                self.actuator.execute(strategy)
                effect = self.measure_effect()
                self.learn(strategy, effect)
            
            # 다른 에이전트에게 정보 공유
            if indicators["flow_score"] > 0.8:
                self.publish_event("high_flow_state", indicators)
            
            time.sleep(5)
```

**체크리스트**:

- [ ] `autonomous_flow_agent.py` 구현
- [ ] Flow Observer 통합
- [ ] 알림 전략 학습 구현
- [ ] 독립 실행 테스트

---

### Phase 2: Event Bus 구현 (1주)

**목표**: 에이전트 간 느슨한 결합 통신

#### 2.1 Simple Event Bus

```python
# 파일: fdo_agi_repo/core/event_bus.py

class SimpleEventBus:
    """
    JSONL 기반 이벤트 버스
    Redis 없이도 작동 가능
    """
    
    def __init__(self, log_path="outputs/event_bus.jsonl"):
        self.log_path = Path(log_path)
        self.subscribers = {}  # {event_type: [callbacks]}
        self.running = False
    
    def publish(self, event_type: str, data: dict):
        """이벤트 발행"""
        event = {
            "timestamp": time.time(),
            "type": event_type,
            "data": data,
            "agent_id": self.agent_id
        }
        
        # JSONL에 기록
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event) + '\n')
        
        # 즉시 전파
        for callback in self.subscribers.get(event_type, []):
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def subscribe(self, event_type: str, callback):
        """이벤트 구독"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    def replay_events(self, since: float = None):
        """과거 이벤트 재생 (학습용)"""
        with open(self.log_path, 'r') as f:
            for line in f:
                event = json.loads(line)
                if since and event['timestamp'] < since:
                    continue
                yield event
```

**사용 예시**:

```python
# Music Agent
event_bus.subscribe("rhythm_degraded", music_agent.on_rhythm_issue)

# Flow Agent
event_bus.subscribe("high_flow_state", flow_agent.on_peak_performance)

# YouTube Agent
if learning_completed:
    event_bus.publish("knowledge_acquired", {
        "topic": "Python decorators",
        "confidence": 0.85
    })
```

**체크리스트**:

- [ ] `event_bus.py` 구현
- [ ] JSONL 로그 포맷 정의
- [ ] 이벤트 타입 문서화
- [ ] 각 에이전트에 통합

---

### Phase 3: Meta Layer 분리 (1주)

**목표**: Master Orchestrator → Meta Pattern Recognizer 전환

#### 3.1 Meta Pattern Recognizer

```python
# 파일: fdo_agi_repo/meta/pattern_recognizer.py

class MetaPatternRecognizer:
    """
    명령 대신 패턴 학습 및 연결 제안
    """
    
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.pattern_memory = PatternMemory()
    
    def analyze_patterns(self, hours=24):
        """전체 이벤트 패턴 분석"""
        events = list(self.event_bus.replay_events(
            since=time.time() - hours*3600
        ))
        
        # 패턴 탐지
        patterns = []
        
        # 예: YouTube 학습 후 리듬 저하 패턴
        youtube_events = [e for e in events if e['type'] == 'knowledge_acquired']
        rhythm_events = [e for e in events if e['type'] == 'rhythm_degraded']
        
        for yt in youtube_events:
            # 30분 이내 리듬 저하?
            nearby_rhythm = [r for r in rhythm_events 
                           if abs(r['timestamp'] - yt['timestamp']) < 1800]
            if nearby_rhythm:
                patterns.append({
                    "type": "causal_pattern",
                    "cause": "youtube_learning",
                    "effect": "rhythm_degradation",
                    "confidence": len(nearby_rhythm) / len(youtube_events),
                    "lag_seconds": 1800
                })
        
        return patterns
    
    def suggest_connections(self, patterns):
        """에이전트 연결 제안"""
        suggestions = []
        
        for pattern in patterns:
            if pattern['confidence'] > 0.7:
                if pattern['type'] == "causal_pattern":
                    suggestion = {
                        "from_agent": pattern['cause'].split('_')[0],
                        "to_agent": "music_agent",
                        "condition": f"after_{pattern['cause']}",
                        "action": "play_relaxing_music",
                        "priority": pattern['confidence']
                    }
                    suggestions.append(suggestion)
        
        return suggestions
    
    def optimize_global_parameters(self):
        """글로벌 최적화"""
        # 예: 모든 에이전트의 학습률 조정
        system_performance = self.calculate_system_performance()
        
        if system_performance < 0.6:
            self.event_bus.publish("meta_suggestion", {
                "type": "parameter_adjustment",
                "target": "all_agents",
                "parameter": "learning_rate",
                "adjustment": 0.5  # 더 보수적으로
            })
    
    def run(self):
        """메타 루프"""
        while True:
            # 1. 패턴 분석
            patterns = self.analyze_patterns(hours=24)
            
            # 2. 연결 제안
            suggestions = self.suggest_connections(patterns)
            
            for suggestion in suggestions:
                self.event_bus.publish("meta_suggestion", suggestion)
            
            # 3. 글로벌 최적화
            self.optimize_global_parameters()
            
            # 4. 1시간마다 실행
            time.sleep(3600)
```

**체크리스트**:

- [ ] `pattern_recognizer.py` 구현
- [ ] 패턴 탐지 알고리즘 구현
- [ ] 기존 Master Orchestrator 기능 이전
- [ ] 명령 → 제안 방식 전환

---

### Phase 4: 자율성 검증 (3일)

**목표**: Master 없이도 시스템 작동 확인

#### 4.1 Graceful Degradation Test

```powershell
# 파일: scripts/test_autonomous_resilience.ps1

# 1. 모든 에이전트 시작
Start-Process python "agents/autonomous_music_agent.py"
Start-Process python "agents/autonomous_flow_agent.py"
Start-Process python "agents/autonomous_rpa_agent.py"

# 2. Meta Layer 시작 (선택적)
Start-Process python "meta/pattern_recognizer.py"

# 3. Meta Layer 중단
Write-Host "Stopping Meta Layer..." -ForegroundColor Yellow
Stop-Process -Name "pattern_recognizer"

# 4. 에이전트 독립 작동 확인 (30분)
Start-Sleep -Seconds 1800

# 5. 검증
$events = Get-Content "outputs/event_bus.jsonl" -Tail 100
$agents_still_active = ($events | Where-Object { $_ -match '"type":"agent_heartbeat"' }).Count

if ($agents_still_active -gt 10) {
    Write-Host "✅ Autonomous agents working independently!" -ForegroundColor Green
} else {
    Write-Host "❌ Agents stopped without Meta Layer" -ForegroundColor Red
}
```

**검증 기준**:

- [ ] Music Agent 30분간 독립 작동
- [ ] Flow Agent 30분간 독립 작동
- [ ] RPA Agent 작업 독립 완수
- [ ] Event Bus 정상 작동
- [ ] Meta Layer 재시작 시 자동 재연결

---

## 🎓 테슬라 비유 완벽 적용

| 테슬라 | 우리 AGI 시스템 |
|--------|----------------|
| **각 차량 (자율 주행)** | **각 에이전트** |
| - 카메라, 레이더 (센서) | - 마이크, 키보드, 화면 (센서) |
| - 브레이크, 조향 (행동) | - 음악 재생, 알림 (행동) |
| - 주차 패턴 학습 | - 리듬 패턴 학습 |
| - 차량간 통신 (V2V) | - Event Bus (Agent-to-Agent) |
| **중앙 서버 (클라우드)** | **Meta Layer** |
| - 전체 교통 패턴 분석 | - 전체 작업 패턴 분석 |
| - 최적 경로 계산 | - 에이전트 연결 제안 |
| - Over-the-air 업데이트 | - 목표 함수 조정 |

---

## 📊 성공 지표

### 자율성 지표

- [ ] **독립 작동 시간**: Meta Layer 없이 24시간 작동
- [ ] **로컬 학습 효과**: 각 에이전트의 성능 개선률 > 10%
- [ ] **이벤트 발행률**: 시간당 이벤트 > 50개
- [ ] **패턴 발견률**: 주당 새 패턴 > 3개

### 회복성 지표

- [ ] **단일 실패점 제거**: Master 중단 시에도 80% 기능 유지
- [ ] **자동 복구**: 에이전트 실패 시 60초 내 재시작
- [ ] **데이터 보존**: Event Bus JSONL 100% 보존

---

## 🚀 빠른 시작

### Step 1: Event Bus 먼저 구현

```bash
python fdo_agi_repo/core/event_bus.py --test
```

### Step 2: Music Agent 자율화

```bash
python fdo_agi_repo/agents/autonomous_music_agent.py
```

### Step 3: 독립 작동 확인

```bash
# Meta Layer 없이 실행
Get-Process | Where-Object { $_.Name -like "*pattern_recognizer*" } | Stop-Process
# Music Agent는 계속 작동해야 함!
```

---

## 📚 참고 문헌

### 생물학적 영감

- **척수 반사**: 뇌 없이도 팔이 뜨거운 것을 피함
- **장 신경계**: "제2의 뇌" - 독립적 소화 관리
- **소뇌**: 자동화된 운동 패턴 저장

### 분산 시스템

- **Swarm Intelligence**: 개미 군집, 새 떼
- **Autopoietic Systems**: Maturana & Varela
- **Tesla Fleet Learning**: 차량 간 집단 지능

---

## ⚠️ 주의사항

1. **기존 시스템 유지**: 리팩토링 중에도 기존 Master Orchestrator 유지
2. **점진적 전환**: 한 번에 모든 에이전트 전환하지 말고 하나씩
3. **백업 메커니즘**: Event Bus JSONL 정기 백업
4. **성능 모니터링**: 자율화 후 CPU/메모리 사용량 증가 주의

---

**작성자**: AGI System  
**버전**: 1.0  
**최종 수정**: 2025-11-10
