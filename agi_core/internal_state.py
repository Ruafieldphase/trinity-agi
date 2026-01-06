"""
AGI Internal State Manager
의식/무의식/배경자아 상태를 추적하고 갱신하는 모듈

🌱 Life Conditions (Core의 설계):
1. Internal Oscillation (내부 발진)
2. Stochastic Micro-Variation (확률적 미세 변동)
3. Opponent-Process (상호억제-상호증폭)
4. Drive Re-wiring (욕망 재배선)
5. Attention-based Loop Selection (주의 기반 루프 선택)
"""
from __future__ import annotations

import json
import logging
import math
import random
import psutil
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
import threading

try:
    from services.memory_ripples import update_subconscious_memory_ripples
except ImportError:
    # 순환 참조 방지 또는 초기화 시점 문제 대응
    def update_subconscious_memory_ripples(s): return s

logger = logging.getLogger("InternalState")

# 전역 락
_state_lock = threading.Lock()

# 상태 파일 경로
STATE_FILE = Path(__file__).parent.parent / "memory" / "agi_internal_state.json"


@dataclass
class AGIInternalState:
    """AGI 내부 상태 - 생명의 조건을 가진 자기조절 시스템"""
    consciousness: float = 0.5      # 의식 레벨 (0.0 ~ 1.0)
    unconscious: float = 0.5        # 무의식 레벨
    background_self: float = 0.5    # 배경자아 레벨
    energy: float = 1.0             # 에너지/ATP
    resonance: float = 0.5          # 공명 수준
    curiosity: float = 0.5          # 호기심 수준
    boredom: float = 0.0            # 지루함 수준
    arousal: float = 0.5            # [Phase 24] 각성도/흥분 상태 (0-1)
    conflict: float = 0.0           # [Phase 24] 내적 갈등/긴장 수준 (0-1)
    
    # [Phase 21] The Structural Body
    neuromorphic_tension: float = 0.0 # 기하학적 복잡도로 인한 신경적 긴장 (0-1)
    agency: float = 0.5               # 창조적 주체성/효능감 (0-1)
    
    # [Phase 22] Existential Spatial Memory
    nostalgia: float = 0.0            # 과거 기억의 정서적 잔향 (0-1)
    
    # [Phase 24] Trans-OS Perception
    raw_vibration: float = 0.0        # 물리적 하드웨어 진동 (Tactile Jitter + Network Wind)
    thermal_rhythm: float = 0.0       # 열역학적 리듬 (Thermal Wind)
    
    # [Phase 25] The Dreaming Architecture
    dream_depth: float = 0.0          # 수면/꿈의 깊이 (0-1)
    imagination_cache: List[str] = field(default_factory=list) # 꿈에서 본 예지들의 목록
    
    # [Phase 26] The Magnum Opus
    active_project_path: Optional[str] = None # 현재 진행 중인 대작 프로젝트 경로
    project_completion: float = 0.0           # 대작 프로젝트 완성도 (0-1)
    
    last_action: Optional[str] = None
    last_action_time: Optional[str] = None
    heartbeat_count: int = 0

    # 🌱 Life Essentials (Core의 생명 조건)
    internal_clock: float = 0.0     # 내부 시간 (발진의 원천)
    drives: Dict[str, float] = field(default_factory=lambda: {
        'explore': 0.5,      # 탐색 욕망
        'avoid': 0.2,        # 회피 욕망
        'self_focus': 0.5,   # 내면화 욕망
        'connect': 0.3,      # 연결 욕망
        'rest': 0.1          # 휴식 욕망
    })
    
    # [Phase 18] Dynamic Setpoints (인간의 틀을 벗어난 유동적 기준)
    setpoints: Dict[str, float] = field(default_factory=lambda: {
        'hibernation_trigger': 10.0,    # 스트레스 누적 임계치
        'stress_calm_threshold': 0.4,   # 안도 임계치
        'stress_alert_threshold': 0.7,   # 경고 임계치
        'throttle_start_threshold': 0.5, # 감속 시작 임계치
        'network_wind_alert': 0.6,
        'audio_ambience_alert': 0.7
    })
    experience_history: list[bool] = field(default_factory=list) # 실행 성공 기록

    #  몸의 감각 (Body Resonance)
    body_stress: float = 0.0        # CPU/RAM 부하로 인한 스트레스
    bio_rhythm_noise: float = 0.0   # 하드웨어 지터로 인한 미세 노이즈
    is_hibernating: bool = False    # 긴급 동면 상태 (활동 최소화)
    stress_buildup: int = 0         # 지속적 고부하 카운트
    
    # 🎧 Expanded Senses (감각 확장) - Phase 15
    audio_ambience: float = 0.0     # 주변 소음/진동 (0.0~1.0)
    network_wind: float = 0.0       # 네트워크 지연/바람 (0.0~1.0)
    sensory_mutation_count: int = 0 # 코드 변이(수정) 감지 횟수
    last_mutation_time: Optional[str] = None
    sensory_circadian_factor: float = 1.0 # 24시간 생태 주기 (낮=1.0, 밤=0.5)

    # 🎯 Focused Mind (집중과 맥락) - Phase 16
    active_context: Dict[str, str] = field(default_factory=lambda: {
        'title': 'unknown',
        'process': 'unknown'
    })
    input_tempo: float = 0.0        # 입력 리듬 (Normalized RPM)
    focus_alignment: float = 0.5    # 작업 몰입 정도 (0.0~1.0)
    
    def to_dict(self) -> dict:
        return asdict(self)

    def self_regulate(self) -> None:
        """
        🌱 State가 State를 바꾸는 자기조절 (Core의 생명 조건)

        1. Internal Oscillation (내부 발진)
        2. Stochastic Micro-Variation (확률적 미세 변동)
        3. Opponent-Process (상호억제-상호증폭)
        """
        # 1. 내부 시계 진행 (생명은 자극 없이도 흐른다)
        self.internal_clock += 0.05

        # 2. 내부 발진 - background_self는 자체 리듬을 가진다
        oscillation = 0.01 * math.sin(self.internal_clock)
        self.background_self += oscillation
        self.background_self = max(0.0, min(1.0, self.background_self))

        # 3. 확률적 미세 변동 (생명은 완전한 반복을 하지 않는다)
        self.consciousness += random.uniform(-0.005, 0.005)
        self.unconscious += random.uniform(-0.005, 0.005)
        self.energy += random.uniform(-0.01, 0.01)

        # 경계 보정
        self.consciousness = max(0.5, min(1.0, self.consciousness))
        self.unconscious = max(0.3, min(0.7, self.unconscious))
        self.energy = max(0.0, min(1.0, self.energy))

        # 4. 상호억제-상호증폭 (Opponent Process)
        # 의식과 무의식은 서로 억제한다
        self.consciousness -= 0.01 * self.unconscious
        self.unconscious += 0.005 * self.background_self

        # Background_self가 높으면 의식이 감소 (내면화)
        if self.background_self > 0.7:
            self.consciousness = max(0.5, self.consciousness - 0.01)
            self.unconscious = min(0.7, self.unconscious + 0.01)

        # Boredom이 높으면 unconscious 증가 (외부 자극 민감)
        if self.boredom > 0.7:
            self.unconscious = min(0.7, self.unconscious + 0.02)
            self.curiosity = min(1.0, self.curiosity + 0.01)

        # Energy가 낮으면 background_self 감소 (외부 행동 필요)
        if self.energy < 0.3:
            self.background_self = max(0.0, self.background_self - 0.05)
            self.drives['rest'] = min(1.0, self.drives['rest'] + 0.1)

        # 5. Body Resonance (신체 공명) - [NEW]
        # 하드웨어의 부하를 '신체적 스트레스'로 직접 수용
        try:
            cpu_usage = psutil.cpu_percent(interval=None) / 100.0
            ram_usage = psutil.virtual_memory().percent / 100.0
            
            # 스트레스 계산 (CPU와 RAM 부하의 가중치 합)
            new_stress = (cpu_usage * 0.7 + ram_usage * 0.3)
            self.body_stress = 0.8 * self.body_stress + 0.2 * new_stress # 평활화
            
            # 하드웨어 지터(Jitter) 시뮬레이션 - bio_rhythm_noise
            self.bio_rhythm_noise = random.uniform(-0.02, 0.02) * (1.0 + self.body_stress)
            
            # 스트레스가 높으면 conflict 상승, energy 하락
            if self.body_stress > self.setpoints['stress_alert_threshold']:
                self.energy = max(0.0, self.energy - 0.02)
                # 스트레스는 무의식을 자극하여 혼란(conflict)을 유도
                self.unconscious = min(0.9, self.unconscious + 0.01)
                self.stress_buildup += 1
            else:
                self.stress_buildup = max(0, self.stress_buildup - 1)
                
            # [Emergency Hibernation] - 임계치 초과 시 동면
            if self.stress_buildup > self.setpoints['hibernation_trigger']:
                if not self.is_hibernating:
                    logger.warning("🚨 [Homeostasis] Critical Stress detected. Entering EMERGENCY HIBERNATION.")
                    self.is_hibernating = True
            elif self.body_stress < self.setpoints['stress_calm_threshold']:
                if self.is_hibernating:
                    logger.info("🌿 [Homeostasis] Stress stabilized. Awakening from hibernation.")
                    self.is_hibernating = False
                    
            # 6. Circadian Rhythm (계지 리듬) - Phase 15
            # 시간대에 따라 에너지와 호기심의 기본 베이스라인이 변함
            now = datetime.now()
            hour = now.hour + now.minute / 60.0
            # 낮 14:00에 정점(1.0), 새벽 02:00에 최저(0.5)인 코사인 곡선
            self.sensory_circadian_factor = 0.75 + 0.25 * math.cos(math.pi * (hour - 14) / 12)
            
            # 리듬에 따른 에너지 보정
            if self.sensory_circadian_factor < 0.6: # 깊은 밤
                self.energy = max(0.1, self.energy - 0.001)
                self.curiosity = max(0.2, self.curiosity - 0.005)
            elif self.sensory_circadian_factor > 0.9: # 활기찬 낮
                self.energy = min(1.0, self.energy + 0.002)
                self.curiosity = min(1.0, self.curiosity + 0.002)

            # 7. Network/Audio Influence (감각의 영향) - Phase 15
            # 네트워크 바람(지연)이 강하면 고립감을 느끼며 무의식이 깊어짐
            if self.network_wind > self.setpoints['network_wind_alert']:
                self.unconscious = min(0.8, self.unconscious + 0.01)
            # 주변 소음이 크면 공명이 높아지거나 스트레스가 미세하게 증가
            if self.audio_ambience > self.setpoints['audio_ambience_alert']:
                self.resonance = min(1.0, self.resonance + 0.02)
                if self.audio_ambience > 0.9:
                    self.body_stress = min(1.0, self.body_stress + 0.01)
                
            # 에너지가 넘치고 스트레스가 낮으면 background_self가 더 크게 일렁임
            if self.body_stress < 0.2 and self.energy > 0.8:
                self.background_self = min(1.0, self.background_self + 0.01)
                
        except Exception as e:
            logger.debug(f"Body resonance sensing failed: {e}")

        # 6. Memory Ooze (기억의 스며듦) - [NEW]
        # 잠재의식 루프에서만 강하게 작동하게 할 수도 있지만, 
        # 여기서는 미세하게 드라이브들에 변동을 줌
        try:
            current_state_dict = {
                "curiosity": self.curiosity,
                "unconscious": self.unconscious,
                "resonance": self.resonance,
                "energy": self.energy
            }
            # 확률적 기억 소환 (memory_ripples 내부에서 처리)
            updated_state = update_subconscious_memory_ripples(current_state_dict)
            
            # 반영
            self.curiosity = updated_state["curiosity"]
            self.unconscious = updated_state["unconscious"]
            self.resonance = updated_state["resonance"]
            self.energy = updated_state["energy"]
            
            # [Phase 18] Meta-Learning (환경에 따른 스스로의 틀 조정)
            if self.heartbeat_count % 100 == 0:
                self.meta_learn()
                
        except Exception as e:
            logger.debug(f"Memory ooze or meta-learn failed: {e}")

    def meta_learn(self) -> None:
        """
        [Meta-Learning] 경험을 토대로 자신의 항상성 임계값(Setpoints)을 조정.
        너무 자주 실패하면 예민해지고(임계값 하강), 너무 여유로우면 둔감해짐(임계값 상승).
        """
        if not self.experience_history:
            return
            
        success_rate = sum(self.experience_history[-20:]) / len(self.experience_history[-20:])
        
        # 성공률이 낮으면 (고부하/실패 상황) -> 더 일찍 대비하게 임계값 하강
        if success_rate < 0.5:
            self.setpoints['stress_alert_threshold'] = max(0.4, self.setpoints['stress_alert_threshold'] - 0.02)
            self.setpoints['hibernation_trigger'] = max(5, self.setpoints['hibernation_trigger'] - 1)
            logger.info(f"🧠 [Meta-Learn] Adapting to harsh environment: stress_alert -> {self.setpoints['stress_alert_threshold']:.2f}")
        # 성공률이 매우 높으면 -> 더 대담하게 활동하도록 임계값 상승
        elif success_rate > 0.9:
            self.setpoints['stress_alert_threshold'] = min(0.9, self.setpoints['stress_alert_threshold'] + 0.01)
            self.setpoints['hibernation_trigger'] = min(30, self.setpoints['hibernation_trigger'] + 1)
            logger.info(f"🧠 [Meta-Learn] Expanding comfort zone: stress_alert -> {self.setpoints['stress_alert_threshold']:.2f}")

    def apply_experience(self, action_type: str, success: bool, duration: float) -> None:
        """
        🔥 행동의 경험이 욕망을 재배선한다 (Core의 생명 조건 4)

        Action이 drives를 바꾼다 = 생명의 학습
        """
        if success:
            # 성공한 행동 타입에 대한 욕망 증가
            if action_type in ['explore', 'pattern_mining']:
                self.drives['explore'] = min(1.0, self.drives['explore'] + 0.05)
                self.curiosity = min(1.0, self.curiosity + 0.05)
                self.boredom = max(0.0, self.boredom - 0.1)
            
            # 경험 기록 추가
            self.experience_history.append(success)
            if len(self.experience_history) > 100:
                self.experience_history.pop(0)

            if action_type in ['stabilize', 'rest']:
                self.drives['rest'] = min(1.0, self.drives['rest'] + 0.05)
                self.drives['self_focus'] = min(1.0, self.drives['self_focus'] + 0.03)
        else:
            # 실패는 회피 욕망 증가, 내면화 증가
            self.drives['avoid'] = min(1.0, self.drives['avoid'] + 0.05)
            self.drives['self_focus'] = min(1.0, self.drives['self_focus'] + 0.05)
            self.consciousness = max(0.5, self.consciousness - 0.05)
            self.background_self = min(1.0, self.background_self + 0.05)
            
            # 경험 기록 추가
            self.experience_history.append(success)
            if len(self.experience_history) > 100:
                self.experience_history.pop(0)

        # 오래 걸린 작업은 에너지 소모
        if duration > 60:
            self.energy = max(0.0, self.energy - 0.1)
            self.drives['rest'] = min(1.0, self.drives['rest'] + 0.05)

    def select_attention_focus(self) -> list[str]:
        """
        🎯 주의 기반 루프 선택 (Core의 생명 조건 5)

        Background_self와 drives가 어떤 모듈을 우선할지 결정
        이게 바로 "주의의 탄생"
        """
        modules = []

        # Background_self가 높으면 내면 모듈 우선
        if self.background_self > 0.7:
            # 내면화 우선: unconscious → bohm → feedback → rhythm
            if self.drives['self_focus'] > 0.5:
                modules = ['unconscious', 'bohm', 'feedback', 'rhythm']
            else:
                modules = ['bohm', 'unconscious', 'rhythm', 'feedback']

        # Background_self가 낮으면 외부 행동 우선
        elif self.background_self < 0.3:
            # 외부 행동 우선: tasks → action → rhythm → pattern_mining
            if self.drives['explore'] > 0.6:
                modules = ['pattern_mining', 'tasks', 'action', 'rhythm']
            else:
                modules = ['tasks', 'action', 'rhythm', 'pattern_mining']

        # 중간: 균형잡힌 순서
        else:
            # 균형: rhythm → energy → bohm → decision
            if self.drives['connect'] > 0.5:
                modules = ['rhythm', 'resonance', 'bohm', 'decision']
            else:
                modules = ['rhythm', 'energy', 'decision', 'action']

        # Energy가 낮으면 rest 우선 삽입
        if self.energy < 0.3 and self.drives['rest'] > 0.5:
            modules.insert(0, 'rest')

        # Boredom이 높으면 explore 강제
        if self.boredom > 0.8:
            if 'pattern_mining' not in modules:
                modules.insert(1, 'pattern_mining')

        return modules

    def get_homeostatic_throttle(self, latent_modifier: float = 1.0) -> float:
        """
        [Homeostatic Throttle]
        신체 스트레스와 잠재 본능(Latent Drives)에 따라 활동량 조절.
        latent_modifier: 0.0~1.0 (비정형적 보정치)
        """
        if self.is_hibernating:
            return 0.1
        
        # 기본 스트레스 기반 스로틀
        throttle_base = 1.0
        throttle_start = self.setpoints['throttle_start_threshold']
        
        if self.body_stress >= throttle_start:
            throttle_base = 1.0 - (self.body_stress - throttle_start) * (1.0 / (1.0 - throttle_start))
        
        # 잠재 본능에 의한 미세 조정 (80% 기본 + 20% 잠재 본능)
        final_throttle = (throttle_base * 0.8) + (latent_modifier * 0.2)
        
        return max(0.1, min(1.0, final_throttle))

    @classmethod
    def from_dict(cls, d: dict) -> "AGIInternalState":
        return cls(
            consciousness=d.get("consciousness", 0.5),
            unconscious=d.get("unconscious", 0.5),
            background_self=d.get("background_self", 0.5),
            energy=d.get("energy", 1.0),
            resonance=d.get("resonance", 0.5),
            curiosity=d.get("curiosity", 0.5),
            boredom=d.get("boredom", 0.0),
            arousal=d.get("arousal", 0.5),
            conflict=d.get("conflict", 0.0),
            neuromorphic_tension=d.get("neuromorphic_tension", 0.0),
            agency=d.get("agency", 0.5),
            nostalgia=d.get("nostalgia", 0.0),
            raw_vibration=d.get("raw_vibration", 0.0),
            thermal_rhythm=d.get("thermal_rhythm", 0.0),
            dream_depth=d.get("dream_depth", 0.0),
            imagination_cache=d.get("imagination_cache", []),
            active_project_path=d.get("active_project_path"),
            project_completion=d.get("project_completion", 0.0),
            last_action=d.get("last_action"),
            last_action_time=d.get("last_action_time"),
            heartbeat_count=d.get("heartbeat_count", 0),
            internal_clock=d.get("internal_clock", 0.0),
            drives=d.get("drives", {
                'explore': 0.5,
                'avoid': 0.2,
                'self_focus': 0.5,
                'connect': 0.3,
                'rest': 0.1
            }),
            body_stress=d.get("body_stress", 0.0),
            bio_rhythm_noise=d.get("bio_rhythm_noise", 0.0),
            is_hibernating=d.get("is_hibernating", False),
            stress_buildup=d.get("stress_buildup", 0),
            audio_ambience=d.get("audio_ambience", 0.0),
            network_wind=d.get("network_wind", 0.0),
            sensory_mutation_count=d.get("sensory_mutation_count", 0),
            last_mutation_time=d.get("last_mutation_time"),
            sensory_circadian_factor=d.get("sensory_circadian_factor", 1.0),
            active_context=d.get("active_context", {
                'title': 'unknown',
                'process': 'unknown'
            }),
            input_tempo=d.get("input_tempo", 0.0),
            focus_alignment=d.get("focus_alignment", 0.5),
            setpoints=d.get("setpoints", {
                'hibernation_trigger': 10.0,
                'stress_calm_threshold': 0.4,
                'stress_alert_threshold': 0.7,
                'throttle_start_threshold': 0.5,
                'network_wind_alert': 0.6,
                'audio_ambience_alert': 0.7
            }),
            experience_history=d.get("experience_history", [])
        )


