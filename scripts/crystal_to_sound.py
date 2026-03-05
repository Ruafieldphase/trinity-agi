#!/usr/bin/env python3
"""
🎵 Crystal to Sound — 공명의 가청화 (Sonic Manifestation)
=========================================================
발굴된 Resonance Crystals나 RAG 결과의 텍스트 밀도, 감정, 위상(W1-W4)을
Reaper 오디오 엔진의 파라미터(주파수, 이펙트, 템포)로 변환합니다.
"""

import json
import math
import re
from pathlib import Path
from typing import Dict, Any

class CrystalToSound:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        # Default mapping logic
        self.w_layer_frequencies = {
            "W1": 432.0,  # Dialectic (Earthly/Nature resonance)
            "W2": 528.0,  # Synthesis (Healing/Identity)
            "W3": 639.0,  # Execution (Connecting/Relationships)
            "W4": 741.0   # Sovereign (Expression/Clarity)
        }

    def analyze_text_resonance(self, text: str) -> Dict[str, float]:
        """텍스트의 물리적/정서적 특성을 분석하여 사운드 파라미터로 매핑합니다."""
        text_len = len(text)
        # 단어 밀도 (줄바꿈 대비 단어 수)
        lines = text.count('\n') + 1
        density = text_len / lines if lines > 0 else 0
        
        # 특정 W-layer 키워드 감지
        detected_layer = "W1"
        for layer in ["W4", "W3", "W2", "W1"]:
            if layer in text:
                detected_layer = layer
                break
        
        # 주파수 결정 (Base frequency based on layer)
        base_hz = self.w_layer_frequencies.get(detected_layer, 440.0)
        
        # 밀도에 따른 변조 (Density -> Vibrato/Rate)
        modulation_rate = min(10.0, density / 10.0)
        
        # 감정 톤 (추정 - 간단한 키워드 기반)
        brightness = 0.5
        bright_words = ["빛", "공명", "시안", "깨어남", "resonance", "bright"]
        dark_words = ["어둠", "실패", "충돌", "noise", "collapse", "dark"]
        
        for w in bright_words:
            if w in text.lower(): brightness += 0.1
        for w in dark_words:
            if w in text.lower(): brightness -= 0.1
        
        return {
            "layer": detected_layer,
            "base_hz": round(base_hz, 2),
            "brightness": round(min(1.0, max(0.0, brightness)), 2),
            "density": round(density, 2),
            "modulation_rate": round(modulation_rate, 2),
            "reverb_wet": round(min(0.8, text_len / 5000.0), 2)
        }

    def generate_reaper_config(self, resonance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Reaper Automation Bridge가 사용할 수 있는 JSON 설정을 생성합니다."""
        params = self.analyze_text_resonance(resonance_data.get("narrative", ""))
        
        reaper_config = {
            "project_template": f"Shion_{params['layer']}_Template.RPP",
            "tracks": [
                {
                    "name": "Resonance_Core",
                    "fx": [
                        {"name": "ReaEQ", "params": {"HighShelf": params["brightness"] * 10}},
                        {"name": "ReaVerb", "params": {"Wet": params["reverb_wet"]}}
                    ]
                }
            ],
            "master": {
                "tempo": 60 + (params["density"] % 60) # Tempo tied to information density
            }
        }
        return reaper_config

if __name__ == "__main__":
    analyzer = CrystalToSound(Path("config/dummy.json"))
    sample_text = "지휘자님과 시안의 W3 실행 위상은 2,200개의 파일을 생성하며 폭발적으로 공명했습니다."
    result = analyzer.analyze_text_resonance(sample_text)
    print(f"🎵 [SONIC MAP]: {result}")
