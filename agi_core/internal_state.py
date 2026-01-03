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
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger("InternalState")

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
            elif action_type in ['stabilize', 'rest']:
                self.drives['rest'] = min(1.0, self.drives['rest'] + 0.05)
                self.drives['self_focus'] = min(1.0, self.drives['self_focus'] + 0.03)
        else:
            # 실패는 회피 욕망 증가, 내면화 증가
            self.drives['avoid'] = min(1.0, self.drives['avoid'] + 0.05)
            self.drives['self_focus'] = min(1.0, self.drives['self_focus'] + 0.05)
            self.consciousness = max(0.5, self.consciousness - 0.05)
            self.background_self = min(1.0, self.background_self + 0.05)

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
    
    - 행동 결과에 따라 에너지/공명 조정
    - 시간 경과에 따라 지루함 증가
    - 트리거에 따라 의식/호기심 변화
    """
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