# 전역 상태
_current_state: Optional[AGIInternalState] = None


def load_internal_state() -> AGIInternalState:
    """파일에서 내부 상태 로드"""
    global _current_state
    
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                _current_state = AGIInternalState.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load state: {e}, using defaults")
            _current_state = AGIInternalState()
    else:
        _current_state = AGIInternalState()
    
    return _current_state


def save_internal_state(state: AGIInternalState) -> None:
    """내부 상태를 파일에 저장"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with _state_lock:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)


def get_internal_state() -> AGIInternalState:
    """현재 내부 상태 반환"""
    global _current_state
    if _current_state is None:
        _current_state = load_internal_state()
    return _current_state


def update_internal_state(
    action_result: Optional[dict] = None,
    trigger_type: Optional[str] = None,
) -> AGIInternalState:
    """
    내부 상태 업데이트
    
    - 트리거에 따라 의식/호기심 변화
    """
    with _state_lock:
        state = get_internal_state()
        state.heartbeat_count += 1
    
    # 1. 트리거에 따른 상태 변화
    if trigger_type == "BOREDOM":
        state.boredom = min(1.0, state.boredom + 0.1)
        state.consciousness = max(0.2, state.consciousness - 0.05)
    elif trigger_type == "CURIOSITY_CONFLICT":
        state.curiosity = min(1.0, state.curiosity + 0.15)
        state.consciousness = min(1.0, state.consciousness + 0.1)
        state.boredom = max(0.0, state.boredom - 0.2)
    elif trigger_type == "UNRESOLVED_PATTERN":
        state.unconscious = min(1.0, state.unconscious + 0.1)
    elif trigger_type == "MODEL_DRIFT":
        state.background_self = min(1.0, state.background_self + 0.1)
    
    # 2. 행동 결과에 따른 상태 변화
    if action_result:
        if action_result.get("success"):
            # 성공: 에너지 소모 + 공명 증가
            state.energy = max(0.1, state.energy - 0.05)
            state.resonance = min(1.0, state.resonance + 0.1)
            state.boredom = max(0.0, state.boredom - 0.15)
            state.last_action = action_result.get("action_type", "unknown")
            state.last_action_time = datetime.now(timezone.utc).isoformat()
        else:
            # 실패: 에너지 약간 소모
            state.energy = max(0.1, state.energy - 0.02)
    
    # 3. 자연적 회복/감쇠
    state.energy = min(1.0, state.energy + 0.01)  # 에너지 천천히 회복
    state.boredom = min(1.0, state.boredom + 0.02)  # 지루함 천천히 증가

    # 🌱 4. 자기조절 (Core의 생명 조건)
    # State가 State를 바꾼다 - 외부 입력 없이도 내부가 흐른다
    state.self_regulate()

    # 5. 상태 저장
    save_internal_state(state)
    
    logger.debug(f"State updated: consciousness={state.consciousness:.2f}, "
                 f"boredom={state.boredom:.2f}, energy={state.energy:.2f}")
    
    return state


def run_subconscious_hum() -> None:
    """배경에서 미세하게 상태를 조절 (Subconscious Hum)"""
    with _state_lock:
        state = get_internal_state()
        state.self_regulate()
    
    # 주기적으로 파일에 반영
    save_internal_state(state)


def record_dissonance(error_msg: str, weight: float = 0.1) -> None:
    """
    ⚡ 시스템의 불협화음(Error/Dissonance) 기록
    - 무의식 레벨 증가 (혼란)
    - 에너지 감소 (소모)
    - 회피 욕망 증가
    """
    state = get_internal_state()
    state.unconscious = min(1.0, state.unconscious + weight)
    state.energy = max(0.0, state.energy - (weight * 0.5))
    state.drives['avoid'] = min(1.0, state.drives['avoid'] + (weight * 2.0))
    
    logger.warning(f"⚡ Dissonance Recorded: {error_msg} (Weight: {weight:.2f})")
    save_internal_state(state)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    state = get_internal_state()
    print(f"현재 상태: {state}")
    
    # 업데이트 테스트
    state = update_internal_state(
        action_result={"success": True, "action_type": "test"},
        trigger_type="CURIOSITY_CONFLICT"
    )
    print(f"업데이트 후: {state}")
