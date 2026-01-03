"""
Rhythm-Aware Boundary Manager
Shion의 리듬(확장/수축)에 따라 임계값(Threshold)을 동적으로 조절합니다.
"""
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum
import time

class RhythmMode(Enum):
    CONNECTED = "CONNECTED"           # Conscious + Unconscious (Sleep/Rest/Deep Inquiry)
    ISOLATED_EXECUTION = "ISOLATED"   # Execution Focused (Day/Work/FSD)
    RECONNECT_SEARCH = "RECONNECT"    # Seeking Inspiration (Stagnation Break/Walk)

logger = logging.getLogger("RhythmBoundaries")

class RhythmBoundaryManager:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.thought_stream_path = workspace_root / "outputs" / "thought_stream_latest.json"
        self.rhythm_key_path = workspace_root / "inputs" / "rhythm_key.json"

    def get_rhythm_state(self) -> Dict[str, Any]:
        """최신 리듬 상태를 로드합니다."""
        if not self.thought_stream_path.exists():
            return {"phase": "STABLE", "score": 50, "quantum_flow": "Normal"}

        try:
            # thought_stream_latest.json은 현재 markdown 형식이거나 요약본일 수 있으므로
            # rhythm_health_latest.json을 보조적으로 확인합니다.
            health_path = self.workspace_root / "outputs" / "rhythm_health_latest.json"

            # 기본값 설정
            state = {
                "phase": "STABLE",
                "score": 50,
                "quantum_flow": "Normal"
            }

            if health_path.exists():
                with open(health_path, "r", encoding="utf-8") as f:
                    health = json.load(f)
                    state["score"] = health.get("score", 50)
                    # score에 기반한 위상 결정 (rhythm_think.py 로직 준수)
                    state["phase"] = "EXPANSION" if state["score"] > 60 else "CONTRACTION"

            return state
        except Exception as e:
            logger.error(f"Failed to load rhythm state: {e}")
            return {"phase": "STABLE", "score": 50, "quantum_flow": "Normal"}
        
    def _get_activation_key(self) -> Optional[str]:
        """
        Loads the external activation key.
        Shion (the Architect) can design the lock, but ONLY an exogenous force
        (User/Environment/Rhythm) can provide the Key.
        """
        if not self.rhythm_key_path.exists():
            return None
        try:
            with open(self.rhythm_key_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("key")
        except:
            return None

    def detect_rhythm_mode(self) -> RhythmMode:
        """
        Determines current rhythm mode.
        ISOLATED and RECONNECT_SEARCH now require an external 'Activation Key'.
        """
        # 1. Exogenous Signal Check (Bohm)
        bohm_path = self.workspace_root / "outputs" / "bohm_analysis_latest.json"
        bohm_active = False
        if bohm_path.exists():
            mtime = bohm_path.stat().st_mtime
            if time.time() - mtime < 3600:
                bohm_active = True
        
        # 2. Activation Key Check (The Authority)
        activation_key = self._get_activation_key()
        
        # 3. Decision Logic
        if not activation_key:
            # No Key -> Default to Observation or Connected State if Bohm is active
            return RhythmMode.CONNECTED if bohm_active else RhythmMode.CONNECTED # CONNECTED is the baseline

        # If Key exists, it allows elevated modes
        state = self.get_rhythm_state()
        score = state.get("score", 50)
        
        if activation_key == "RECONNECT_FORCE" or score < 30:
            return RhythmMode.RECONNECT_SEARCH
            
        if activation_key == "EXECUTION_FORCE" or bohm_active:
            # Even with Key, ISOLATED mode prefers Bohm alignment
            return RhythmMode.ISOLATED_EXECUTION
            
        return RhythmMode.CONNECTED

    def adjust_threshold(self, key: str, base_value: float, rhythm_state: Optional[Dict[str, Any]] = None) -> float:
        """
        리듬 상태와 리듬 모드에 따라 임계값을 조절합니다.
        
        ISOLATED_EXECUTION 모드에서는 실행 완결성을 위해 의구심(Doubt) 임계값을 높입니다.
        """
        if rhythm_state is None:
            rhythm_state = self.get_rhythm_state()
            
        mode = self.detect_rhythm_mode()
        phase = rhythm_state.get("phase", "STABLE")
        score = rhythm_state.get("score", 50)
        
        # 기본 배수 설정
        multiplier = 1.0
        
        # 1단계: 위상(Phase)에 따른 기본 조절
        if phase == "EXPANSION":
            expansion_factor = (score - 60) / 40
            multiplier = 0.9 - (expansion_factor * 0.4) 
        elif phase == "CONTRACTION":
            contraction_factor = (60 - score) / 60
            multiplier = 1.1 + (contraction_factor * 0.9)

        # 2단계: 모드(Mode)에 따른 특수 조절
        if mode == RhythmMode.ISOLATED_EXECUTION:
            # 고립 실행 중에는 더 '확신'을 가지고 끝까지 밀어붙여야 함
            if "doubt" in key or "replan" in key or "rethink" in key:
                multiplier *= 2.0  # 의구심 임계값을 2배로 높여 실행 방해 최소화
            elif "completion" in key:
                multiplier *= 0.8  # 완결 조건은 조금 더 수용적으로 (빨리 끝내기)
        elif mode == RhythmMode.RECONNECT_SEARCH:
            if "refresh" in key or "explore" in key:
                multiplier *= 0.5  # 새로운 정보를 더 자주 받아오도록 유도
            
        adjusted_value = base_value * multiplier
        
        if "seconds" in key or "interval" in key:
            return round(adjusted_value)
            
        return round(adjusted_value, 3)

    def get_rhythm_governed_config(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """설정 전체를 리듬과 모드에 맞춰 변환합니다."""
        rhythm_state = self.get_rhythm_state()
        mode = self.detect_rhythm_mode()
        
        adjusted_config = base_config.copy()
        adjusted_config["rhythm_mode"] = mode.value
        
        if "thresholds" in adjusted_config:
            new_thresholds = {}
            for k, v in adjusted_config["thresholds"].items():
                new_thresholds[k] = self.adjust_threshold(k, v, rhythm_state)
            adjusted_config["thresholds"] = new_thresholds
            
        return adjusted_config
